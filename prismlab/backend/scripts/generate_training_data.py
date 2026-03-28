#!/usr/bin/env python3
"""Generate training data for Ollama fine-tuning.

Runs Claude API across hero/role/matchup combinations using the actual
ContextBuilder pipeline. Outputs ChatML-format JSONL for Unsloth.

Usage:
    cd prismlab/backend
    python -m scripts.generate_training_data --output data/training_data.jsonl --limit 100
    python -m scripts.generate_training_data --output data/training_data.jsonl  # all combos
    python -m scripts.generate_training_data --output data/training_data.jsonl --resume 500
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Project imports (run from prismlab/backend as cwd)
# ---------------------------------------------------------------------------
from data.cache import DataCache, data_cache, HeroCached
from data.database import engine as db_engine, async_session, Base
from data.opendota_client import OpenDotaClient
from engine.context_builder import ContextBuilder
from engine.llm import LLMEngine
from engine.rules import RulesEngine
from engine.schemas import RecommendRequest, VALID_PLAYSTYLES
from engine.prompts.system_prompt import SYSTEM_PROMPT
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hero role mapping
#
# Maps hero localized_name -> list of (role, lane) tuples.
# Each hero has 1-2 primary roles. This is intentionally conservative:
# quality > coverage. Heroes not in this map are auto-assigned from their
# DB "roles" field with a heuristic fallback.
# ---------------------------------------------------------------------------
HERO_ROLE_MAP: dict[str, list[tuple[int, str]]] = {
    # Pos 1 carries
    "Anti-Mage": [(1, "safe")],
    "Faceless Void": [(1, "safe")],
    "Phantom Assassin": [(1, "safe")],
    "Juggernaut": [(1, "safe")],
    "Spectre": [(1, "safe")],
    "Terrorblade": [(1, "safe")],
    "Morphling": [(1, "safe")],
    "Luna": [(1, "safe")],
    "Lifestealer": [(1, "safe")],
    "Slark": [(1, "safe")],
    "Wraith King": [(1, "safe")],
    "Phantom Lancer": [(1, "safe")],
    "Medusa": [(1, "safe")],
    "Drow Ranger": [(1, "safe")],
    "Sven": [(1, "safe")],
    "Troll Warlord": [(1, "safe")],
    "Ursa": [(1, "safe")],
    "Chaos Knight": [(1, "safe")],
    "Monkey King": [(1, "safe"), (2, "mid")],
    "Naga Siren": [(1, "safe")],
    "Weaver": [(1, "safe")],
    "Gyrocopter": [(1, "safe")],
    "Alchemist": [(1, "safe"), (2, "mid")],
    "Bloodseeker": [(1, "safe"), (2, "mid")],
    "Riki": [(1, "safe")],
    "Clinkz": [(1, "safe")],
    "Arc Warden": [(1, "safe"), (2, "mid")],
    "Muerta": [(1, "safe"), (2, "mid")],
    "Lone Druid": [(1, "safe")],
    "Razor": [(1, "safe"), (2, "mid")],
    "Sniper": [(1, "safe"), (2, "mid")],
    "Dragon Knight": [(2, "mid"), (1, "safe")],
    "Templar Assassin": [(2, "mid"), (1, "safe")],
    "Meepo": [(2, "mid")],
    "Huskar": [(2, "mid")],

    # Pos 2 mids
    "Storm Spirit": [(2, "mid")],
    "Invoker": [(2, "mid")],
    "Shadow Fiend": [(2, "mid")],
    "Puck": [(2, "mid")],
    "Queen of Pain": [(2, "mid")],
    "Lina": [(2, "mid"), (4, "off")],
    "Ember Spirit": [(2, "mid")],
    "Outworld Destroyer": [(2, "mid")],
    "Tinker": [(2, "mid")],
    "Zeus": [(2, "mid")],
    "Void Spirit": [(2, "mid")],
    "Kunkka": [(2, "mid")],
    "Death Prophet": [(2, "mid")],
    "Leshrac": [(2, "mid")],
    "Pangolier": [(2, "mid"), (3, "off")],
    "Windranger": [(2, "mid"), (3, "off")],
    "Broodmother": [(2, "mid"), (3, "off")],
    "Batrider": [(2, "mid"), (3, "off")],
    "Necrophos": [(2, "mid"), (3, "off")],
    "Viper": [(2, "mid")],
    "Primal Beast": [(2, "mid"), (3, "off")],

    # Pos 3 offlaners
    "Axe": [(3, "off")],
    "Tidehunter": [(3, "off")],
    "Mars": [(3, "off")],
    "Centaur Warrunner": [(3, "off")],
    "Underlord": [(3, "off")],
    "Bristleback": [(3, "off")],
    "Timbersaw": [(3, "off")],
    "Sand King": [(3, "off")],
    "Doom": [(3, "off")],
    "Legion Commander": [(3, "off")],
    "Beastmaster": [(3, "off")],
    "Enigma": [(3, "off")],
    "Night Stalker": [(3, "off")],
    "Dark Seer": [(3, "off")],
    "Slardar": [(3, "off")],
    "Clockwerk": [(3, "off"), (4, "off")],
    "Spirit Breaker": [(3, "off"), (4, "off")],
    "Brewmaster": [(3, "off")],
    "Elder Titan": [(3, "off"), (4, "off")],
    "Magnus": [(3, "off")],
    "Abaddon": [(3, "off"), (5, "safe")],
    "Omniknight": [(3, "off"), (5, "safe")],
    "Bane": [(5, "safe")],
    "Undying": [(3, "off"), (5, "safe")],
    "Vengeful Spirit": [(4, "off"), (1, "safe")],
    "Lycan": [(3, "off")],
    "Visage": [(3, "off"), (2, "mid")],
    "Dawnbreaker": [(3, "off")],
    "Marci": [(3, "off"), (4, "off")],

    # Pos 4 soft supports
    "Earth Spirit": [(4, "off")],
    "Tusk": [(4, "off")],
    "Pudge": [(4, "off")],
    "Rubick": [(4, "off")],
    "Mirana": [(4, "off")],
    "Bounty Hunter": [(4, "off")],
    "Earth Shaker": [(4, "off")],
    "Dark Willow": [(4, "off")],
    "Hoodwink": [(4, "off")],
    "Nyx Assassin": [(4, "off")],
    "Shadow Demon": [(4, "off"), (5, "safe")],
    "Snapfire": [(4, "off"), (5, "safe")],
    "Tiny": [(4, "off"), (2, "mid")],
    "Treant Protector": [(4, "off"), (5, "safe")],
    "Grimstroke": [(4, "off"), (5, "safe")],
    "Phoenix": [(4, "off"), (3, "off")],

    # Pos 5 hard supports
    "Crystal Maiden": [(5, "safe")],
    "Shadow Shaman": [(5, "safe")],
    "Witch Doctor": [(5, "safe")],
    "Warlock": [(5, "safe")],
    "Dazzle": [(5, "safe")],
    "Lich": [(5, "safe")],
    "Lion": [(5, "safe")],
    "Oracle": [(5, "safe")],
    "Io": [(5, "safe")],
    "Chen": [(5, "safe")],
    "Enchantress": [(5, "safe")],
    "Disruptor": [(5, "safe")],
    "Jakiro": [(5, "safe")],
    "Ogre Magi": [(5, "safe")],
    "Winter Wyvern": [(5, "safe")],
    "Keeper of the Light": [(5, "safe")],
    "Silencer": [(5, "safe"), (4, "off")],
    "Ancient Apparition": [(5, "safe")],
    "Skywrath Mage": [(5, "safe"), (4, "off")],
    "Techies": [(4, "off")],

    # Flex heroes
    "Nature's Prophet": [(3, "off"), (4, "off")],
    "Pugna": [(2, "mid"), (5, "safe")],
    "Vengeful Spirit": [(4, "off"), (1, "safe")],
    "Witch Doctor": [(5, "safe")],
}

# Role -> lane mapping
ROLE_TO_LANE: dict[int, str] = {
    1: "safe",
    2: "mid",
    3: "off",
    4: "off",
    5: "safe",
}


def _infer_roles_from_db(hero: HeroCached) -> list[tuple[int, str]]:
    """Infer role/lane from hero's DB roles field as a fallback.

    Uses conservative mapping: 'Carry' -> Pos 1, 'Nuker'/'Initiator' -> Pos 2/3, etc.
    Returns at most 1 role to avoid noise from uncertain inference.
    """
    if not hero.roles:
        return []

    roles_set = set(hero.roles)

    # Priority order: most distinctive role first
    if "Carry" in roles_set:
        return [(1, "safe")]
    if "Nuker" in roles_set and hero.attack_type == "Ranged":
        return [(2, "mid")]
    if "Initiator" in roles_set or "Durable" in roles_set:
        return [(3, "off")]
    if "Support" in roles_set and "Disabler" in roles_set:
        return [(5, "safe")]
    if "Support" in roles_set:
        return [(4, "off")]

    # Fallback: mid for ranged, offlane for melee
    if hero.attack_type == "Ranged":
        return [(2, "mid")]
    return [(3, "off")]


def generate_combinations(
    cache: DataCache,
) -> list[dict]:
    """Generate all hero/role/playstyle/matchup combinations.

    Returns a list of dicts with keys: hero_id, role, lane, playstyle, side,
    lane_opponents. Each dict is one training example to generate.
    """
    all_heroes = cache.get_all_heroes()
    hero_ids = [h.id for h in all_heroes]
    hero_name_map = {h.id: h.localized_name for h in all_heroes}

    combinations: list[dict] = []
    side_toggle = False  # alternates radiant/dire

    for hero in all_heroes:
        name = hero.localized_name
        role_lanes = HERO_ROLE_MAP.get(name, [])

        # Fallback: infer from DB roles if not in manual map
        if not role_lanes:
            role_lanes = _infer_roles_from_db(hero)

        if not role_lanes:
            continue

        for role, lane in role_lanes:
            valid_playstyles = list(VALID_PLAYSTYLES.get(role, set()))
            if not valid_playstyles:
                continue

            # Pick 1-2 playstyles (first is most common, second adds variety)
            selected_playstyles = valid_playstyles[:2]

            for playstyle in selected_playstyles:
                # Generate 2-3 matchups per hero/role/playstyle
                # Exclude self from opponent pool
                opponent_pool = [hid for hid in hero_ids if hid != hero.id]

                for _ in range(random.randint(2, 3)):
                    # Pick 1-2 lane opponents
                    num_opponents = random.randint(1, 2) if lane != "mid" else 1
                    lane_opponents = random.sample(
                        opponent_pool,
                        min(num_opponents, len(opponent_pool)),
                    )

                    side = "radiant" if side_toggle else "dire"
                    side_toggle = not side_toggle

                    combinations.append({
                        "hero_id": hero.id,
                        "hero_name": hero_name_map.get(hero.id, f"Hero #{hero.id}"),
                        "role": role,
                        "lane": lane,
                        "playstyle": playstyle,
                        "side": side,
                        "lane_opponents": lane_opponents,
                    })

    return combinations


async def generate_training_data(
    output_path: str,
    limit: int | None = None,
    resume: int = 0,
    delay: float = 0.5,
) -> None:
    """Main pipeline: generate combinations, call Claude, write JSONL.

    Args:
        output_path: Path to output JSONL file.
        limit: Max examples to generate (None = all).
        resume: Skip first N combinations (for resuming interrupted runs).
        delay: Seconds between API calls (rate limit protection).
    """
    # -- Initialize infrastructure --
    logger.info("Initializing database and cache...")
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        await data_cache.load(db)

    hero_count = len(data_cache.get_all_heroes())
    logger.info("Cache loaded: %d heroes", hero_count)
    if hero_count == 0:
        logger.error("No heroes in cache. Run the seed script first.")
        sys.exit(1)

    # -- Create components --
    opendota = OpenDotaClient(api_key=settings.opendota_api_key)
    context_builder = ContextBuilder(opendota_client=opendota, cache=data_cache)
    rules_engine = RulesEngine(cache=data_cache)
    llm = LLMEngine()

    # -- Generate combinations --
    logger.info("Generating hero/role/matchup combinations...")
    combos = generate_combinations(data_cache)
    random.shuffle(combos)  # Shuffle for variety when using --limit

    total_available = len(combos)
    logger.info("Generated %d total combinations", total_available)

    # Apply resume offset
    if resume > 0:
        combos = combos[resume:]
        logger.info("Resuming from %d, %d remaining", resume, len(combos))

    # Apply limit
    if limit is not None:
        combos = combos[:limit]

    total = len(combos)
    logger.info("Will generate %d training examples", total)

    # -- Open output file --
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if resume > 0 else "w"

    generated = 0
    failures = 0
    total_input_tokens = 0
    total_output_tokens = 0
    start_time = time.monotonic()

    # Haiku pricing: $1.00 / MTok input, $5.00 / MTok output
    INPUT_COST_PER_MTOK = 1.00
    OUTPUT_COST_PER_MTOK = 5.00

    with open(output, mode, encoding="utf-8") as f:
        for i, combo in enumerate(combos):
            idx = i + resume + 1  # 1-based display index accounting for resume

            try:
                # Build RecommendRequest
                request = RecommendRequest(
                    hero_id=combo["hero_id"],
                    role=combo["role"],
                    playstyle=combo["playstyle"],
                    side=combo["side"],
                    lane=combo["lane"],
                    lane_opponents=combo["lane_opponents"],
                )

                # Run rules engine
                rules_items = rules_engine.evaluate(request)

                # Build the user message (the real context_builder pipeline)
                async with async_session() as db:
                    user_message = await context_builder.build(
                        request, rules_items, db
                    )

                # Call Claude to generate the "ideal" output
                recommendation, fallback_reason = await llm.generate(user_message)

                if recommendation is None:
                    failures += 1
                    logger.warning(
                        "[%d/%d] FAILED %s (Pos %d, %s) - %s",
                        idx, total + resume, combo["hero_name"], combo["role"],
                        combo["playstyle"], fallback_reason,
                    )
                    await asyncio.sleep(delay)
                    continue

                # Track token usage
                if llm.last_usage:
                    total_input_tokens += llm.last_usage.get("input_tokens", 0)
                    total_output_tokens += llm.last_usage.get("output_tokens", 0)

                # Write ChatML JSONL line
                training_example = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                        {
                            "role": "assistant",
                            "content": recommendation.model_dump_json(),
                        },
                    ]
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
                f.flush()  # Flush after each line so progress is saved

                generated += 1

                # Progress logging every 50 examples
                if generated % 50 == 0 or generated == 1:
                    elapsed = time.monotonic() - start_time
                    rate = generated / elapsed if elapsed > 0 else 0
                    est_cost = (
                        (total_input_tokens / 1_000_000) * INPUT_COST_PER_MTOK
                        + (total_output_tokens / 1_000_000) * OUTPUT_COST_PER_MTOK
                    )
                    pct = (generated / total * 100) if total > 0 else 0
                    logger.info(
                        "[%d/%d] Generated %d (%.1f%%), %d failures, "
                        "%.1f ex/min, ~$%.2f cost so far",
                        idx, total + resume, generated, pct, failures,
                        rate * 60, est_cost,
                    )

            except Exception as e:
                failures += 1
                logger.warning(
                    "[%d/%d] ERROR %s (Pos %d) - %s: %s",
                    idx, total + resume, combo["hero_name"], combo["role"],
                    type(e).__name__, e,
                )

            # Rate limit protection
            if delay > 0:
                await asyncio.sleep(delay)

    # -- Print summary --
    elapsed = time.monotonic() - start_time
    est_cost = (
        (total_input_tokens / 1_000_000) * INPUT_COST_PER_MTOK
        + (total_output_tokens / 1_000_000) * OUTPUT_COST_PER_MTOK
    )

    logger.info("=" * 60)
    logger.info("TRAINING DATA GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info("Output: %s", output_path)
    logger.info("Generated: %d examples", generated)
    logger.info("Failures: %d", failures)
    logger.info("Total input tokens: %d", total_input_tokens)
    logger.info("Total output tokens: %d", total_output_tokens)
    logger.info("Estimated cost: $%.2f", est_cost)
    logger.info("Elapsed time: %.1f minutes", elapsed / 60)
    if generated > 0:
        logger.info("Rate: %.1f examples/minute", generated / (elapsed / 60))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate training data for Ollama fine-tuning using Claude API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Generate 10 examples for testing
  python -m scripts.generate_training_data --output data/training_data.jsonl --limit 10

  # Generate all combinations (~7500 examples)
  python -m scripts.generate_training_data --output data/training_data.jsonl

  # Resume from example 500 after interruption
  python -m scripts.generate_training_data --output data/training_data.jsonl --resume 500

  # Slower rate for lower API tier
  python -m scripts.generate_training_data --output data/training_data.jsonl --delay 1.0
""",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output JSONL file",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        help="Maximum number of training examples to generate (default: all)",
    )
    parser.add_argument(
        "--resume", "-r",
        type=int,
        default=0,
        help="Skip first N combinations (for resuming interrupted runs)",
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=0.5,
        help="Seconds between API calls (default: 0.5)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible combination shuffling (default: 42)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for `python -m scripts.generate_training_data`."""
    args = parse_args()
    random.seed(args.seed)

    logger.info("Training data generator starting")
    logger.info("Output: %s", args.output)
    logger.info("Limit: %s", args.limit or "all")
    logger.info("Resume: %d", args.resume)
    logger.info("Delay: %.1fs", args.delay)
    logger.info("Seed: %d", args.seed)

    asyncio.run(
        generate_training_data(
            output_path=args.output,
            limit=args.limit,
            resume=args.resume,
            delay=args.delay,
        )
    )


if __name__ == "__main__":
    main()
