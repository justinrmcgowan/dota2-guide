#!/usr/bin/env python3
"""Offline training pipeline for the ML win predictor.

Downloads 200k+ recent matches from OpenDota SQL Explorer, constructs
252-dim one-hot feature vectors, trains one XGBoost model per MMR bracket,
computes synergy/counter matrices, and commits all artifacts to disk.

Usage (from prismlab/backend/):
    python scripts/train_win_predictor.py

Output:
    models/win_predictor_bracket_{1..4}.ubj  -- XGBoost model per bracket
    models/matrices.json                     -- synergy + counter matrices per bracket

Notes:
    - Rate limit: 60 req/min free tier. If 429 errors appear, wait 60s and re-run.
    - Patch filtering: start_time >= PATCH_741_START (2026-03-24).
    - Early in the patch cycle there may be <200k matches — a WARNING is logged
      but training proceeds with available data.
    - Running from prismlab/backend/ is required so relative imports resolve.
"""

import asyncio
import json
import logging
import os
import sys
import time
from collections import defaultdict

import numpy as np
import xgboost as xgb
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Project imports — run from prismlab/backend/ as cwd
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.opendota_client import OpenDotaClient
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PATCH_741_START = 1742774400  # Unix epoch for 2026-03-24 (patch 7.41 release)

BRACKET_FILTERS: dict[int, str] = {
    1: "avg_rank_tier BETWEEN 10 AND 39",   # Herald-Crusader
    2: "avg_rank_tier BETWEEN 40 AND 59",   # Archon-Legend
    3: "avg_rank_tier BETWEEN 60 AND 79",   # Ancient-Divine
    4: "avg_rank_tier >= 80",               # Immortal
}

BRACKET_NAMES: dict[int, str] = {
    1: "Herald-Crusader",
    2: "Archon-Legend",
    3: "Ancient-Divine",
    4: "Immortal",
}

PAGE_SIZE: int = 40000
TARGET_ROWS_PER_BRACKET: int = 200000
MIN_PAIR_MATCHES: int = 50   # minimum matches for synergy/counter inclusion
MODELS_DIR: str = "models"


# ---------------------------------------------------------------------------
# Step 1 — fetch_bracket_matches
# ---------------------------------------------------------------------------
async def fetch_bracket_matches(
    bracket: int,
    client: OpenDotaClient,
) -> list[dict]:
    """Download up to TARGET_ROWS_PER_BRACKET matches for one MMR bracket.

    Paginates OpenDota SQL Explorer via LIMIT/OFFSET until fewer than PAGE_SIZE
    rows are returned or TARGET_ROWS_PER_BRACKET is reached.

    Args:
        bracket: Integer key 1-4 corresponding to BRACKET_FILTERS / BRACKET_NAMES.
        client: Initialized OpenDotaClient instance.

    Returns:
        List of row dicts with keys: match_id, radiant_win, radiant_team, dire_team.
    """
    bracket_filter = BRACKET_FILTERS[bracket]
    all_rows: list[dict] = []
    page = 0

    while len(all_rows) < TARGET_ROWS_PER_BRACKET:
        offset = page * PAGE_SIZE
        sql = (
            f"SELECT match_id, radiant_win, radiant_team, dire_team, avg_rank_tier "
            f"FROM public_matches "
            f"WHERE start_time >= {PATCH_741_START} "
            f"  AND {bracket_filter} "
            f"  AND game_mode = 22 "
            f"  AND lobby_type = 7 "
            f"  AND array_length(radiant_team, 1) = 5 "
            f"  AND array_length(dire_team, 1) = 5 "
            f"ORDER BY match_id DESC "
            f"LIMIT {PAGE_SIZE} OFFSET {offset}"
        )

        try:
            rows = await client.fetch_explorer_sql(sql)
        except Exception as exc:
            logger.error(
                "Bracket %d page %d fetch failed: %s — retrying after 65s",
                bracket, page, exc,
            )
            await asyncio.sleep(65)
            rows = await client.fetch_explorer_sql(sql)

        # Filter out malformed rows
        valid_rows = []
        for row in rows:
            radiant = row.get("radiant_team")
            dire = row.get("dire_team")
            if (
                radiant is None
                or dire is None
                or not isinstance(radiant, list)
                or not isinstance(dire, list)
                or len(radiant) != 5
                or len(dire) != 5
            ):
                continue
            valid_rows.append(row)

        all_rows.extend(valid_rows)
        logger.info(
            "Bracket %d (%s): page %d, %d valid rows this page, %d total so far",
            bracket, BRACKET_NAMES[bracket], page, len(valid_rows), len(all_rows),
        )

        if len(rows) < PAGE_SIZE:
            # No more pages
            break

        page += 1
        # Respect rate limit — 60 req/min free tier
        await asyncio.sleep(1.1)

    if len(all_rows) < 50000:
        logger.warning(
            "Bracket %d (%s): only %d rows collected — patch 7.41 may be too new. "
            "Training will continue but model accuracy may be lower.",
            bracket, BRACKET_NAMES[bracket], len(all_rows),
        )

    return all_rows[: TARGET_ROWS_PER_BRACKET]


# ---------------------------------------------------------------------------
# Step 2 — build_hero_id_to_index
# ---------------------------------------------------------------------------
def build_hero_id_to_index(
    all_bracket_matches: dict[int, list[dict]],
) -> tuple[dict[int, int], int]:
    """Build a stable hero_id -> 0-based index mapping from all brackets' matches.

    Collecting all hero IDs across all brackets and sorting them guarantees that
    the mapping is consistent between training and inference (Plan 02 loads
    matrices.json which embeds this mapping).

    Args:
        all_bracket_matches: Dict mapping bracket number to list of match rows.

    Returns:
        Tuple of (hero_id_to_index dict, n_heroes int).
    """
    hero_ids: set[int] = set()
    for matches in all_bracket_matches.values():
        for row in matches:
            for hid in row.get("radiant_team", []):
                hero_ids.add(int(hid))
            for hid in row.get("dire_team", []):
                hero_ids.add(int(hid))

    sorted_ids = sorted(hero_ids)
    hero_id_to_index = {hid: idx for idx, hid in enumerate(sorted_ids)}
    n_heroes = len(hero_id_to_index)
    logger.info("Hero universe: %d distinct heroes across all brackets", n_heroes)
    return hero_id_to_index, n_heroes


# ---------------------------------------------------------------------------
# Step 3 — build_feature_vector
# ---------------------------------------------------------------------------
def build_feature_vector(
    radiant_ids: list[int],
    dire_ids: list[int],
    hero_id_to_index: dict[int, int],
    n_heroes: int,
) -> np.ndarray:
    """Construct a 252-dim (n_heroes*2) one-hot feature vector for one match.

    First n_heroes positions represent Radiant hero presence.
    Next n_heroes positions represent Dire hero presence.

    Args:
        radiant_ids: List of 5 Radiant hero IDs.
        dire_ids: List of 5 Dire hero IDs.
        hero_id_to_index: Mapping from hero ID to 0-based index.
        n_heroes: Total number of heroes in the universe.

    Returns:
        Float32 numpy array of shape (n_heroes * 2,).
    """
    vec = np.zeros(n_heroes * 2, dtype=np.float32)
    for hid in radiant_ids:
        idx = hero_id_to_index.get(int(hid))
        if idx is not None:
            vec[idx] = 1.0
    for hid in dire_ids:
        idx = hero_id_to_index.get(int(hid))
        if idx is not None:
            vec[n_heroes + idx] = 1.0
    return vec


# ---------------------------------------------------------------------------
# Step 4 — train_bracket_model
# ---------------------------------------------------------------------------
def train_bracket_model(
    bracket: int,
    matches: list[dict],
    hero_id_to_index: dict[int, int],
    n_heroes: int,
) -> xgb.XGBClassifier:
    """Build features, train XGBoost, log metrics, save model artifact.

    Args:
        bracket: Integer bracket number 1-4 (used in output filename).
        matches: List of match row dicts.
        hero_id_to_index: Stable hero ID -> index mapping.
        n_heroes: Total heroes in the universe.

    Returns:
        Fitted XGBClassifier instance.
    """
    logger.info(
        "Bracket %d (%s): building feature matrix for %d matches…",
        bracket, BRACKET_NAMES[bracket], len(matches),
    )

    X_rows = []
    y_labels = []

    for row in matches:
        radiant = row.get("radiant_team", [])
        dire = row.get("dire_team", [])
        radiant_win = row.get("radiant_win")

        if radiant_win is None:
            continue

        vec = build_feature_vector(radiant, dire, hero_id_to_index, n_heroes)
        X_rows.append(vec)
        y_labels.append(1 if radiant_win else 0)

    if len(X_rows) < 100:
        logger.warning(
            "Bracket %d: only %d valid matches — skipping model training",
            bracket, len(X_rows),
        )
        return None

    X = np.array(X_rows, dtype=np.float32)
    y = np.array(y_labels, dtype=np.int32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info(
        "Bracket %d: training on %d examples, testing on %d…",
        bracket, len(X_train), len(X_test),
    )

    classifier = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )

    classifier.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = classifier.predict(X_test)
    y_proba = classifier.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    logger.info(
        "Bracket %d (%s): accuracy=%.4f, AUC=%.4f",
        bracket, BRACKET_NAMES[bracket], acc, auc,
    )

    # Use get_booster().save_model() to write the native .ubj format.
    # Do NOT use joblib.dump or XGBClassifier.save_model() — those embed sklearn
    # wrapper metadata that breaks across XGBoost version upgrades (Pitfall 4).
    model_path = os.path.join(MODELS_DIR, f"win_predictor_bracket_{bracket}.ubj")
    classifier.get_booster().save_model(model_path)
    logger.info("Bracket %d model saved to %s", bracket, model_path)

    return classifier


# ---------------------------------------------------------------------------
# Step 5 — compute_individual_winrates
# ---------------------------------------------------------------------------
def compute_individual_winrates(
    matches: list[dict],
    hero_id_to_index: dict[int, int],
    n_heroes: int,
) -> list[float]:
    """Compute per-hero win rate across all matches in which that hero appears.

    Used as the baseline for synergy delta computation.

    Args:
        matches: List of match row dicts.
        hero_id_to_index: Stable hero ID -> index mapping.
        n_heroes: Total heroes in the universe.

    Returns:
        List of floats indexed by hero index. 0.5 if hero never appears.
    """
    wins = [0] * n_heroes
    games = [0] * n_heroes

    for row in matches:
        radiant = row.get("radiant_team", [])
        dire = row.get("dire_team", [])
        radiant_win = row.get("radiant_win", False)

        for hid in radiant:
            idx = hero_id_to_index.get(int(hid))
            if idx is not None:
                games[idx] += 1
                if radiant_win:
                    wins[idx] += 1

        for hid in dire:
            idx = hero_id_to_index.get(int(hid))
            if idx is not None:
                games[idx] += 1
                if not radiant_win:
                    wins[idx] += 1

    individual_wr = []
    for i in range(n_heroes):
        individual_wr.append(wins[i] / games[i] if games[i] > 0 else 0.5)

    return individual_wr


# ---------------------------------------------------------------------------
# Step 6 — compute_synergy_matrix
# ---------------------------------------------------------------------------
def compute_synergy_matrix(
    matches: list[dict],
    hero_id_to_index: dict[int, int],
    n_heroes: int,
) -> list[list[float | None]]:
    """Compute an n_heroes x n_heroes synergy matrix.

    synergy[a][b] = win_rate(a+b on same team) - (wr[a] + wr[b]) / 2

    Positive values indicate the pair wins more than expected from individual rates.
    Cells with fewer than MIN_PAIR_MATCHES matches are set to None (sparse).
    The matrix is symmetric (synergy[a][b] == synergy[b][a]).

    Args:
        matches: Match rows for one bracket.
        hero_id_to_index: Stable hero ID -> index mapping.
        n_heroes: Total heroes in the universe.

    Returns:
        n_heroes x n_heroes list-of-lists with float or None entries.
    """
    individual_wr = compute_individual_winrates(matches, hero_id_to_index, n_heroes)

    pair_wins: dict[tuple[int, int], int] = defaultdict(int)
    pair_games: dict[tuple[int, int], int] = defaultdict(int)

    for row in matches:
        radiant = row.get("radiant_team", [])
        dire = row.get("dire_team", [])
        radiant_win = row.get("radiant_win", False)

        for team, team_won in [(radiant, radiant_win), (dire, not radiant_win)]:
            ids = [hero_id_to_index.get(int(hid)) for hid in team]
            ids = [i for i in ids if i is not None]

            for a_idx in range(len(ids)):
                for b_idx in range(a_idx + 1, len(ids)):
                    a, b = ids[a_idx], ids[b_idx]
                    key = (min(a, b), max(a, b))
                    pair_games[key] += 1
                    if team_won:
                        pair_wins[key] += 1

    # Build symmetric matrix
    matrix: list[list[float | None]] = [[None] * n_heroes for _ in range(n_heroes)]

    for (a, b), games in pair_games.items():
        if games < MIN_PAIR_MATCHES:
            continue
        pair_wr = pair_wins[(a, b)] / games
        baseline = (individual_wr[a] + individual_wr[b]) / 2.0
        delta = round(pair_wr - baseline, 6)
        matrix[a][b] = delta
        matrix[b][a] = delta  # symmetric

    return matrix


# ---------------------------------------------------------------------------
# Step 7 — compute_counter_matrix
# ---------------------------------------------------------------------------
def compute_counter_matrix(
    matches: list[dict],
    hero_id_to_index: dict[int, int],
    n_heroes: int,
) -> list[list[float | None]]:
    """Compute an n_heroes x n_heroes counter matrix.

    counter[a][b] = win rate of hero a when facing hero b on the opposing team.

    Asymmetric: counter[a][b] + counter[b][a] ≈ 1.0 but not exactly due to
    multi-hero matches where both heroes may appear at different times.
    Cells with fewer than MIN_PAIR_MATCHES encounters are set to None.

    Args:
        matches: Match rows for one bracket.
        hero_id_to_index: Stable hero ID -> index mapping.
        n_heroes: Total heroes in the universe.

    Returns:
        n_heroes x n_heroes list-of-lists with float or None entries.
    """
    cross_wins: dict[tuple[int, int], int] = defaultdict(int)
    cross_games: dict[tuple[int, int], int] = defaultdict(int)

    for row in matches:
        radiant = row.get("radiant_team", [])
        dire = row.get("dire_team", [])
        radiant_win = row.get("radiant_win", False)

        radiant_indices = [hero_id_to_index.get(int(hid)) for hid in radiant]
        dire_indices = [hero_id_to_index.get(int(hid)) for hid in dire]
        radiant_indices = [i for i in radiant_indices if i is not None]
        dire_indices = [i for i in dire_indices if i is not None]

        for a in radiant_indices:
            for b in dire_indices:
                # a (radiant) vs b (dire)
                cross_games[(a, b)] += 1
                if radiant_win:
                    cross_wins[(a, b)] += 1

                # b (dire) vs a (radiant)
                cross_games[(b, a)] += 1
                if not radiant_win:
                    cross_wins[(b, a)] += 1

    matrix: list[list[float | None]] = [[None] * n_heroes for _ in range(n_heroes)]

    for (a, b), games in cross_games.items():
        if games < MIN_PAIR_MATCHES:
            continue
        matrix[a][b] = round(cross_wins[(a, b)] / games, 6)

    return matrix


# ---------------------------------------------------------------------------
# Step 8 — main
# ---------------------------------------------------------------------------
async def main() -> None:
    """End-to-end training pipeline: download → featurize → train → matrices → save."""
    t_start = time.monotonic()

    api_key = os.getenv("OPENDOTA_API_KEY")
    client = OpenDotaClient(api_key=api_key)

    if api_key:
        logger.info("Using OpenDota API key (higher rate limits)")
    else:
        logger.info("No OPENDOTA_API_KEY set — using free tier (60 req/min)")

    os.makedirs(MODELS_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Download match data for all 4 brackets
    # ------------------------------------------------------------------
    all_bracket_matches: dict[int, list[dict]] = {}
    for bracket in range(1, 5):
        logger.info(
            "=== Fetching bracket %d (%s) ===",
            bracket, BRACKET_NAMES[bracket],
        )
        rows = await fetch_bracket_matches(bracket, client)
        all_bracket_matches[bracket] = rows
        logger.info(
            "Bracket %d: %d matches collected", bracket, len(rows)
        )

    # ------------------------------------------------------------------
    # Build stable hero_id_to_index from ALL brackets combined
    # (ensures consistent indexing between training and inference)
    # ------------------------------------------------------------------
    hero_id_to_index, n_heroes = build_hero_id_to_index(all_bracket_matches)

    # ------------------------------------------------------------------
    # Per-bracket: train model + compute matrices
    # ------------------------------------------------------------------
    matrices: dict[int, dict] = {}

    for bracket in range(1, 5):
        matches = all_bracket_matches[bracket]
        bracket_name = BRACKET_NAMES[bracket]

        logger.info("=== Training bracket %d (%s) ===", bracket, bracket_name)

        if len(matches) == 0:
            logger.warning(
                "Bracket %d: no matches — skipping training and matrix computation",
                bracket,
            )
            matrices[bracket] = {
                "synergy": [],
                "counter": [],
                "hero_id_to_index": {str(k): v for k, v in hero_id_to_index.items()},
                "n_heroes": n_heroes,
            }
            continue

        train_bracket_model(bracket, matches, hero_id_to_index, n_heroes)

        logger.info(
            "Bracket %d: computing synergy matrix (%d matches)…",
            bracket, len(matches),
        )
        synergy = compute_synergy_matrix(matches, hero_id_to_index, n_heroes)

        logger.info(
            "Bracket %d: computing counter matrix (%d matches)…",
            bracket, len(matches),
        )
        counter = compute_counter_matrix(matches, hero_id_to_index, n_heroes)

        matrices[bracket] = {
            "synergy": synergy,
            "counter": counter,
            "hero_id_to_index": {str(k): v for k, v in hero_id_to_index.items()},
            "n_heroes": n_heroes,
        }

    # ------------------------------------------------------------------
    # Write matrices.json
    # ------------------------------------------------------------------
    result = {f"bracket_{b}": matrices[b] for b in range(1, 5)}
    matrices_path = os.path.join(MODELS_DIR, "matrices.json")
    with open(matrices_path, "w") as f:
        json.dump(result, f)

    logger.info("matrices.json written to %s", matrices_path)

    elapsed = time.monotonic() - t_start
    logger.info(
        "Training complete. Models and matrices saved to %s/ (elapsed: %.1f min)",
        MODELS_DIR, elapsed / 60,
    )


if __name__ == "__main__":
    asyncio.run(main())
