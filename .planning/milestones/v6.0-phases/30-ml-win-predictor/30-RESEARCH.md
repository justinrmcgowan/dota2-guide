# Phase 30: ML Win Predictor - Research

**Researched:** 2026-03-29
**Domain:** XGBoost win prediction, OpenDota SQL Explorer, synergy/counter matrices, model serving in FastAPI/Docker
**Confidence:** HIGH (stack) / MEDIUM (OpenDota schema details, patch filtering) / HIGH (integration patterns)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- OpenDota SQL Explorer for bulk match data (free, up to 200k rows per query, SQL-level patch/rank filtering)
- Current patch only (7.41) — most accurate for current meta
- 4 MMR brackets: Herald-Crusader, Archon-Legend, Ancient-Divine, Immortal
- Manual retraining script — run when new patch drops, not scheduled
- XGBoost classifier — standard for Dota prediction, handles non-linear hero interactions
- One-hot hero encoding — binary 252-dim vector (126 per team), simple and proven
- Hero-only features — no role encoding, positions implicit in draft context
- One model per MMR bracket (4 total)
- 50-match minimum per hero pair to include in synergy/counter matrices
- Pool across brackets when a pairing has insufficient data in a specific bracket
- 4 brackets for synergy/counter matrices matching the model brackets
- Win probability percentage displayed inside existing WinConditionBadge — e.g. "Teamfight 54%"
- Opacity-based confidence encoding (100/75/50) matching WinConditionBadge pattern
- Appears alongside Claude's qualitative win condition so users see both statistical and reasoning signals

### Claude's Discretion
- XGBoost hyperparameters and training pipeline details
- SQL query structure for OpenDota Explorer
- Synergy/counter matrix storage format (JSON, SQLite, pickle)
- API endpoint design for serving predictions
- How to handle partial drafts (<10 heroes) — could show partial prediction or wait for complete draft

### Deferred Ideas (OUT OF SCOPE)
- Real-time draft tracking during captain's mode (v7.0+)
- Hero embeddings / hero2vec for richer feature engineering (future iteration)
- Role-aware model (carry Lina vs support Lina) — data fragmentation concern
- Confidence text labels ("Low confidence") — opacity pattern is sufficient
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRED-01 | Given a full 10-hero draft, the system predicts win probability as a percentage for the allied team | XGBoost classifier on 252-dim one-hot vector; served at /api/recommend as post-LLM enrichment |
| PRED-02 | Win predictions are trained on 200k+ recent matches from OpenDota bulk data, filtered to current patch | public_matches table via SQL Explorer; patch filtered by start_time >= Unix epoch of 7.41 release |
| PRED-03 | Precomputed synergy matrix scores hero pairs by observed win rate delta vs independent pick rates, segmented by MMR bracket | Pairwise WR delta computation from the same match dataset; stored as JSON in DataCache |
| PRED-04 | Precomputed counter matrix scores hero matchups by observed win rate when opposing, segmented by MMR bracket | Cross-team hero pair win rate from radiant_team / dire_team arrays; same storage pattern as PRED-03 |
| PRED-05 | Win probability displays alongside Claude's qualitative win condition assessment | win_probability field added to RecommendResponse; WinConditionBadge.tsx updated to display "Teamfight 54%" |
</phase_requirements>

---

## Summary

Phase 30 adds a statistical win probability layer on top of the existing qualitative WinConditionBadge. The end-to-end pipeline has two parts that are architecturally distinct: (1) an offline training script that downloads match data, trains XGBoost models, computes matrices, and writes artifacts to disk; (2) runtime integration that loads those artifacts at startup and enriches the /api/recommend response with a prediction.

The XGBoost approach is industry-standard for Dota draft prediction, with accuracy ceilings around 59-65% on hero-only features — inherently limited because the game outcome is strongly influenced by player execution, not just draft. This ceiling should be communicated in the UI; a 54% prediction should feel like a useful signal, not a definitive forecast. The andreiapostoae/dota2-predictor project (the most cited reference implementation) used logistic regression and achieved ~65% ROC AUC with synergy+counter features — XGBoost with the same features typically performs at least as well.

**Primary recommendation:** Use XGBoost 3.2.0 with its native `.ubj` save format (not joblib/pickle) for model persistence; load all 4 bracket models + 4 bracket matrices into DataCache at startup as frozen objects; serve predictions synchronously in the recommend endpoint with a try/except fallback to `None` (no probability shown) if the model isn't loaded.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| xgboost | 3.2.0 | XGBoost classifier training and inference | Industry standard for tabular prediction; Python 3.12/3.14 compatible; supports `.ubj` native format |
| scikit-learn | 1.8.0 | Train/test split, accuracy metrics, preprocessing utilities | Pairs naturally with XGBoost; provides `cross_val_score`, `accuracy_score`, `roc_auc_score` |
| numpy | 2.4.4 | Feature vector construction, matrix math | Required by both xgboost and scikit-learn |
| pandas | 3.0.1 | CSV ingestion and DataFrame manipulation for training data | Optional but useful for data exploration; can skip in pure-numpy pipeline |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| joblib | 1.5.3 | Parallel processing during matrix computation | Use `joblib.Parallel` to parallelize per-hero matrix row computation; do NOT use `joblib.dump` for model persistence |
| httpx | 0.28.1 (already in project) | HTTP calls to OpenDota SQL Explorer API | Already in `opendota_client.py`; extend with `fetch_explorer_sql()` method |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| XGBoost native `.ubj` format | `joblib.dump` / pickle | Joblib/pickle are version-unstable across XGBoost upgrades; native format is the XGBoost team's recommended approach |
| `pandas` for training CSV | Pure `numpy` from JSON | pandas makes exploratory work easier; for production training script, either works |
| 4 separate model files | Single multi-output model | Separate files are simpler to load/swap per bracket; multi-output adds complexity with no practical benefit |

**Installation (backend):**
```bash
pip install "xgboost==3.2.0" "scikit-learn==1.8.0" "numpy==2.4.4"
```

Add to `prismlab/backend/requirements.txt`.

**Version verification (confirmed 2026-03-29):**
- xgboost: 3.2.0 (latest stable as of 2026-03-29)
- scikit-learn: 1.8.0 (latest stable)
- numpy: 2.4.4 (latest stable)
- Python 3.12 in Dockerfile: confirmed compatible — XGBoost 3.x requires Python >= 3.10

---

## Architecture Patterns

### Recommended Project Structure
```
prismlab/backend/
├── engine/
│   ├── win_predictor.py          # WinPredictor class: load models, run inference
│   └── win_condition.py          # existing — unchanged
├── data/
│   ├── cache.py                  # extend with _win_models and _matrices fields
│   └── opendota_client.py        # extend with fetch_explorer_sql() method
├── scripts/
│   ├── train_win_predictor.py    # offline: download data, train, save models + matrices
│   └── generate_training_data.py # existing — unchanged
└── models/                       # new directory: model artifacts committed to repo
    ├── win_predictor_bracket_1.ubj   # Herald-Crusader model
    ├── win_predictor_bracket_2.ubj   # Archon-Legend model
    ├── win_predictor_bracket_3.ubj   # Ancient-Divine model
    ├── win_predictor_bracket_4.ubj   # Immortal model
    └── matrices.json                 # synergy + counter matrices for all 4 brackets
```

The `models/` directory should be committed to the git repo so the Docker container has artifacts at startup without a training step. Training is an offline developer workflow — run once per patch on developer machine, commit artifacts.

### Pattern 1: OpenDota SQL Explorer Data Download

**What:** HTTP GET to `https://api.opendota.com/api/explorer?sql=<encoded_sql>` returns JSON `{"rows": [...], "rowCount": N}`.

**Key schema facts (confirmed from odota/core source):**
- `public_matches` columns: `match_id`, `match_seq_num`, `radiant_win` (boolean), `start_time` (Unix epoch bigint), `duration`, `lobby_type`, `game_mode`, `avg_rank_tier` (float), `num_rank_tier`, `cluster`, `radiant_team` (integer[]), `dire_team` (integer[])`
- `radiant_team` and `dire_team` are PostgreSQL integer arrays — OpenDota Explorer returns them as arrays of hero IDs (e.g. `[1, 5, 11, 35, 126]`)
- **No `patch` column on `public_matches`** — filter by `start_time` instead. Patch 7.41 released 2026-03-24 (Unix epoch ~1742774400). Use `start_time >= 1742774400` for 7.41+ matches.
- `avg_rank_tier` uses the 2-digit encoding scheme: tens digit = tier (1=Herald, 2=Guardian, 3=Crusader, 4=Archon, 5=Legend, 6=Ancient, 7=Divine, 8=Immortal), ones digit = star (1-5). E.g. 45 = Archon[5], 80 = Immortal.

**Bracket filter ranges for avg_rank_tier:**
```
Herald-Crusader:  avg_rank_tier BETWEEN 10 AND 39
Archon-Legend:    avg_rank_tier BETWEEN 40 AND 59
Ancient-Divine:   avg_rank_tier BETWEEN 60 AND 79
Immortal:         avg_rank_tier >= 80
```

**Rate limits:** 60 requests/minute, 50,000 calls/month (free tier). The training script makes ~4-8 paginated requests (one set per bracket), well within limits.

**Pagination strategy:** SQL Explorer times out at 30 seconds. Use `LIMIT 40000 OFFSET N` to page through results. With 200k rows target, ~5 pages per bracket.

**Example SQL (Archon-Legend bracket, current patch):**
```sql
SELECT match_id, radiant_win, radiant_team, dire_team, avg_rank_tier
FROM public_matches
WHERE start_time >= 1742774400
  AND avg_rank_tier BETWEEN 40 AND 59
  AND game_mode = 22
  AND array_length(radiant_team, 1) = 5
  AND array_length(dire_team, 1) = 5
ORDER BY match_id DESC
LIMIT 40000
OFFSET 0
```

`game_mode = 22` is All Pick (ranked). `array_length = 5` guards against partial/corrupted draft rows.

**Example Python (extending opendota_client.py):**
```python
# Source: OpenDota API docs + confirmed schema from odota/core SQL
async def fetch_explorer_sql(self, sql: str) -> list[dict]:
    """Run an arbitrary SQL query against OpenDota's Explorer endpoint.

    Returns list of row dicts. Caller handles pagination via LIMIT/OFFSET in sql.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.BASE_URL.rstrip('/api')}/api/explorer",
            params={**self.params, "sql": sql},
            timeout=60.0,  # Explorer can be slow for large result sets
        )
        response.raise_for_status()
        data = response.json()
        return data.get("rows", [])
```

### Pattern 2: Feature Vector Construction

**What:** One-hot encoding of hero picks into a 252-dim binary vector.

**Key details:**
- OpenDota hero IDs range from 1 to ~140 in active use, but the maximum hero ID is ~146 with gaps. Use the hero count from DataCache for the vector dimension — current count is 126 active heroes (DataCache is source of truth).
- **Vector layout:** First 126 positions = radiant team (1 if hero present), next 126 positions = dire team. Total = 252 dims.
- Input to predict: always from the allied team's perspective. If user is Radiant, allies go in positions 0-125, opponents in 126-251. If user is Dire, flip.

```python
# Source: established Dota2 ML convention (andreiapostoae/dota2-predictor pattern)
import numpy as np

def build_feature_vector(
    radiant_hero_ids: list[int],
    dire_hero_ids: list[int],
    hero_id_to_index: dict[int, int],  # hero_id -> 0-based index (from DataCache)
    n_heroes: int = 126,
) -> np.ndarray:
    vec = np.zeros(n_heroes * 2, dtype=np.float32)
    for hid in radiant_hero_ids:
        idx = hero_id_to_index.get(hid)
        if idx is not None:
            vec[idx] = 1.0
    for hid in dire_hero_ids:
        idx = hero_id_to_index.get(hid)
        if idx is not None:
            vec[n_heroes + idx] = 1.0
    return vec
```

**Training dataset shape:** Each row = 1 match. Shape = (N_matches, 252). Target = `radiant_win` (bool → int 0/1).

### Pattern 3: Synergy and Counter Matrix Computation

**What:** Pairwise statistics for hero combinations.

**Synergy matrix** (shape: N_heroes × N_heroes, symmetric):
- `synergy[i][j]` = win rate of matches where heroes i AND j are on the same team, MINUS the average individual win rate of each hero. Higher = better synergy.
- Range: typically -0.10 to +0.10 (ten percentage points around the mean).

**Counter matrix** (shape: N_heroes × N_heroes, asymmetric):
- `counter[i][j]` = win rate of hero i when hero j is on the opposing team.
- `counter[i][j] > 0.5` means hero i tends to win vs hero j.

**Minimum threshold:** Only record a value when `match_count >= 50` for the pair. Below threshold, use `None` or `0.5` (neutral signal).

```python
# Source: andreiapostoae/dota2-predictor conceptual approach, adapted
from collections import defaultdict

def compute_synergy_matrix(matches: list[dict], hero_id_to_idx: dict, n_heroes: int):
    """matches: list of {"radiant_team": [...], "dire_team": [...], "radiant_win": bool}"""
    wins = defaultdict(int)
    games = defaultdict(int)

    for m in matches:
        radiant_win = m["radiant_win"]
        for team, won in [(m["radiant_team"], radiant_win), (m["dire_team"], not radiant_win)]:
            heroes = [hero_id_to_idx[h] for h in team if h in hero_id_to_idx]
            for i in range(len(heroes)):
                for j in range(i + 1, len(heroes)):
                    a, b = min(heroes[i], heroes[j]), max(heroes[i], heroes[j])
                    games[(a, b)] += 1
                    if won:
                        wins[(a, b)] += 1

    matrix = [[None] * n_heroes for _ in range(n_heroes)]
    hero_wr = compute_individual_winrates(matches, hero_id_to_idx, n_heroes)

    for (a, b), count in games.items():
        if count >= 50:
            pair_wr = wins[(a, b)] / count
            # Synergy = pair win rate minus average of individual win rates
            delta = pair_wr - (hero_wr[a] + hero_wr[b]) / 2
            matrix[a][b] = delta
            matrix[b][a] = delta  # symmetric

    return matrix
```

**Storage format:** JSON file with structure:
```json
{
  "bracket_1": {
    "synergy": [[float_or_null, ...], ...],
    "counter": [[float_or_null, ...], ...],
    "hero_id_to_index": {"1": 0, "2": 1, ...}
  },
  "bracket_2": { ... },
  "bracket_3": { ... },
  "bracket_4": { ... }
}
```

Size estimate: 4 brackets × 2 matrices × 126² values × 4 bytes ≈ ~500KB. Trivial for DataCache.

### Pattern 4: XGBoost Training

**What:** Standard XGBoost binary classification with scikit-learn API wrapper.

```python
# Source: XGBoost official docs + Dota prediction literature
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

def train_bracket_model(X: np.ndarray, y: np.ndarray) -> xgb.XGBClassifier:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"Accuracy: {acc:.3f}  AUC: {auc:.3f}")

    return model

# Save using XGBoost native format (NOT joblib)
model.save_model("models/win_predictor_bracket_2.ubj")

# Load at runtime
model = xgb.XGBClassifier()
model.load_model("models/win_predictor_bracket_2.ubj")
```

**Expected accuracy:** 58-65% accuracy on held-out test set. ROC AUC 0.63-0.68. This is the known ceiling for hero-only draft features in Dota 2 (confirmed across multiple academic papers and community projects). Do not expect higher — game outcome is heavily influenced by player skill and execution.

### Pattern 5: DataCache Extension

**What:** Add win models and matrices to the existing DataCache singleton.

```python
# In data/cache.py — extend DataCache.__init__ and load()
import xgboost as xgb
import json

class DataCache:
    def __init__(self) -> None:
        # ... existing fields ...
        self._win_models: dict[int, xgb.XGBClassifier] = {}   # bracket_num -> model
        self._matrices: dict[int, dict] = {}                   # bracket_num -> {synergy, counter, hero_id_to_index}
        self._win_predictor_ready: bool = False

    def load_win_predictor(self, models_dir: str = "models") -> None:
        """Load XGBoost models and matrices from disk. Called once at startup."""
        import os
        bracket_map = {1: "bracket_1", 2: "bracket_2", 3: "bracket_3", 4: "bracket_4"}
        new_models = {}
        for num, name in bracket_map.items():
            path = os.path.join(models_dir, f"win_predictor_{name}.ubj")
            if os.path.exists(path):
                m = xgb.XGBClassifier()
                m.load_model(path)
                new_models[num] = m

        matrices_path = os.path.join(models_dir, "matrices.json")
        new_matrices = {}
        if os.path.exists(matrices_path):
            with open(matrices_path) as f:
                raw = json.load(f)
            for num, name in bracket_map.items():
                if name in raw:
                    new_matrices[num] = raw[name]

        self._win_models = new_models
        self._matrices = new_matrices
        self._win_predictor_ready = len(new_models) > 0
        logger.info("WinPredictor loaded: %d bracket models", len(new_models))
```

### Pattern 6: RecommendResponse Integration

**What:** Add `win_probability` field to schemas and compute it as post-LLM enrichment.

```python
# In engine/schemas.py — extend RecommendResponse
class RecommendResponse(BaseModel):
    # ... existing fields ...
    win_probability: float | None = None  # 0.0-1.0, None if model not ready or <10 heroes

# In engine/win_predictor.py — new module
class WinPredictor:
    def predict(
        self,
        allied_hero_ids: list[int],
        enemy_hero_ids: list[int],
        is_radiant: bool,
        bracket: int,
        cache: DataCache,
    ) -> float | None:
        """Returns win probability (0.0-1.0) for the allied team, or None."""
        if not cache._win_predictor_ready:
            return None
        if len(allied_hero_ids) + len(enemy_hero_ids) < 10:
            return None  # Require full draft per PRED-01
        model = cache._win_models.get(bracket)
        if model is None:
            return None
        radiant = allied_hero_ids if is_radiant else enemy_hero_ids
        dire = enemy_hero_ids if is_radiant else allied_hero_ids
        # hero_id_to_index from matrices metadata
        hero_id_to_index = cache._matrices.get(bracket, {}).get("hero_id_to_index", {})
        X = build_feature_vector(radiant, dire, {int(k): v for k, v in hero_id_to_index.items()})
        prob = float(model.predict_proba(X.reshape(1, -1))[0, 1])
        return prob if is_radiant else (1.0 - prob)
```

### Pattern 7: WinConditionBadge.tsx Extension

**What:** Display `"Teamfight 54%"` inside the allied archetype pill.

```tsx
// In WinConditionBadge.tsx — add win_probability prop
interface WinConditionBadgeProps {
  winCondition: WinConditionResponse;
  winProbability?: number | null;  // 0.0-1.0
}

// In the allied archetype span, append the probability
{formatArchetype(winCondition.allied_archetype)}
{winProbability != null && (
  <span className="ml-1 text-secondary/80">{Math.round(winProbability * 100)}%</span>
)}
```

The confidence opacity on the badge already communicates uncertainty — no separate confidence display needed (per locked decision).

### Anti-Patterns to Avoid

- **Using joblib/pickle for XGBoost models:** Cross-version incompatible. Use `model.save_model("path.ubj")` / `model.load_model("path.ubj")` — the XGBoost team's official recommendation since v2.0.
- **Sending win probability to Claude:** Probability is post-LLM enrichment only (matches the existing `win_condition` pattern in `recommender.py`). Never send it in the user message to Claude.
- **Training in the Docker container:** Training belongs in an offline script. Docker containers should only load pre-built artifacts.
- **Missing fallback when models not found:** Always handle `_win_predictor_ready = False` gracefully — return `None` and let the frontend hide the probability display.
- **Not filtering game_mode = 22:** Public matches include ability draft, turbo, etc. Always filter `game_mode = 22` (All Pick) and `lobby_type = 7` (ranked) in the SQL.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Gradient boosted classifier | Custom decision tree ensemble | `xgboost.XGBClassifier` | XGBoost handles regularization, feature importance, column subsampling, GPU support; battle-tested in Kaggle competitions |
| Train/test split + metrics | Manual array slicing + accuracy loop | `sklearn.model_selection.train_test_split` + `sklearn.metrics` | Stratified splits, AUC calculation, cross-validation |
| Feature vector shape | Custom dict-based encoding | numpy array with hero_id_to_index mapping from DataCache | DataCache already has all hero IDs; build the mapping once |
| JSON serialization of large matrices | Custom CSV or SQLite | `json.dump` with `None` for sparse values | 126×126 matrix is ~64KB per bracket uncompressed; simple to load/update |

**Key insight:** The data pipeline (download → featurize → train → save) is 200 lines of Python. Everything beyond that is handled by XGBoost and scikit-learn — no custom ML infrastructure needed.

---

## Common Pitfalls

### Pitfall 1: No `patch` column on `public_matches`

**What goes wrong:** Assuming a `patch` column exists and writing `WHERE patch = '7.41'` — query returns no rows.

**Why it happens:** The OpenDota schema separates match-level data (`public_matches`) from replay-parsed data (`match_patch`). Only full parsed matches have a `match_patch` record, and `public_matches` is ~15% sample with no parsed data.

**How to avoid:** Filter by `start_time >= 1742774400` (Unix epoch for 2026-03-24, the 7.41 release date). To make the script patch-agnostic, define `PATCH_741_START_EPOCH = 1742774400` as a constant at the top of the training script.

**Warning signs:** Empty result set when querying with `WHERE patch =`.

---

### Pitfall 2: Hero ID gaps break one-hot indexing

**What goes wrong:** Using `hero_id` directly as an array index gives a 146-dim sparse vector with gaps where retired/unreleased hero IDs would be. The feature vector isn't 252-dim, it's larger and has mostly zeros in the middle.

**Why it happens:** Hero IDs are not contiguous — they range from 1 to ~146 with missing IDs (e.g. IDs 24, 60, 107+ have gaps).

**How to avoid:** Build `hero_id_to_index` as a sorted dict `{hero_id: 0-based_idx}` from `DataCache.get_all_heroes()`. This gives a dense 126-dim encoding. Embed this mapping in `matrices.json` alongside the matrices so training and inference use identical indexing.

**Warning signs:** `IndexError` during inference, or models trained with one hero set silently giving wrong predictions when hero roster changes.

---

### Pitfall 3: `radiant_team` / `dire_team` may be `null` in API response

**What goes wrong:** Some `public_matches` rows have `null` for `radiant_team` or `dire_team` if match data was partially recorded. Array unpacking fails.

**Why it happens:** OpenDota parses match data asynchronously; not every match has full draft data populated.

**How to avoid:** Filter `WHERE array_length(radiant_team, 1) = 5 AND array_length(dire_team, 1) = 5` in the SQL. Also validate in the training script: `if row["radiant_team"] is None or len(row["radiant_team"]) != 5: continue`.

**Warning signs:** `TypeError: 'NoneType' is not subscriptable` in training script.

---

### Pitfall 4: XGBoost native format vs scikit-learn wrapper

**What goes wrong:** Training with `XGBClassifier` (scikit-learn wrapper) then calling `model.save_model()` saves only the booster, not the scikit-learn metadata. Loading with `XGBClassifier()` then `load_model()` works but `predict_proba` may not be available on the reloaded object in some versions.

**Why it happens:** `XGBClassifier.save_model()` saves the internal `Booster`, not the full sklearn wrapper state.

**How to avoid:** After `load_model()`, call `model.predict_proba(X)` — test this explicitly in the training script's verification step. Alternatively, use `xgb.Booster` directly and call `booster.predict(xgb.DMatrix(X))` which returns probabilities directly. The Booster API is simpler for inference-only use.

**Warning signs:** `AttributeError: 'XGBClassifier' object has no attribute 'classes_'` after loading.

**Recommended pattern for inference-only loading:**
```python
booster = xgb.Booster()
booster.load_model("models/win_predictor_bracket_2.ubj")
dmat = xgb.DMatrix(X.reshape(1, -1))
prob = float(booster.predict(dmat)[0])  # returns probability directly
```

---

### Pitfall 5: `avg_rank_tier` is a float, not an int

**What goes wrong:** Filtering `WHERE avg_rank_tier = 45` returns no rows because the column is `double precision` (float) and stored as an average like `44.8`.

**Why it happens:** `avg_rank_tier` is the average across all players in the match — it's a mean of integer rank tiers, so it's a float like `44.8`.

**How to avoid:** Use `BETWEEN` range filters as shown in Pattern 1. This naturally handles float values within a bracket range.

**Warning signs:** Zero rows returned for a bracket query with `= 45` exact match.

---

### Pitfall 6: Cold-start model absence in Docker

**What goes wrong:** First deployment has no model files; the `models/` directory is empty; `DataCache.load_win_predictor()` finds no `.ubj` files; every `/api/recommend` call returns `win_probability: null`.

**Why it happens:** The training script must be run before deployment, and model artifacts must be committed to git or copied into the image.

**How to avoid:** Commit the trained model artifacts to git. The `models/` directory with `.ubj` and `matrices.json` files is ~2-3MB total — acceptable to version-control. Document this as a pre-deployment step in the training script's docstring. The graceful fallback (`win_probability: null` → badge shows archetype only) ensures the app remains functional even without models.

**Warning signs:** `_win_predictor_ready = False` in startup logs.

---

### Pitfall 7: Partial draft prediction instability

**What goes wrong:** User has only 5 allies selected (no opponents yet). The model predicts on a half-filled feature vector (allies present, opponents all zeros). Result is misleading — opponent zeros aren't "no opponents", they're noise.

**Why it happens:** One-hot encoding doesn't distinguish "hero not picked" from "hero not in pool".

**How to avoid:** Require all 10 heroes (5 + 5) for a prediction. Return `None` if `len(allied) + len(enemies) < 10`. The CONTEXT.md leaves this as Claude's discretion — the correct choice is "wait for complete draft" (cleaner, no misleading partial signals). Implement as a guard at the top of `WinPredictor.predict()`.

**Warning signs:** Win probability swinging wildly as opponents are added one by one.

---

## Code Examples

### OpenDota SQL Explorer request pattern
```python
# Source: OpenDota API docs + confirmed endpoint from community usage
import urllib.parse

BASE_URL = "https://api.opendota.com/api"
PATCH_741_START = 1742774400  # Unix epoch 2026-03-24

BRACKET_FILTERS = {
    1: "avg_rank_tier BETWEEN 10 AND 39",    # Herald-Crusader
    2: "avg_rank_tier BETWEEN 40 AND 59",    # Archon-Legend
    3: "avg_rank_tier BETWEEN 60 AND 79",    # Ancient-Divine
    4: "avg_rank_tier >= 80",                # Immortal
}

def build_bracket_sql(bracket: int, limit: int = 40000, offset: int = 0) -> str:
    rank_filter = BRACKET_FILTERS[bracket]
    return f"""
    SELECT match_id, radiant_win, radiant_team, dire_team, avg_rank_tier
    FROM public_matches
    WHERE start_time >= {PATCH_741_START}
      AND {rank_filter}
      AND game_mode = 22
      AND lobby_type = 7
      AND array_length(radiant_team, 1) = 5
      AND array_length(dire_team, 1) = 5
    ORDER BY match_id DESC
    LIMIT {limit} OFFSET {offset}
    """
```

### XGBoost Booster inference (recommended over XGBClassifier for load)
```python
# Source: XGBoost 3.2.0 official docs on Model IO
import xgboost as xgb
import numpy as np

# Save (during training — XGBClassifier)
classifier.get_booster().save_model("models/win_predictor_bracket_2.ubj")

# Load (at runtime — Booster only, no sklearn overhead)
booster = xgb.Booster()
booster.load_model("models/win_predictor_bracket_2.ubj")

# Inference
X = build_feature_vector(radiant_ids, dire_ids, hero_id_to_index)
dmat = xgb.DMatrix(X.reshape(1, -1))
prob = float(booster.predict(dmat)[0])  # scalar probability Radiant wins
```

### main.py startup extension
```python
# In prismlab/backend/main.py lifespan function
async with async_session() as session:
    await data_cache.load(session)

# After DB cache load, load ML artifacts (synchronous file I/O, fast)
data_cache.load_win_predictor(models_dir="models")
logger.info("WinPredictor ready: %s", data_cache._win_predictor_ready)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pickle / joblib for XGBoost | Native `.ubj` (UBJSON) format | XGBoost 2.0+ (2023) | Cross-version stability; pickle was always version-fragile |
| XGBoost 1.x with sklearn wrapper | XGBoost 3.x with Booster API for inference | 2024-2026 | Lighter inference path; `Booster.predict()` returns probabilities directly |
| Full parsed matches for hero data | `public_matches.radiant_team` / `dire_team` arrays | Available since 2017 | No replay parsing needed; hero arrays available in 15% sample |
| One model across all skill levels | Per-bracket models | Community best practice | Hero strength varies significantly by rank tier; better calibration |

**Deprecated/outdated:**
- `pickle.dump(model, f)` for XGBoost: version-fragile, officially deprecated in favor of `save_model()`
- Using `avg_mmr` (the old column): replaced by `avg_rank_tier` in the current `public_matches` schema. Some older tutorials reference `avg_mmr` which no longer exists in this table.

---

## Open Questions

1. **How many post-7.41 matches are available right now?**
   - What we know: Patch 7.41 released 2026-03-24 — that's 5 days before this research. The pool is likely 50k-100k matches total across all brackets, not yet 200k.
   - What's unclear: Will the training script need to pull pre-7.41 matches (e.g., 7.40) to reach the 200k target? PRED-02 says "current patch" but there may not be 200k yet.
   - Recommendation: The training script should check row count per bracket and log a warning if below 50k. The planner should document this as a known risk — the first training run may use 7.40 + 7.41 matches combined to hit 200k, then be retrained as 7.41 data accumulates. Alternatively, drop the 200k requirement to "as many as available" with a minimum of 50k.

2. **Hero ID ceiling — are there 126 heroes or more?**
   - What we know: DataCache loads heroes from DB; the training script's `generate_combinations` lists ~140 heroes. OpenDota has 126 actively played heroes in ranked.
   - What's unclear: The exact count changes with new hero releases. The feature vector dimension must match between training and inference.
   - Recommendation: Always derive `n_heroes` from `len(DataCache.get_all_heroes())` at training time, and save this count into `matrices.json` as `"n_heroes": 126`. At inference time, validate `n_heroes` matches before loading model.

3. **`XGBClassifier.predict_proba` after `load_model`**
   - What we know: The XGBoost docs note that sklearn wrapper metadata (classes_, n_features_in_) is NOT saved by `save_model()`.
   - What's unclear: Whether `predict_proba` works correctly on a re-loaded `XGBClassifier` in XGBoost 3.2.0.
   - Recommendation: Use the `Booster` API for inference as shown in Code Examples. Saves complexity and avoids the ambiguity entirely. Train with `XGBClassifier`, save with `classifier.get_booster().save_model()`, load with `Booster().load_model()`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Dockerfile / training script | In Docker container | 3.12-slim | — |
| xgboost | Training script + runtime | Not yet installed | 3.2.0 available on PyPI | — (must install) |
| scikit-learn | Training script only | Not yet installed | 1.8.0 available on PyPI | — (must install) |
| numpy | Training + runtime | Not yet installed | 2.4.4 available on PyPI | — (must install) |
| OpenDota API | Data download | HTTP endpoint | api.opendota.com | — (rate limited; 60/min free) |

**Missing dependencies with no fallback:**
- `xgboost`, `scikit-learn`, `numpy` must be added to `requirements.txt` — they are not currently installed in the backend.

**Missing dependencies with fallback:**
- If OpenDota Explorer is unavailable or returns insufficient data, the training script should fail gracefully with a clear error message rather than training on an empty dataset. The deployed app continues to work without a model (win_probability returns null).

---

## Sources

### Primary (HIGH confidence)
- `odota/core` GitHub — `sql/create_tables.sql` — confirmed `public_matches` schema (radiant_team, dire_team arrays; no patch column)
- PyPI `xgboost` — version 3.2.0 confirmed as latest stable, Python 3.12+ compatible
- PyPI `scikit-learn` — version 1.8.0 confirmed as latest stable
- XGBoost Model IO docs — confirmed native `.ubj` format best practice over joblib/pickle
- Existing codebase — `opendota_client.py`, `cache.py`, `schemas.py`, `recommender.py`, `WinConditionBadge.tsx` directly read

### Secondary (MEDIUM confidence)
- OpenDota blog + API docs search results — Explorer endpoint format `GET /api/explorer?sql=...`, 30s timeout, rate limits 60 req/min
- OpenDota explorer example URL (from search results) — confirmed `public_player_matches` table existence and join pattern
- andreiapostoae/dota2-predictor project — confirmed synergy/counter matrix definition and 59-65% accuracy ceiling for hero-only draft features
- Liquipedia — Patch 7.41 release date 2026-03-24 (epoch ~1742774400)
- ranktier library (marcusmunch) — confirmed two-digit rank_tier encoding (tens=tier, ones=star)

### Tertiary (LOW confidence)
- Single-source: `avg_rank_tier` specific range boundaries (10-39 Herald-Crusader etc.) — derived from rank_tier encoding convention, verified by example `Archon[2] = 42` from ranktier library

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on PyPI with exact versions
- Architecture patterns: HIGH — all patterns derived from existing codebase conventions + confirmed OpenDota schema
- Pitfalls: HIGH — most pitfalls confirmed from official schema (no patch column), XGBoost docs (save_model), community ML projects
- OpenDota rank bracket filter values: MEDIUM — derived from two-digit encoding convention, spot-checked against examples

**Research date:** 2026-03-29
**Valid until:** 2026-05-01 (stable Python libs; OpenDota schema changes slowly; rank tier encoding is Valve API stable)
