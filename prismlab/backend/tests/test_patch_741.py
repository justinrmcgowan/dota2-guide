"""Patch 7.41 data correctness tests.

Validates that the database reflects Dota 2 patch 7.41 changes:
- New items exist with correct costs
- Removed items (Cornucopia) are absent
- Changed item costs are accurate
- Rules engine has no stale item references
- System prompt stays within token budget
"""
import inspect
import math
import re

import pytest

from data.cache import data_cache
from engine.rules import RulesEngine


# New 7.41 items -- these require a live OpenDota re-seed to appear in DB.
# Skipped until production re-seed is performed.
NEW_741_ITEMS = [
    "wizard_hat",
    "shawl",
    "splintmail",
    "chasm_stone",
    "consecrated_wraps",
    "essence_distiller",
    "crellas_crozier",
    "hydras_breath",
]


@pytest.mark.usefixtures("test_db_setup")
class TestPatch741Items:
    """Data correctness tests for 7.41 item changes."""

    @pytest.mark.skip(reason="Requires live OpenDota re-seed data")
    @pytest.mark.parametrize("internal_name", NEW_741_ITEMS)
    def test_new_items_exist(self, internal_name: str):
        """After re-seed, each new 7.41 item should exist in the item catalog.

        Unskip after the first production re-seed against OpenDota 7.41 data.
        """
        item_id = data_cache.item_name_to_id(internal_name)
        assert item_id is not None, (
            f"New 7.41 item '{internal_name}' not found in data_cache. "
            f"Run a fresh seed from OpenDota to pick up 7.41 items."
        )

    def test_cornucopia_removed(self):
        """Cornucopia should not appear in the item catalog after 7.41."""
        item_id = data_cache.item_name_to_id("cornucopia")
        assert item_id is None, (
            "Cornucopia (removed in 7.41) still present in item catalog. "
            "Re-seed from OpenDota to remove deprecated items."
        )

    def test_shivas_guard_cost_updated(self):
        """Shiva's Guard cost should be 4500g in 7.41 (down from 5175g)."""
        item_id = data_cache.item_name_to_id("shivas_guard")
        assert item_id is not None, "Shiva's Guard not found in data_cache"
        item = data_cache.get_item(item_id)
        assert item is not None
        assert item.cost == 4500, (
            f"Shiva's Guard cost is {item.cost}, expected 4500 (7.41 value)"
        )

    def test_blade_mail_cost_updated(self):
        """Blade Mail cost should be 2300g in 7.41 (up from 2100g)."""
        item_id = data_cache.item_name_to_id("blade_mail")
        assert item_id is not None, "Blade Mail not found in data_cache"
        item = data_cache.get_item(item_id)
        assert item is not None
        assert item.cost == 2300, (
            f"Blade Mail cost is {item.cost}, expected 2300 (7.41 value)"
        )


@pytest.mark.usefixtures("test_db_setup")
class TestPatch741RulesIntegrity:
    """Verify rules engine has no stale references after 7.41."""

    def test_rules_no_cornucopia_reference(self):
        """Rules engine source must not reference 'cornucopia' (removed item)."""
        source = inspect.getsource(RulesEngine)
        assert "cornucopia" not in source.lower(), (
            "Rules engine still references 'cornucopia', which was removed in 7.41."
        )

    def test_rules_no_stale_item_references(self):
        """Every _item_id('xxx') call in rules.py must resolve to a valid item.

        Extracts all internal_name string literals from _item_id() calls and
        verifies each exists in data_cache.
        """
        source = inspect.getsource(RulesEngine)
        # Match _item_id("xxx") or _item_id('xxx')
        pattern = r'_item_id\(["\']([a-z_]+)["\']\)'
        item_refs = re.findall(pattern, source)
        assert len(item_refs) > 0, "No _item_id() calls found in rules source"

        missing = []
        for name in item_refs:
            if data_cache.item_name_to_id(name) is None:
                missing.append(name)

        assert len(missing) == 0, (
            f"Rules engine references {len(missing)} items not in data_cache: {missing}. "
            f"Either add test fixtures or update rules for 7.41."
        )

    def test_minimum_rule_count_741(self):
        """Rules engine should have at least 22 rules after 7.41 updates."""
        engine = RulesEngine(data_cache)
        rule_count = len(engine._rules)
        assert rule_count >= 22, (
            f"Only {rule_count} rules found, expected >= 22. "
            f"Rules may have been accidentally removed during 7.41 update."
        )


@pytest.mark.usefixtures("test_db_setup")
class TestPatch741PromptBudget:
    """Verify system prompt stays within token budget after 7.41 changes."""

    def test_prompt_token_budget_with_741_hints(self):
        """System prompt must stay under 5000 tokens after any 7.41 additions.

        Uses conservative estimate: ceil(chars / 3.5) tokens.
        """
        from engine.prompts.system_prompt import SYSTEM_PROMPT
        estimated_tokens = math.ceil(len(SYSTEM_PROMPT) / 3.5)
        assert estimated_tokens < 5000, (
            f"System prompt estimated at {estimated_tokens} tokens "
            f"({len(SYSTEM_PROMPT)} chars / 3.5). Budget: 5,000 tokens."
        )


@pytest.mark.usefixtures("test_db_setup")
class TestPatch741ExcludedItems:
    """Verify EXCLUDED_ITEMS does not contain valid purchasable 7.41 items."""

    def test_excluded_items_no_valid_purchasable(self):
        """EXCLUDED_ITEMS in cache.get_relevant_items should not exclude
        any valid purchasable 7.41 items."""
        source = inspect.getsource(data_cache.get_relevant_items)
        # Extract EXCLUDED_ITEMS entries
        pattern = r'"([a-z_]+)"'
        excluded = re.findall(pattern, source.split("EXCLUDED_ITEMS")[1].split("}")[0])

        # None of the new 7.41 purchasable items should be in EXCLUDED_ITEMS
        new_purchasable = [
            "wizard_hat", "shawl", "splintmail", "chasm_stone",
            "consecrated_wraps", "essence_distiller",
            "crellas_crozier", "hydras_breath",
        ]
        wrongly_excluded = [item for item in new_purchasable if item in excluded]
        assert len(wrongly_excluded) == 0, (
            f"EXCLUDED_ITEMS incorrectly contains 7.41 purchasable items: {wrongly_excluded}"
        )
