# Phase 26: Engine Optimization - Research

**Researched:** 2026-03-28
**Domain:** Local LLM inference (Ollama), fine-tuning pipeline (Unsloth/QLoRA), multi-mode engine routing, API cost management
**Confidence:** HIGH

## Summary

This phase transforms Prismlab's recommendation engine from a single-path Claude API dependency into a 3-mode architecture (Fast/Auto/Deep) with local LLM inference via Ollama. The existing `HybridRecommender` already has a clean rules-then-LLM-then-merge pipeline with fallback architecture, making this extension natural.

The Ollama HTTP API at `/api/chat` directly mirrors the Claude API's message-based interface. Structured JSON output is supported via a `format` parameter that accepts a JSON schema -- Prismlab's existing `LLM_OUTPUT_SCHEMA` can be passed directly. Qwen 2.5 7B Instruct is the recommended local model: it outperforms Llama 3.1 8B on structured JSON generation benchmarks and runs comfortably on consumer hardware at ~4GB VRAM (Q4_K_M quantization) with 30-40+ tokens/sec on GPU.

Fine-tuning uses Unsloth + QLoRA on a free Google Colab T4 GPU with ChatML-format training data. The pipeline is: generate training pairs via Claude Batch API (50% cost discount) -> fine-tune with Unsloth -> export to GGUF Q4_K_M -> deploy to Ollama via Modelfile. Estimated cost for 7,500 training examples: ~$11-19 USD via batch API.

**Primary recommendation:** Use `/api/chat` with Qwen 2.5 7B Instruct (Q4_K_M), structured output via `format` parameter with the existing JSON schema, and the official `ollama` Python library's `AsyncClient` for async integration matching the current httpx patterns.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Three recommendation modes: Fast (rules-only, <1s), Auto (Ollama primary + Claude fallback, <5s), Deep (Claude always, <15s)
- **D-02:** Default mode: Auto
- **D-03:** Auto mode routing: rules fire first, then Ollama. If rules produce 8+ confident items AND matchup is straightforward, Ollama handles it. If complex (unusual hero combos, <3 items from rules), escalate to Claude API.
- **D-04:** Ollama model: fine-tune Llama 3.1 8B or Qwen 2.5 7B, deploy as Q4_K_M on Unraid Ollama (port 11434)
- **D-05:** Training data by running Claude across hero/role/matchup combinations using existing system prompt + context builder
- **D-06:** Target 5,000-10,000 training pairs covering all heroes, roles, common matchups
- **D-07:** Fast mode skips ALL LLM calls, returns rules output with no NL reasoning
- **D-08:** Fast mode still returns full 5-phase structure
- **D-09:** Auto mode is default -- Claude only for edge cases in Auto, always in Deep
- **D-10:** Monthly API budget cap in Settings (soft warn at 80%, hard stop at 100%)
- **D-11:** Display current month's API usage in Settings panel
- **D-12:** Fast: <1 second
- **D-13:** Auto: <5 seconds (Ollama on Unraid hardware)
- **D-14:** Deep: <15 seconds (Claude API)

### Claude's Discretion
- Ollama API integration details (HTTP endpoint, model loading)
- Training data generation script design
- Fine-tuning approach (QLoRA, hyperparams)
- Confidence scoring for Auto mode routing
- Token counting / cost estimation implementation
- Response cache strategy per mode (different TTLs?)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Project Constraints (from CLAUDE.md)

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + SQLite + Pydantic
- **Existing HTTP client:** httpx 0.28.1 (already in requirements.txt)
- **LLM client:** anthropic 0.86.0 (AsyncAnthropic wrapper)
- **Hybrid engine architecture:** Rules fire first, LLM second, always have fallback
- **Structured JSON output:** Parse and validate before returning to frontend
- **Type hints throughout, async endpoints, Pydantic models for validation**
- **Docker Compose deployment on Unraid** (backend port 8420, frontend port 8421)
- **Ollama already running on Unraid** at `http://100.78.161.13:11434`

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ollama | latest (PyPI) | Official Python client for Ollama API | Official library, AsyncClient mirrors project's async patterns, handles streaming/schema natively |
| httpx | 0.28.1 (existing) | HTTP client fallback for Ollama | Already in requirements.txt, raw HTTP fallback if ollama lib has issues |
| anthropic | 0.86.0 (existing) | Claude API for Deep mode + training data generation | Already integrated, Haiku 4.5 at $1/$5 per MTok |
| unsloth | latest | QLoRA fine-tuning with 2x speedup | De facto standard for efficient consumer-GPU fine-tuning, direct Ollama export |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.12.5 (existing) | Schema for Ollama structured output + validation | `model_json_schema()` generates the format parameter for Ollama |
| tiktoken or anthropic.count_tokens | -- | Token counting for cost tracking | Estimate Claude API costs per request |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ollama` Python lib | Raw httpx to `/api/chat` | More control but more boilerplate; ollama lib handles schema/streaming cleanly |
| Qwen 2.5 7B | Llama 3.1 8B | Qwen significantly better at structured JSON output; Llama slightly faster inference |
| Unsloth | Axolotl | Axolotl more flexible but slower, heavier dependencies; Unsloth 2x faster on Colab T4 |

**Installation:**
```bash
pip install ollama
```

No other new production dependencies needed. Unsloth is a training-time dependency (runs on Colab, not on the Unraid server).

## Architecture Patterns

### Recommended Project Structure
```
prismlab/backend/
├── engine/
│   ├── llm.py              # Existing Claude LLMEngine (rename to claude_engine.py)
│   ├── ollama_engine.py     # NEW: OllamaEngine with same generate() interface
│   ├── recommender.py       # Extend HybridRecommender with mode routing
│   ├── mode_router.py       # NEW: Mode selection + Auto escalation logic
│   ├── cost_tracker.py      # NEW: Per-request token counting + monthly budget
│   ├── rules.py             # Existing 23 rules (no changes)
│   ├── context_builder.py   # Existing (no changes, shared by Claude + Ollama)
│   ├── schemas.py           # Extend RecommendRequest with mode field
│   └── prompts/
│       └── system_prompt.py # Existing (shared by both engines)
├── config.py                # Add mode, ollama_url, api_budget_monthly
├── scripts/
│   └── generate_training_data.py  # NEW: Offline script for training data
└── requirements.txt         # Add ollama
```

### Pattern 1: Engine Protocol (Duck Typing / Protocol)
**What:** Both `LLMEngine` (Claude) and `OllamaEngine` share the same `generate()` signature so the recommender can swap them transparently.
**When to use:** Always -- this is the core abstraction enabling mode switching.
**Example:**
```python
# Source: existing llm.py pattern + Ollama integration
from typing import Protocol

class LLMBackend(Protocol):
    async def generate(
        self, user_message: str
    ) -> tuple[LLMRecommendation | None, FallbackReason | None]:
        ...

class OllamaEngine:
    """Ollama API wrapper matching LLMEngine interface."""

    def __init__(self, model: str = "prismlab-qwen:q4_k_m") -> None:
        from ollama import AsyncClient
        self.client = AsyncClient(host=settings.ollama_url)
        self.model = model

    async def generate(
        self, user_message: str
    ) -> tuple[LLMRecommendation | None, FallbackReason | None]:
        try:
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                format=LLMRecommendation.model_json_schema(),
                options={"temperature": 0.3, "num_predict": 5120},
                stream=False,
            )
            text = response["message"]["content"]
            return (LLMRecommendation.model_validate_json(text), None)
        except Exception as e:
            logger.warning("Ollama error: %s", e)
            return (None, FallbackReason.ollama_error)
```

### Pattern 2: Mode Router in Recommender
**What:** `HybridRecommender.recommend()` checks the mode at the top and routes to the appropriate path.
**When to use:** On every recommendation request.
**Example:**
```python
# Source: extending existing recommender.py
async def recommend(self, request: RecommendRequest, db: AsyncSession) -> RecommendResponse:
    mode = request.mode or settings.recommendation_mode

    if mode == "fast":
        return await self._fast_path(request, db)
    elif mode == "auto":
        return await self._auto_path(request, db)
    else:  # deep
        return await self._deep_path(request, db)

async def _auto_path(self, request, db):
    """Rules first, then Ollama, escalate to Claude on failure or complexity."""
    rules_items = self.rules.evaluate(request)

    # Escalation check: complex matchup?
    should_escalate = self._should_escalate(request, rules_items)

    if should_escalate and not self.cost_tracker.budget_exceeded():
        # Use Claude (Deep path)
        return await self._deep_path(request, db)

    # Use Ollama
    user_message = await self.context_builder.build(request, rules_items, db)
    llm_result, fallback_reason = await self.ollama.generate(user_message)

    if llm_result is None:
        # Ollama failed -- try Claude if budget allows
        if not self.cost_tracker.budget_exceeded():
            llm_result, fallback_reason = await self.llm.generate(user_message)

        if llm_result is None:
            # Both failed -- rules only
            return self._build_rules_only_response(rules_items, fallback_reason)

    return self._build_merged_response(rules_items, llm_result, ...)
```

### Pattern 3: Cost Tracker (Monthly Budget)
**What:** SQLite-backed monthly token/cost accumulator with soft warn at 80%, hard stop at 100%.
**When to use:** Before every Claude API call, checked in Auto mode routing and Deep mode.
**Example:**
```python
# Source: new cost_tracker.py
class CostTracker:
    """Track Claude API usage per month in SQLite."""

    HAIKU_INPUT_RATE = 1.0 / 1_000_000   # $1 per MTok
    HAIKU_OUTPUT_RATE = 5.0 / 1_000_000   # $5 per MTok

    async def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        cost = (input_tokens * self.HAIKU_INPUT_RATE) + (output_tokens * self.HAIKU_OUTPUT_RATE)
        # Insert into usage_log table, keyed by month

    def budget_exceeded(self) -> bool:
        return self.current_month_cost >= settings.api_budget_monthly

    def budget_warning(self) -> bool:
        return self.current_month_cost >= settings.api_budget_monthly * 0.8
```

### Anti-Patterns to Avoid
- **Calling Ollama synchronously in async endpoint:** Always use `AsyncClient` -- blocking calls will stall the entire FastAPI event loop.
- **Sharing mutable state between Ollama and Claude engines:** Each engine should be stateless; the recommender orchestrates.
- **Bypassing the existing merge/validate pipeline:** Ollama output MUST go through the same `_merge()`, `_validate_item_ids()`, and enrichment steps as Claude output.
- **Hardcoding the Ollama URL:** Use `settings.ollama_url` so Docker networking works (Unraid host IP differs from localhost).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ollama HTTP protocol | Custom httpx wrapper with streaming, JSON parsing | `ollama` Python library `AsyncClient` | Handles streaming, schema validation, reconnects, model loading states |
| JSON schema for structured output | Manual schema dict | `LLMRecommendation.model_json_schema()` (Pydantic) | Already have the Pydantic model; auto-generates valid JSON schema |
| Fine-tuning infrastructure | Custom training loop | Unsloth + QLoRA on Google Colab | 2x faster, handles GGUF export, free GPU |
| Token counting for cost tracking | Character-based estimation | Anthropic response `usage` object | Every Claude API response includes `input_tokens` and `output_tokens` in the usage field |
| Chat template for fine-tuned model | Manual template string | Unsloth `get_chat_template()` + auto-Modelfile | Wrong chat template is the #1 cause of poor fine-tuned model performance in Ollama |

**Key insight:** The Ollama Python library + Pydantic schema generation eliminates most of the integration complexity. The existing `LLMRecommendation` Pydantic model serves triple duty: (1) Claude output validation, (2) Ollama structured output schema, (3) fine-tuning output target.

## Common Pitfalls

### Pitfall 1: Wrong Chat Template in Fine-Tuned Model
**What goes wrong:** Model fine-tuned with Unsloth performs well during training but produces garbage in Ollama.
**Why it happens:** The chat template used during training (ChatML for Qwen 2.5) doesn't match what Ollama applies at inference time.
**How to avoid:** Use Unsloth's auto-generated Modelfile which embeds the correct chat template. When creating the Ollama model, always use `ollama create` from the Unsloth output directory -- never manually write the Modelfile.
**Warning signs:** Model outputs raw tokens, repeats the prompt, or produces malformed JSON despite working in training eval.

### Pitfall 2: Ollama Model Not Loaded (Cold Start Latency)
**What goes wrong:** First request to Ollama after model eviction takes 10-30 seconds as the model loads into VRAM.
**Why it happens:** Ollama evicts models from memory after `keep_alive` expires (default 5 minutes).
**How to avoid:** Set `keep_alive` to a longer duration (e.g., `"30m"` or `"-1"` for indefinite) in the API call or Modelfile. Alternatively, send a warmup request on backend startup.
**Warning signs:** First recommendation after idle period is 10x slower than subsequent ones.

### Pitfall 3: Ollama Returning Invalid JSON Despite Schema
**What goes wrong:** Even with the `format` parameter, the model occasionally produces JSON that doesn't validate against the Pydantic model (e.g., wrong item_ids, missing phases).
**Why it happens:** Structured output constrains the JSON *structure* but not the *semantic content*. A 7B model may hallucinate item_ids or skip phases.
**How to avoid:** Keep the existing `_validate_item_ids()` pipeline for Ollama output. Add a phase completeness check (all 5 phases present). On validation failure, escalate to Claude in Auto mode.
**Warning signs:** High rate of filtered-out invalid item_ids in logs.

### Pitfall 4: Budget Tracking Race Condition
**What goes wrong:** Two concurrent requests both check budget, both see it as under limit, both fire Claude calls, exceeding the budget.
**Why it happens:** Budget check and usage recording are not atomic.
**How to avoid:** Use optimistic concurrency -- check budget before call, record usage after call. Accept that the budget is a soft limit (can overshoot by one request's cost). This is acceptable per D-10 design.
**Warning signs:** Monthly cost slightly exceeds budget cap.

### Pitfall 5: Training Data Quality -- Garbage In, Garbage Out
**What goes wrong:** Fine-tuned model produces generic recommendations like "BKB is good."
**Why it happens:** Training data was generated without the full context builder pipeline (missing matchup data, item catalog, ability threats).
**How to avoid:** Use the ACTUAL `ContextBuilder.build()` method to generate training prompts, not simplified templates. Each training example must include the full user message that Claude would see in production.
**Warning signs:** Fine-tuned model's reasoning doesn't reference specific enemy abilities or hero names.

### Pitfall 6: Docker Network Isolation
**What goes wrong:** Backend container can't reach Ollama at `http://100.78.161.13:11434`.
**Why it happens:** Docker bridge network isolates container from host network by default.
**How to avoid:** Use `network_mode: host` for the backend container, OR use the Docker host gateway (`host.docker.internal` or the Unraid host IP). Since the Ollama instance is on the Unraid host (not in Docker), the backend container needs to reach the host network. The existing config uses bridge networking -- the Tailscale IP `100.78.161.13` should be accessible from within the container since it's a routable IP.
**Warning signs:** `ConnectionRefusedError` or timeout when trying to reach Ollama from the backend container.

## Code Examples

### Ollama AsyncClient with Structured Output (Production Pattern)
```python
# Source: Ollama Python library docs + Pydantic schema generation
from ollama import AsyncClient
from engine.schemas import LLMRecommendation
from engine.prompts.system_prompt import SYSTEM_PROMPT
from config import settings

client = AsyncClient(host=settings.ollama_url)

response = await client.chat(
    model="prismlab-qwen:q4_k_m",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ],
    format=LLMRecommendation.model_json_schema(),
    options={
        "temperature": 0.3,
        "num_predict": 5120,  # equivalent to max_tokens
        "num_ctx": 8192,       # context window
    },
    stream=False,
    keep_alive="30m",
)

text = response["message"]["content"]
result = LLMRecommendation.model_validate_json(text)
```

### Ollama Raw HTTP Fallback (if ollama lib has issues)
```python
# Source: Ollama REST API docs - /api/chat endpoint
import httpx
import json

async with httpx.AsyncClient(timeout=30.0) as client:
    resp = await client.post(
        f"{settings.ollama_url}/api/chat",
        json={
            "model": "prismlab-qwen:q4_k_m",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "format": LLMRecommendation.model_json_schema(),
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 5120},
            "keep_alive": "30m",
        },
    )
    data = resp.json()
    text = data["message"]["content"]
```

### Claude API Cost Extraction from Response
```python
# Source: Anthropic API docs - response usage object
# The existing LLMEngine.generate() response includes usage data:
response = await self.client.messages.create(...)

# Extract token counts from response
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens

# Calculate cost
cost = (input_tokens * 1.0 / 1_000_000) + (output_tokens * 5.0 / 1_000_000)

# Record for budget tracking
await self.cost_tracker.record_usage(input_tokens, output_tokens)
```

### Training Data Generation (Offline Script)
```python
# Source: Existing context_builder.py + Claude Batch API pattern
# scripts/generate_training_data.py

import json
import itertools

# Generate hero/role/matchup combinations
heroes = cache.get_all_heroes()  # ~125 heroes
roles = [1, 2, 3, 4, 5]
common_matchups = get_common_lane_matchups()  # top 3 opponents per hero per role

for hero, role, opponents in itertools.product(heroes, roles, common_matchups):
    # Build context using actual ContextBuilder
    request = RecommendRequest(
        hero_id=hero.id, role=role,
        playstyle=default_playstyle(role),
        side="radiant", lane=default_lane(role),
        lane_opponents=opponents,
    )
    rules_items = rules.evaluate(request)
    user_message = await context_builder.build(request, rules_items, db)

    # Claude generates the output (use Batch API for 50% discount)
    llm_result, _ = await llm.generate(user_message)
    if llm_result:
        training_pair = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": llm_result.model_dump_json()},
            ]
        }
        output_file.write(json.dumps(training_pair) + "\n")
```

### Modelfile for Fine-Tuned Model
```
# Source: Ollama import docs + Unsloth export
FROM ./prismlab-qwen-q4_k_m.gguf

PARAMETER temperature 0.3
PARAMETER num_predict 5120
PARAMETER num_ctx 8192

SYSTEM """You are an elite Dota 2 item coach (8000+ MMR)..."""
```

Note: Unsloth auto-generates this Modelfile with the correct chat template. Use the auto-generated one rather than writing manually.

## Ollama API Reference

### /api/chat Endpoint (Recommended)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model | string | Yes | Model name (e.g., "prismlab-qwen:q4_k_m") |
| messages | array | Yes | `[{role, content}]` with roles: system, user, assistant |
| format | string or object | No | `"json"` for free-form JSON, or JSON schema object for structured output |
| stream | boolean | No | Default true; set false for single response |
| options | object | No | `{temperature, num_predict, num_ctx, top_p, seed, stop}` |
| keep_alive | string | No | How long to keep model loaded (default "5m", use "30m" or "-1") |

### Response Fields (Non-Streaming)
| Field | Type | Description |
|-------|------|-------------|
| model | string | Model name used |
| message | object | `{role: "assistant", content: "..."}` |
| done | boolean | Always true for non-streaming |
| total_duration | int | Total time in nanoseconds |
| prompt_eval_count | int | Input token count |
| eval_count | int | Output token count |
| eval_duration | int | Generation time in nanoseconds |

**Tokens/sec calculation:** `eval_count / (eval_duration / 1_000_000_000)`

## Model Selection: Qwen 2.5 7B Instruct

### Why Qwen 2.5 7B over Llama 3.1 8B
| Criterion | Qwen 2.5 7B | Llama 3.1 8B | Winner |
|-----------|-------------|-------------|--------|
| Structured JSON quality | Excellent -- "crushes structured data handling" | Good but inferior | Qwen |
| JSON schema adherence | Designed for structured output | Adequate | Qwen |
| Instruction following | Superior on benchmarks | Good | Qwen |
| Inference speed | ~30-40 tok/s Q4_K_M | ~35-45 tok/s Q4_K_M | Llama (slight) |
| VRAM (Q4_K_M) | ~4.0 GB | ~4.5 GB | Qwen |
| Fine-tuning support | Full Unsloth support, ChatML native | Full Unsloth support | Tie |
| Ollama support | `ollama pull qwen2.5:7b-instruct-q4_K_M` | `ollama pull llama3.1:8b-instruct-q4_K_M` | Tie |

**Verdict:** Qwen 2.5 7B Instruct is the clear choice for this use case. The structured JSON quality advantage is decisive for generating valid `LLMRecommendation` objects with correct item_ids, phase names, and priority values.

### Quantization: Q4_K_M
- **Size:** ~4.0 GB on disk, ~4.0 GB VRAM
- **Quality:** ~75% smaller than FP16 with minimal quality degradation
- **Speed:** 30-40+ tokens/sec on GPU, ~9 tok/s CPU-only
- **Compatibility:** Direct Ollama support, standard GGUF format

## Fine-Tuning Pipeline

### Overview
1. **Generate training data** via Claude Batch API (offline script)
2. **Fine-tune** with Unsloth + QLoRA on Google Colab (free T4 GPU)
3. **Export** to GGUF Q4_K_M
4. **Deploy** to Ollama on Unraid via `ollama create`

### Training Data Format (ChatML)
```jsonl
{"messages": [{"role": "system", "content": "You are an elite Dota 2 item coach..."}, {"role": "user", "content": "## Your Hero\nAnti-Mage (Pos 1, Farm-first playstyle, radiant safe lane)\n..."}, {"role": "assistant", "content": "{\"phases\": [...], \"overall_strategy\": \"...\"}"}]}
```

### Training Data Volume and Cost Estimate

**Target:** 7,500 examples (midpoint of 5K-10K range)

**Token estimates per example (based on current system prompt + context builder):**
- System prompt: ~2,500 tokens (measured from system_prompt.py, ~10KB)
- User message (context builder output): ~1,500-2,500 tokens (hero + opponents + items catalog + rules + sections)
- Assistant response (LLMRecommendation JSON): ~2,000-3,000 tokens (10-16 items with reasoning)
- **Total per example:** ~6,000-8,000 tokens input + ~2,500 tokens output

**Claude Haiku 4.5 Batch API pricing (50% discount):**
- Input: $0.50 / MTok (batch)
- Output: $2.50 / MTok (batch)

**Cost calculation for 7,500 examples:**
- Input tokens: 7,500 * 7,000 = 52.5M tokens -> $26.25
- Output tokens: 7,500 * 2,500 = 18.75M tokens -> $46.88
- **Total: ~$73** at standard rate, **~$36.50** at batch rate

**With prompt caching on system prompt (cache hit = 0.1x):**
- System prompt: 2,500 tokens * 7,500 = 18.75M tokens -> only $0.94 at cache rate vs $9.38 standard
- Savings: ~$8.44 on top of batch discount
- **Realistic total with caching + batch: ~$28-32**

Note: Batch API and prompt caching discounts stack. The system prompt is identical across all examples, making it highly cacheable.

### Training Data Generation Strategy

**Hero coverage:** ~125 heroes * 1-2 primary roles = ~200 hero/role combinations
**Matchup coverage:** Top 3-5 opponents per hero/role = ~800 unique hero/role/opponent triples
**Playstyle variation:** 2-3 playstyles per role = ~2,400 examples at minimum
**Side/lane variation:** 2 sides * 1 primary lane = ~4,800 examples

**Target: 7,500 examples** by sampling the most common matchups, with extra coverage for:
- High-pick-rate heroes (top 30 heroes get 2x coverage)
- Complex matchups (heroes with many counter-items)
- Edge cases (supports, unusual role assignments)

### Unsloth QLoRA Configuration
```python
# Source: Unsloth docs for Qwen 2.5 fine-tuning
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    max_seq_length=8192,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0,
    bias="none",
)

# Apply chat template
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="qwen-2.5")

# Train
from trl import SFTTrainer, SFTConfig
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=SFTConfig(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        output_dir="outputs",
        max_seq_length=8192,
    ),
)
trainer.train()

# Export to GGUF for Ollama
model.save_pretrained_gguf("prismlab-qwen", tokenizer, quantization_method="q4_k_m")
```

### Deployment to Ollama
```bash
# On Unraid server after copying GGUF file
cd /path/to/gguf/output
ollama create prismlab-qwen:q4_k_m -f Modelfile
ollama run prismlab-qwen:q4_k_m "test prompt"
```

## Auto Mode Escalation Logic

### Confidence Scoring for Routing (D-03)
```python
def should_escalate(request: RecommendRequest, rules_items: list[RuleResult]) -> bool:
    """Determine if Auto mode should escalate from Ollama to Claude.

    Escalate when:
    1. Rules produced fewer than 8 items (low rules coverage = complex matchup)
    2. Unusual hero combo (hero/role not in top 80% pick rate)
    3. More than 3 lane opponents specified (complex multi-hero interaction)
    4. Mid-game re-evaluation with enemy_context (requires nuanced reasoning)
    """
    # Low rules coverage = complex matchup
    if len(rules_items) < 8:
        return True

    # Mid-game context requires deeper reasoning
    if request.lane_result is not None or len(request.enemy_context) > 0:
        return True

    # Many opponents = complex interaction
    if len(request.lane_opponents) > 1 and len(request.all_opponents) > 3:
        return True

    return False
```

**Rationale:** The rules engine already covers ~8-12 items for straightforward matchups (Magic Stick vs spell spammers, BKB vs magic damage, etc.). When rules produce 8+ items, the matchup is well-characterized and Ollama mainly needs to fill in reasoning + laning/core items. When rules produce fewer items, the matchup is unusual and benefits from Claude's deeper reasoning.

## Cost Tracking Implementation

### Token Counting
The Anthropic Python SDK returns token counts on every response:
```python
response.usage.input_tokens   # int
response.usage.output_tokens  # int
```

Similarly, Ollama returns:
```python
response["prompt_eval_count"]  # input tokens
response["eval_count"]         # output tokens
```

### Cost Estimation Formula
```
request_cost = (input_tokens * $1.00 / 1M) + (output_tokens * $5.00 / 1M)
```

For a typical Prismlab request:
- Input: ~5,000-7,000 tokens (system prompt + context) = $0.005-0.007
- Output: ~2,500 tokens (recommendation JSON) = $0.0125
- **Per-request cost: ~$0.017-0.020**
- **Monthly cost at 100 requests/day: ~$52-60**
- **With prompt caching (system prompt cached): ~$30-40/month**

### Budget Cap Strategy
- Store monthly totals in SQLite `api_usage` table: `(month TEXT, total_cost REAL, request_count INTEGER)`
- Soft warning at 80% of budget -- frontend shows amber indicator
- Hard stop at 100% -- Auto mode stops escalating to Claude, Deep mode falls back to Auto
- Reset on 1st of each month

### Settings UI Additions
- Mode selector: 3 radio buttons (Fast / Auto / Deep) with descriptions
- Monthly budget input: Dollar amount with validation
- Current month usage display: "$X.XX / $Y.YY used (Z%)" progress bar
- Budget warning badge when > 80%

## Response Cache Strategy per Mode

| Mode | TTL | Rationale |
|------|-----|-----------|
| Fast | 60 seconds | Rules are deterministic; short TTL just prevents duplicate clicks |
| Auto | 300 seconds (existing) | Ollama output is near-deterministic with low temperature |
| Deep | 300 seconds (existing) | Claude output varies slightly; 5 min cache prevents re-calling |

Include mode in the cache key hash to prevent cross-mode cache hits.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JSON mode (`format: "json"`) | Structured output (`format: {schema}`) | Ollama 0.5+ (2024) | Schema-enforced JSON instead of hoping for valid JSON |
| llama.cpp CLI for inference | Ollama server + REST API | 2024+ | Managed model lifecycle, hot-loading, API interface |
| Full fine-tuning | QLoRA via Unsloth | 2024-2025 | 7B models trainable on free T4 GPU in <2 hours |
| Manual GGUF conversion | Unsloth direct GGUF export | 2025 | `save_pretrained_gguf()` eliminates manual llama.cpp conversion step |

## Open Questions

1. **Unraid GPU availability for Ollama**
   - What we know: Ollama is already running on Unraid at port 11434. Qwen 2.5 7B Q4_K_M needs ~4GB VRAM.
   - What's unclear: What GPU (if any) is in the Unraid server? Ollama can run CPU-only but at ~9 tok/s vs 30+ tok/s on GPU.
   - Recommendation: Check `ssh root@100.78.161.13 "ollama ps"` and `nvidia-smi` to verify GPU availability. If CPU-only, the <5s Auto mode latency target may be tight for complex prompts. Consider reducing context window size for Ollama-only requests.

2. **Fine-tuned model context window**
   - What we know: Base Qwen 2.5 7B supports 128K context. Q4_K_M quantization doesn't reduce this.
   - What's unclear: Optimal `num_ctx` for Prismlab. Current system prompt + user message is ~5,000-7,000 tokens. Setting `num_ctx=8192` should be sufficient and keeps VRAM usage low.
   - Recommendation: Use 8192. If some requests are larger (many opponents, mid-game context), monitor and increase if needed.

3. **Training data re-generation on Dota patches**
   - What we know: D-05 says use existing system prompt + context builder. Dota patches change hero abilities and item stats.
   - What's unclear: How often to re-fine-tune? How to detect when the model's recommendations are stale?
   - Recommendation: Re-generate training data and re-fine-tune after major Dota patches (every 2-3 months). The training pipeline script should be idempotent and re-runnable.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Ollama server | Auto mode LLM inference | Yes (confirmed) | Unknown -- verify | Fall back to Claude (Deep mode) |
| Python 3.12 | Backend | Yes | 3.12 | -- |
| httpx | Ollama fallback HTTP | Yes | 0.28.1 | -- |
| anthropic | Claude API (Deep mode) | Yes | 0.86.0 | -- |
| Google Colab (T4 GPU) | Fine-tuning | Yes (free) | -- | Kaggle Notebooks or RunPod |
| Qwen 2.5 7B on Ollama | Auto mode inference | Needs setup | -- | `ollama pull qwen2.5:7b-instruct-q4_K_M` |
| Docker Compose | Deployment | Yes | 2.40.3 | -- |

**Missing dependencies with no fallback:**
- None -- all paths have fallback (Auto falls back to Claude, Claude falls back to rules-only)

**Missing dependencies with fallback:**
- Fine-tuned model not yet created -- use base `qwen2.5:7b-instruct-q4_K_M` until fine-tuning is complete, then swap via config

## Sources

### Primary (HIGH confidence)
- [Ollama API docs - /api/generate](https://docs.ollama.com/api/generate) - Full request/response schema, structured output format parameter
- [Ollama API docs - /api/chat](https://github.com/ollama/ollama/blob/main/docs/api.md) - Chat endpoint with messages, format, options
- [Ollama Structured Outputs blog](https://ollama.com/blog/structured-outputs) - JSON schema in format parameter, Pydantic integration
- [Ollama Python library](https://github.com/ollama/ollama-python) - AsyncClient usage, streaming, schema support
- [Ollama Import docs](https://docs.ollama.com/import) - GGUF import, Modelfile, fine-tuned adapter deployment
- [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing) - Haiku 4.5: $1/$5 MTok, batch 50%, cache 0.1x
- [Anthropic Usage API](https://platform.claude.com/docs/en/build-with-claude/usage-cost-api) - Programmatic cost tracking
- [Unsloth Datasets Guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide) - ChatML/ShareGPT format, data quality
- [Unsloth Ollama Export](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-ollama) - GGUF export + Modelfile auto-generation

### Secondary (MEDIUM confidence)
- [LLM-stats Qwen vs Llama comparison](https://llm-stats.com/models/compare/llama-3.1-8b-instruct-vs-qwen-2.5-7b-instruct) - Benchmark comparisons
- [Qwen 2.5 official blog](https://qwenlm.github.io/blog/qwen2.5/) - Structured output improvements
- [LocalLLM VRAM guide](https://localllm.in/blog/ollama-vram-requirements-for-local-llms) - VRAM usage estimates for quantized models

### Tertiary (LOW confidence)
- Training time estimates for 7,500 examples on T4 -- needs validation by actually running the training

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Ollama API is well-documented, Python library is official, Qwen 2.5 7B is well-tested
- Architecture: HIGH - Extending existing HybridRecommender with mode routing follows established patterns
- Ollama integration: HIGH - Verified API endpoint format, structured output support, Python library
- Fine-tuning pipeline: MEDIUM - Unsloth + QLoRA is well-documented but training data generation is custom; exact training time and quality are unverified
- Cost estimates: MEDIUM - Token count estimates based on system prompt measurement; actual costs depend on context builder output variability
- Pitfalls: HIGH - Chat template issues, cold start latency, and Docker networking are well-documented failure modes

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (Ollama API is stable; re-check if Qwen 3.x or newer models release)
