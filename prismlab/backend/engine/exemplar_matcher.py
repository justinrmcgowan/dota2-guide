"""Archetype matcher for few-shot exemplar selection.

Loads gold-standard exemplar JSONs from engine/prompts/exemplars/ and
selects the 1-2 closest matches for a given request based on role +
threat profile scoring.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_EXEMPLAR_DIR = Path(__file__).parent / "prompts" / "exemplars"


def load_exemplars() -> list[dict[str, Any]]:
    """Load all exemplar JSON files from the exemplars directory."""
    exemplars = []
    for path in sorted(_EXEMPLAR_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            data["_file"] = path.name
            exemplars.append(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load exemplar %s: %s", path.name, e)
    return exemplars


class ExemplarMatcher:
    """Select 1-2 closest exemplars for a recommendation request."""

    def __init__(self, exemplars: list[dict[str, Any]] | None = None):
        self.exemplars = exemplars if exemplars is not None else load_exemplars()

    def select(
        self,
        role: int,
        threat_profile: str | None = None,
        matchup_type: str | None = None,
        max_results: int = 2,
    ) -> list[dict[str, Any]]:
        """Score exemplars and return the top 1-2 matches.

        Scoring:
        - role match: +3 points (exact), +1 for same category (core vs support)
        - threat_profile match: +2 points (exact), +1 partial
        - matchup_type match: +1 point

        Returns empty list if no exemplar scores above threshold (1 point minimum).
        """
        scored = []
        for ex in self.exemplars:
            score = 0
            # Role scoring
            ex_role = ex.get("role", 0)
            if ex_role == role:
                score += 3
            elif (ex_role <= 3 and role <= 3) or (ex_role >= 4 and role >= 4):
                score += 1  # same category (core/support)

            # Threat profile scoring
            if threat_profile and ex.get("threat_profile"):
                if ex["threat_profile"] == threat_profile:
                    score += 2
                elif threat_profile in ex.get("threat_profile", ""):
                    score += 1

            # Matchup type scoring
            if matchup_type and ex.get("matchup_type") == matchup_type:
                score += 1

            if score >= 1:
                scored.append((score, ex))

        # Sort by score descending, take top N
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:max_results]]

    def format_exemplar(self, exemplar: dict[str, Any]) -> str:
        """Format an exemplar as a compact string for injection into user message."""
        hero = exemplar.get("hero_example", "Unknown Hero")
        enemy = exemplar.get("enemy_example", "Unknown Enemies")
        rec = exemplar.get("recommendation", {})
        strategy = rec.get("overall_strategy", "")

        lines = [f"### Example: {hero} vs {enemy}"]
        for phase in rec.get("phases", []):
            phase_name = phase.get("phase", "unknown")
            items = phase.get("items", [])
            item_strs = []
            for item in items:
                name = item.get("item_name", "?")
                reasoning = item.get("reasoning", "")
                item_strs.append(f"{name}: {reasoning}")
            if item_strs:
                lines.append(f"**{phase_name}:** " + " | ".join(item_strs))
        if strategy:
            lines.append(f"**Strategy:** {strategy}")
        return "\n".join(lines)
