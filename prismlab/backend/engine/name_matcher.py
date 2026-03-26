"""Fuzzy name matching for Vision output against DB records.

Maps Claude Vision's extracted hero and item names to database records
using exact case-insensitive matching first, then SequenceMatcher fallback.
Includes confidence resolution based on Vision certainty + match quality.

Exports: match_hero_name, match_item_name, resolve_confidence
"""

from difflib import SequenceMatcher


def match_hero_name(vision_name: str, heroes: list) -> tuple[object | None, float]:
    """Match a Vision-extracted hero name to a Hero ORM object.

    Args:
        vision_name: Hero name string from Claude Vision output.
        heroes: List of Hero ORM objects with localized_name attribute.

    Returns:
        Tuple of (matched_hero_or_None, match_ratio).
        Ratio is 1.0 for exact match, 0.0-1.0 for fuzzy, 0.0 if no match.
    """
    if not vision_name or not vision_name.strip():
        return None, 0.0

    lower = vision_name.lower().strip()

    # Exact case-insensitive match first
    for hero in heroes:
        if hero.localized_name.lower() == lower:
            return hero, 1.0

    # Fuzzy match fallback
    best_match = None
    best_ratio = 0.0
    for hero in heroes:
        ratio = SequenceMatcher(None, lower, hero.localized_name.lower()).ratio()
        if ratio > best_ratio and ratio > 0.7:
            best_ratio = ratio
            best_match = hero

    return best_match, best_ratio


def match_item_name(vision_name: str, items: list) -> tuple[object | None, float]:
    """Match a Vision-extracted item name to an Item ORM object.

    Args:
        vision_name: Item name string from Claude Vision output.
        items: List of Item ORM objects with name attribute.

    Returns:
        Tuple of (matched_item_or_None, match_ratio).
        Ratio is 1.0 for exact match, 0.0-1.0 for fuzzy, 0.0 if no match.
    """
    if not vision_name or not vision_name.strip():
        return None, 0.0

    lower = vision_name.lower().strip()

    # Exact case-insensitive match first
    for item in items:
        if not item.name:
            continue
        if item.name.lower() == lower:
            return item, 1.0

    # Fuzzy match fallback
    best_match = None
    best_ratio = 0.0
    for item in items:
        if not item.name:
            continue
        ratio = SequenceMatcher(None, lower, item.name.lower()).ratio()
        if ratio > best_ratio and ratio > 0.7:
            best_ratio = ratio
            best_match = item

    return best_match, best_ratio


def resolve_confidence(vision_confidence: str, match_ratio: float) -> str:
    """Translate Vision confidence + match ratio to high/medium/low.

    Combines Claude's self-reported certainty with the quality of the
    fuzzy match against the database to produce a final confidence score.

    Args:
        vision_confidence: "certain", "likely", or "uncertain" from Vision.
        match_ratio: 0.0-1.0 from SequenceMatcher.

    Returns:
        "high", "medium", or "low".
    """
    if vision_confidence == "certain" and match_ratio >= 0.95:
        return "high"
    if vision_confidence in ("certain", "likely") and match_ratio >= 0.85:
        return "medium"
    return "low"
