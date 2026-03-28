"""Track Claude API usage per month with budget cap enforcement.

In-memory totals with SQLite persistence via the ApiUsage model.
Soft warning at 80% of budget, hard stop at 100%.

Pricing: Claude Haiku 4.5 at $1/MTok input, $5/MTok output.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from data.models import ApiUsage

logger = logging.getLogger(__name__)


class CostTracker:
    """Track Claude API usage per month. In-memory with SQLite persistence."""

    # Claude Haiku 4.5 pricing (per token)
    HAIKU_INPUT_RATE: float = 1.0 / 1_000_000   # $1 per million input tokens
    HAIKU_OUTPUT_RATE: float = 5.0 / 1_000_000   # $5 per million output tokens

    def __init__(self) -> None:
        self._current_month: str = self._month_key()
        self._month_cost: float = 0.0
        self._month_requests: int = 0
        self._loaded: bool = False

    @staticmethod
    def _month_key() -> str:
        return datetime.now().strftime("%Y-%m")

    def _check_month_rollover(self) -> None:
        """Reset in-memory totals if the month has changed."""
        current = self._month_key()
        if current != self._current_month:
            logger.info(
                "Month rollover: %s -> %s, resetting cost tracker",
                self._current_month, current,
            )
            self._current_month = current
            self._month_cost = 0.0
            self._month_requests = 0
            self._loaded = False

    async def load(self, db: AsyncSession) -> None:
        """Load current month totals from SQLite."""
        self._check_month_rollover()
        month = self._current_month

        result = await db.execute(
            select(ApiUsage).where(ApiUsage.month == month)
        )
        row = result.scalar_one_or_none()
        if row:
            self._month_cost = row.cost or 0.0
            self._month_requests = row.request_count or 0
        else:
            self._month_cost = 0.0
            self._month_requests = 0
        self._loaded = True
        logger.info(
            "CostTracker loaded: month=%s cost=$%.4f requests=%d",
            month, self._month_cost, self._month_requests,
        )

    async def record_usage(
        self, input_tokens: int, output_tokens: int, db: AsyncSession
    ) -> None:
        """Calculate cost, update in-memory totals, and persist to SQLite."""
        self._check_month_rollover()
        month = self._current_month

        cost = (
            input_tokens * self.HAIKU_INPUT_RATE
            + output_tokens * self.HAIKU_OUTPUT_RATE
        )

        self._month_cost += cost
        self._month_requests += 1

        # Upsert into SQLite
        result = await db.execute(
            select(ApiUsage).where(ApiUsage.month == month)
        )
        row = result.scalar_one_or_none()
        if row:
            row.input_tokens = (row.input_tokens or 0) + input_tokens
            row.output_tokens = (row.output_tokens or 0) + output_tokens
            row.cost = self._month_cost
            row.request_count = self._month_requests
        else:
            row = ApiUsage(
                month=month,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                request_count=1,
            )
            db.add(row)

        await db.commit()
        logger.debug(
            "Recorded API usage: +%d in / +%d out = $%.6f (month total: $%.4f)",
            input_tokens, output_tokens, cost, self._month_cost,
        )

    def budget_exceeded(self) -> bool:
        """Check if monthly budget cap has been reached."""
        self._check_month_rollover()
        return self._month_cost >= settings.api_budget_monthly

    def budget_warning(self) -> bool:
        """Check if monthly budget is at 80% or above (soft warning)."""
        self._check_month_rollover()
        return self._month_cost >= settings.api_budget_monthly * 0.8

    def get_usage(self) -> dict:
        """Return current month usage summary."""
        self._check_month_rollover()
        return {
            "month": self._current_month,
            "cost": round(self._month_cost, 4),
            "requests": self._month_requests,
            "budget": settings.api_budget_monthly,
            "exceeded": self.budget_exceeded(),
            "warning": self.budget_warning(),
        }
