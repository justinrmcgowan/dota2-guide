"""Tests for system prompt token budget and content constraints (Phase 19, DATA-04).

Validates that the system prompt:
1. Stays under the 5,000 token budget
2. Contains ONLY directives -- no dynamic data
3. Includes all v4.0 directive sections
4. Is a stable constant (no per-request variation)
"""
import re
import math

from engine.prompts.system_prompt import SYSTEM_PROMPT


class TestSystemPromptBudget:
    """Verify system prompt stays within token budget."""

    def test_token_budget(self):
        """DATA-04: System prompt must be under 5,000 tokens.

        Uses conservative estimate: ceil(chars / 3.5) tokens.
        English text averages ~4 chars/token; 3.5 is conservative.
        """
        estimated_tokens = math.ceil(len(SYSTEM_PROMPT) / 3.5)
        assert estimated_tokens < 5000, (
            f"System prompt estimated at {estimated_tokens} tokens "
            f"({len(SYSTEM_PROMPT)} chars / 3.5). Budget: 5,000 tokens."
        )

    def test_reasonable_minimum_size(self):
        """System prompt should be substantial enough to guide Claude."""
        assert len(SYSTEM_PROMPT) > 2000, (
            f"System prompt is only {len(SYSTEM_PROMPT)} chars -- "
            "seems too short after v4.0 additions."
        )


class TestSystemPromptNoDynamicData:
    """Verify system prompt contains no dynamic per-request data."""

    def test_no_specific_win_rates(self):
        """DATA-04: No specific win rate percentages in system prompt.

        Win rates like '58%' or '41.2%' are dynamic data that belongs
        in the user message. Directive-style references like 'win rate
        drops sharply' are fine.
        """
        # Match patterns like "58%", "41.2%", "62.5%"
        win_rate_pattern = r'\b\d{1,3}\.?\d*%'
        matches = re.findall(win_rate_pattern, SYSTEM_PROMPT)
        assert len(matches) == 0, (
            f"System prompt contains specific percentages: {matches}. "
            "Move to user message."
        )

    def test_no_specific_timing_targets(self):
        """DATA-04: No specific minute targets like 'BKB before 25 minutes'.

        Timing RANGES in examples are OK if they are directive-style
        (e.g. '15-25 min window'). But specific prescriptive targets
        with win rates ('BKB before 25 min has 58% WR') are dynamic.
        """
        # Match "before N minutes" or "by N min" with associated win rates
        prescriptive_pattern = r'before \d+ minutes? has \d+%|by \d+ min.+\d+%'
        matches = re.findall(prescriptive_pattern, SYSTEM_PROMPT, re.IGNORECASE)
        assert len(matches) == 0, (
            f"System prompt contains prescriptive timing targets: {matches}. "
            "Move timing benchmarks to user message."
        )

    def test_no_hero_ability_descriptions(self):
        """DATA-04: No hero ability descriptions with damage numbers.

        References to abilities in examples are OK ('Zeus's Arc Lightning').
        But stat blocks ('deals 120 damage, 6s cooldown') are dynamic data.
        """
        # Match damage number patterns like "120 damage", "6s cooldown"
        stat_pattern = r'\b\d{2,4}\s*(damage|heal|mana|armor|hp)\b'
        matches = re.findall(stat_pattern, SYSTEM_PROMPT, re.IGNORECASE)
        # Allow the example section to have some numbers for illustration
        # The key check is that these aren't hero-specific stat blocks
        # We allow up to 3 matches (from the existing example section)
        assert len(matches) <= 3, (
            f"System prompt contains {len(matches)} ability stat references: {matches}. "
            "Keep stat data in user message."
        )

    def test_no_item_catalog(self):
        """DATA-04: System prompt does not contain an item list or catalog."""
        # No lines that look like "- Item Name (cost: 4050g)"
        catalog_pattern = r'^\s*-\s+\w.+\(cost:\s*\d+g?\)'
        matches = re.findall(catalog_pattern, SYSTEM_PROMPT, re.MULTILINE)
        assert len(matches) == 0, (
            f"System prompt contains item catalog entries: {matches}. "
            "Item catalogs belong in user message."
        )


class TestSystemPromptV4Directives:
    """Verify v4.0 directive sections are present."""

    def test_timing_benchmarks_directive(self):
        """DATA-04: System prompt includes timing benchmark reasoning directives."""
        assert "Timing Benchmarks" in SYSTEM_PROMPT, (
            "Missing 'Timing Benchmarks' directive section."
        )

    def test_counter_item_specificity_directive(self):
        """DATA-04: System prompt includes counter-item specificity directives."""
        assert "Counter-Item Specificity" in SYSTEM_PROMPT, (
            "Missing 'Counter-Item Specificity' directive section."
        )

    def test_win_condition_framing_directive(self):
        """DATA-04: System prompt includes win condition framing directives."""
        assert "Win Condition Framing" in SYSTEM_PROMPT, (
            "Missing 'Win Condition Framing' directive section."
        )

    def test_build_path_awareness_directive(self):
        """DATA-04: System prompt includes build path awareness directives."""
        assert "Build Path Awareness" in SYSTEM_PROMPT, (
            "Missing 'Build Path Awareness' directive section."
        )

    def test_conditional_directive_pattern(self):
        """v4.0 directives use conditional 'If section is present' pattern.

        New directive sections should reference optional context sections
        (timing, abilities, strategy) with 'If...present' guards so they
        don't confuse Claude when those sections are absent.
        """
        # At least 2 conditional guards expected for new sections
        conditional_count = SYSTEM_PROMPT.count("If") + SYSTEM_PROMPT.count("if")
        assert conditional_count >= 4, (
            f"Only {conditional_count} conditional guards found. "
            "v4.0 directives should use 'If [section] is present' patterns."
        )


class TestSystemPromptIsConstant:
    """Verify system prompt is a stable constant."""

    def test_is_string_constant(self):
        """DATA-06: SYSTEM_PROMPT is a plain string, not callable."""
        assert isinstance(SYSTEM_PROMPT, str)
        assert not callable(SYSTEM_PROMPT)

    def test_json_output_instruction_preserved(self):
        """Existing JSON-only output instruction must be preserved."""
        assert "RAW JSON ONLY" in SYSTEM_PROMPT

    def test_mmr_identity_preserved(self):
        """Existing 8K+ MMR identity must be preserved."""
        assert "8000" in SYSTEM_PROMPT or "8K" in SYSTEM_PROMPT
