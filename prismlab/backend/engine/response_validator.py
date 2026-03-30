"""Post-parse validation for Claude LLM recommendations.

Catches logically wrong recommendations before the user sees them:
phase-cost violations, cross-phase duplicates, missing counter items,
and empty required phases. Logs failure rates for prompt tuning.
"""

import logging
from dataclasses import dataclass, field

from data.cache import DataCache
from engine.schemas import RecommendPhase, RecommendRequest

logger = logging.getLogger(__name__)

# Validation metrics (module-level counters for logging)
_validation_runs = 0
_validation_failures = 0

# Known stun/disable-heavy heroes (hero IDs).
# These heroes have at least one reliable hard disable (stun, hex, or similar).
# Used by counter-logic audit when ability data doesn't have explicit stun tags.
_STUN_HERO_IDS: set[int] = {
    3,    # Bane (Fiend's Grip)
    5,    # Crystal Maiden (Frostbite)
    7,    # Earthshaker (Fissure, Aftershock)
    17,   # Storm Spirit (Electric Vortex)
    19,   # Tiny (Avalanche)
    22,   # Zeus (Lightning Bolt mini-stun)
    25,   # Lina (Light Strike Array)
    26,   # Lion (Earth Spike, Hex)
    27,   # Shadow Shaman (Shackles, Hex)
    30,   # Witch Doctor (Paralyzing Cask)
    31,   # Lich (Sinister Gaze)
    32,   # Enigma (Black Hole)
    33,   # Tidehunter (Ravage)
    36,   # Sven (Storm Hammer)
    37,   # Vengeful Spirit (Magic Missile)
    38,   # Sand King (Burrowstrike)
    40,   # Wraith King (Wraithfire Blast)
    42,   # Skeleton King -> Wraith King duplicate
    50,   # Dazzle (not a stunner, but still relevant for disable chains)
    51,   # Clockwerk (Battery Assault, Hookshot)
    53,   # Nature's Prophet (Sprout is a root)
    58,   # Enchantress (Enchant)
    59,   # Huskar (Berserker's Blood -- not a stunner; remove)
    62,   # Centaur Warrunner (Hoof Stomp)
    65,   # Magnus (Reverse Polarity)
    66,   # Treant Protector (Overgrowth)
    69,   # Doom (Infernal Blade stun)
    72,   # Nyx Assassin (Impale)
    77,   # Jakiro (Ice Path)
    80,   # Batrider (Flaming Lasso)
    84,   # Ogre Magi (Fireblast)
    86,   # Rubick (Telekinesis)
    87,   # Disruptor (Static Storm)
    90,   # Keeper of the Light (Will-O-Wisp)
    95,   # Tusk (Walrus Punch)
    97,   # Magnus -> already listed
    99,   # Bristleback (no stun, remove)
    100,  # Tusk -> already listed
    104,  # Legion Commander (Duel)
    106,  # Ember Spirit (Searing Chains root)
    110,  # Phoenix (Supernova stun)
    113,  # Oracle (Fortune's End root)
    114,  # Winter Wyvern (Winter's Curse)
    120,  # Pangolier (Rolling Thunder stun)
    126,  # Void Spirit (Aether Remnant)
    128,  # Snapfire (Firesnap Cookie stun)
    129,  # Mars (Spear of Mars stun)
    131,  # Dawnbreaker (Celestial Hammer stun)
    136,  # Muerta (not a stunner; remove)
}

# More refined: focus on heroes with reliable hard disables
RELIABLE_STUN_HEROES: set[int] = {
    3,    # Bane
    7,    # Earthshaker
    19,   # Tiny
    25,   # Lina
    26,   # Lion
    27,   # Shadow Shaman
    32,   # Enigma
    33,   # Tidehunter
    36,   # Sven
    37,   # Vengeful Spirit
    38,   # Sand King
    40,   # Wraith King
    51,   # Clockwerk
    62,   # Centaur Warrunner
    65,   # Magnus
    69,   # Doom
    72,   # Nyx Assassin
    77,   # Jakiro
    80,   # Batrider
    84,   # Ogre Magi
    86,   # Rubick
    95,   # Tusk
    104,  # Legion Commander
    110,  # Phoenix
    114,  # Winter Wyvern
    120,  # Pangolier
    128,  # Snapfire
    129,  # Mars
}


@dataclass
class ValidationIssue:
    """A single validation issue found in the recommendation."""

    check: str       # e.g. "phase_cost", "duplicate", "missing_counter", "empty_phase"
    severity: str    # "error" (triggers retry) or "warning" (logged only)
    message: str     # Human-readable description for retry prompt


@dataclass
class ValidationResult:
    """Aggregate result of all validation checks."""

    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_messages(self) -> list[str]:
        """Messages from error-severity issues (used for retry prompt)."""
        return [i.message for i in self.issues if i.severity == "error"]

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)


class ResponseValidator:
    """Validates Claude's parsed recommendation for logical consistency.

    Checks:
    1. Phase-cost validation: starting < 625g, laning each < 2500g, core each > 1000g
    2. Cross-phase duplicate detection: same item_id in multiple phases
    3. Counter-logic audit: if 3+ stun heroes and no BKB/Linken's, flag
    4. Empty required phases: late_game and situational must not be empty
    """

    # Cost thresholds per phase
    STARTING_BUDGET = 625
    LANING_MAX_PER_ITEM = 2500
    CORE_MIN_PER_ITEM = 1000

    # BKB-adjacent items (internal names) that satisfy "has disable protection"
    DISABLE_PROTECTION_ITEMS = {"bkb", "black_king_bar", "sphere", "aeon_disk"}

    def __init__(self, cache: DataCache):
        self.cache = cache

    def validate(
        self,
        phases: list[RecommendPhase],
        request: RecommendRequest,
    ) -> ValidationResult:
        """Run all validation checks against parsed LLM output.

        Returns ValidationResult with issues list. Caller decides
        whether to retry based on has_errors.
        """
        global _validation_runs, _validation_failures
        _validation_runs += 1

        issues: list[ValidationIssue] = []
        issues.extend(self._check_phase_costs(phases))
        issues.extend(self._check_cross_phase_duplicates(phases))
        issues.extend(self._check_counter_logic(phases, request))
        issues.extend(self._check_empty_phases(phases))

        has_errors = any(i.severity == "error" for i in issues)
        if has_errors:
            _validation_failures += 1
            logger.warning(
                "Validation failed (%d errors, %d warnings). "
                "Failure rate: %d/%d (%.1f%%)",
                sum(1 for i in issues if i.severity == "error"),
                sum(1 for i in issues if i.severity == "warning"),
                _validation_failures,
                _validation_runs,
                (_validation_failures / _validation_runs * 100) if _validation_runs > 0 else 0,
            )
            for issue in issues:
                logger.info("  [%s] %s: %s", issue.severity, issue.check, issue.message)
        elif issues:
            for issue in issues:
                logger.debug("  [%s] %s: %s", issue.severity, issue.check, issue.message)

        return ValidationResult(valid=not has_errors, issues=issues)

    def _check_phase_costs(self, phases: list[RecommendPhase]) -> list[ValidationIssue]:
        """Validate item costs per phase against budget thresholds.

        - starting: total cost must be <= 625g
        - laning: each individual item must be < 2500g
        - core: each individual item should be > 1000g (warning only -- some
          cheap core items like BKB components are legitimate)
        """
        issues: list[ValidationIssue] = []

        for phase in phases:
            if phase.phase == "starting":
                total_cost = 0
                for item in phase.items:
                    cached = self.cache.get_item(item.item_id)
                    if cached and cached.cost:
                        total_cost += cached.cost
                if total_cost > self.STARTING_BUDGET:
                    issues.append(ValidationIssue(
                        check="phase_cost",
                        severity="error",
                        message=(
                            f"Starting items total {total_cost}g exceeds the "
                            f"{self.STARTING_BUDGET}g starting gold budget. "
                            f"Remove or replace items to fit within budget."
                        ),
                    ))

            elif phase.phase == "laning":
                for item in phase.items:
                    cached = self.cache.get_item(item.item_id)
                    if cached and cached.cost and cached.cost > self.LANING_MAX_PER_ITEM:
                        issues.append(ValidationIssue(
                            check="phase_cost",
                            severity="error",
                            message=(
                                f"Laning item '{cached.name}' costs {cached.cost}g, "
                                f"exceeding the {self.LANING_MAX_PER_ITEM}g laning phase limit. "
                                f"Move to core phase or replace with a cheaper alternative."
                            ),
                        ))

            elif phase.phase == "core":
                for item in phase.items:
                    cached = self.cache.get_item(item.item_id)
                    if cached and cached.cost and cached.cost < self.CORE_MIN_PER_ITEM:
                        issues.append(ValidationIssue(
                            check="phase_cost",
                            severity="warning",
                            message=(
                                f"Core item '{cached.name}' costs only {cached.cost}g, "
                                f"which is unusually cheap for a core-phase item. "
                                f"Consider moving to laning phase."
                            ),
                        ))

        return issues

    def _check_cross_phase_duplicates(self, phases: list[RecommendPhase]) -> list[ValidationIssue]:
        """Detect same item_id appearing in multiple phases.

        The recommender already runs _deduplicate_across_phases, but this
        catches duplicates that survived (e.g. if Claude re-introduced them).
        """
        issues: list[ValidationIssue] = []
        seen: dict[int, str] = {}  # item_id -> first-seen phase

        for phase in phases:
            for item in phase.items:
                if item.item_id in seen:
                    issues.append(ValidationIssue(
                        check="duplicate",
                        severity="error",
                        message=(
                            f"Item '{item.item_name}' (ID {item.item_id}) appears in both "
                            f"'{seen[item.item_id]}' and '{phase.phase}' phases. "
                            f"Remove the duplicate -- each item should appear in exactly one phase."
                        ),
                    ))
                else:
                    seen[item.item_id] = phase.phase

        return issues

    def _check_counter_logic(
        self, phases: list[RecommendPhase], request: RecommendRequest
    ) -> list[ValidationIssue]:
        """Check if recommendations include disable protection against stun-heavy enemies.

        If 3+ opponents are known stun/disable heroes and no BKB/Linken's/Aeon Disk
        is recommended, flag as a warning (not error -- Claude may have valid reasons).
        """
        issues: list[ValidationIssue] = []

        # Count stun heroes among all opponents
        all_enemy_ids = set(request.all_opponents) | set(request.lane_opponents)
        stun_count = sum(1 for eid in all_enemy_ids if eid in RELIABLE_STUN_HEROES)

        if stun_count < 3:
            return issues

        # Check if any recommended item is a disable protection item
        has_protection = False
        for phase in phases:
            for item in phase.items:
                cached = self.cache.get_item(item.item_id)
                if cached and cached.internal_name in self.DISABLE_PROTECTION_ITEMS:
                    has_protection = True
                    break
            if has_protection:
                break

        if not has_protection:
            stun_hero_names = []
            for eid in all_enemy_ids:
                if eid in RELIABLE_STUN_HEROES:
                    hero = self.cache.get_hero(eid)
                    stun_hero_names.append(hero.localized_name if hero else f"Hero#{eid}")

            issues.append(ValidationIssue(
                check="missing_counter",
                severity="warning",
                message=(
                    f"Enemy team has {stun_count} stun/disable heroes "
                    f"({', '.join(stun_hero_names)}) but no BKB, Linken's Sphere, "
                    f"or Aeon Disk is recommended. Consider adding disable protection."
                ),
            ))

        return issues

    def _check_empty_phases(self, phases: list[RecommendPhase]) -> list[ValidationIssue]:
        """Check that late_game and situational phases are present.

        A complete recommendation should have suggestions for late game and
        situational decisions. Their absence is a warning (not blocking).
        """
        issues: list[ValidationIssue] = []
        phase_names = {p.phase for p in phases}

        if "late_game" not in phase_names:
            issues.append(ValidationIssue(
                check="empty_phase",
                severity="warning",
                message=(
                    "No 'late_game' phase in recommendations. "
                    "Include at least 1-2 late-game items for scaling options."
                ),
            ))

        if "situational" not in phase_names:
            issues.append(ValidationIssue(
                check="empty_phase",
                severity="warning",
                message=(
                    "No 'situational' phase in recommendations. "
                    "Include conditional items for adapting to game developments."
                ),
            ))

        return issues


def get_validation_metrics() -> dict[str, int | float]:
    """Return current validation metrics for monitoring."""
    return {
        "total_runs": _validation_runs,
        "total_failures": _validation_failures,
        "failure_rate_pct": round(
            (_validation_failures / _validation_runs * 100)
            if _validation_runs > 0 else 0, 1
        ),
    }
