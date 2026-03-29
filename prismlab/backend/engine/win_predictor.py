"""Statistical win probability prediction from hero draft compositions.

Uses pre-trained XGBoost models (one per MMR bracket) loaded from the DataCache.
Inference uses the Booster API directly (not XGBClassifier) to avoid sklearn
wrapper issues after load_model() -- see 30-RESEARCH.md Pitfall 4.

Input: allied hero IDs, enemy hero IDs, is_radiant flag, bracket (1-4).
Output: float 0.0-1.0 (allied win probability) or None (model unavailable/partial draft).
"""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def build_feature_vector(
    radiant_ids: list[int],
    dire_ids: list[int],
    hero_id_to_index: dict[int, int],
    n_heroes: int,
) -> "np.ndarray":
    """Build 252-dim one-hot feature vector from radiant and dire hero IDs.

    First n_heroes positions = radiant, next n_heroes positions = dire.
    Unknown hero IDs (not in hero_id_to_index) are silently skipped.
    """
    vec = np.zeros(n_heroes * 2, dtype=np.float32)
    for hid in radiant_ids:
        idx = hero_id_to_index.get(hid)
        if idx is not None:
            vec[idx] = 1.0
    for hid in dire_ids:
        idx = hero_id_to_index.get(hid)
        if idx is not None:
            vec[n_heroes + idx] = 1.0
    return vec


class WinPredictor:
    """Stateless inference wrapper around DataCache-held XGBoost Booster models.

    All methods are synchronous (model inference is CPU-bound, no I/O).
    """

    def predict(
        self,
        allied_hero_ids: list[int],
        enemy_hero_ids: list[int],
        is_radiant: bool,
        bracket: int,
        cache: object,  # DataCache -- avoid circular import with type hint
    ) -> float | None:
        """Return allied team win probability (0.0-1.0), or None.

        Returns None when:
        - Model not loaded (_win_predictor_ready is False)
        - Fewer than 10 total heroes (allied + enemy) -- partial draft
        - Bracket model not found in cache
        - xgboost not installed (ImportError handled in load_win_predictor)

        Allied perspective: probability is always from allied team's view.
        If user is Dire, the Radiant win probability is inverted (1 - prob).
        """
        if not getattr(cache, "_win_predictor_ready", False):
            return None

        total_heroes = len(allied_hero_ids) + len(enemy_hero_ids)
        if total_heroes < 10:
            return None  # Require full 10-hero draft per PRED-01

        model = cache._win_models.get(bracket)
        if model is None:
            logger.debug("WinPredictor: no model for bracket %d", bracket)
            return None

        bracket_data = cache._matrices.get(bracket, {})
        raw_mapping = bracket_data.get("hero_id_to_index", {})
        hero_id_to_index = {int(k): v for k, v in raw_mapping.items()}
        n_heroes = bracket_data.get("n_heroes", 126)

        # Frame as radiant/dire from the model's perspective
        radiant_ids = allied_hero_ids if is_radiant else enemy_hero_ids
        dire_ids = enemy_hero_ids if is_radiant else allied_hero_ids

        X = build_feature_vector(radiant_ids, dire_ids, hero_id_to_index, n_heroes)

        try:
            import xgboost as xgb
            dmat = xgb.DMatrix(X.reshape(1, -1))
            radiant_win_prob = float(model.predict(dmat)[0])
        except Exception as exc:
            logger.warning("WinPredictor inference failed: %s", exc)
            return None

        # Return allied win probability
        return radiant_win_prob if is_radiant else (1.0 - radiant_win_prob)
