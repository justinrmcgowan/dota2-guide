# Deferred Items - Phase 14

## Pre-existing Test Failures (Out of Scope)

1. `test_context_builder.py::TestSystemPromptAllyRules::test_system_prompt_has_team_coordination` - System prompt missing "## Team Coordination" section
2. `test_context_builder.py::TestSystemPromptAllyRules::test_system_prompt_has_aura_dedup_rule` - System prompt missing aura dedup rule
3. `test_context_builder.py::TestSystemPromptAllyRules::test_system_prompt_has_combo_awareness_rule` - System prompt missing combo awareness rule
4. `test_context_builder.py::TestSystemPromptAllyRules::test_system_prompt_has_gap_filling_rule` - System prompt missing gap filling rule
5. `test_context_builder.py::TestSystemPromptNeutralRules::test_system_prompt_has_rank_by_hero_synergy` - System prompt missing neutral synergy section
6. `test_context_builder.py::TestSystemPromptNeutralRules::test_system_prompt_has_build_path_interaction` - System prompt missing build path interaction section

These failures are about system prompt content strings and are NOT caused by Phase 14 changes. The system prompt was likely restructured in a previous phase.
