from __future__ import annotations

from contextlib import contextmanager
import contextvars
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.outputs import ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


class CostTracker:
    """Tracks token usage and estimated dollar costs for each LLM call."""

    _DEFAULT_SECTION = "unassigned"

    def __init__(
        self,
        pricing_config: Optional[Dict[str, Dict[str, float]]] = None,
        currency: str = "USD",
    ) -> None:
        self.pricing_config = pricing_config or {}
        self.currency = currency
        self._section_var: contextvars.ContextVar[str] = contextvars.ContextVar(
            "cost_tracker_section", default=self._DEFAULT_SECTION
        )
        self.reset()

    def reset(self) -> None:
        self._model_stats: Dict[str, Dict[str, Any]] = {}
        self._section_stats: Dict[str, Dict[str, Any]] = {}
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_calls = 0

    @contextmanager
    def section(self, section_name: str):
        """Context manager used to attribute downstream LLM calls to a pipeline section."""
        token = self._section_var.set(section_name or self._DEFAULT_SECTION)
        try:
            yield
        finally:
            self._section_var.reset(token)

    def wrap_section(
        self, section_name: str, fn: Callable[..., Dict[str, Any]]
    ) -> Callable[..., Dict[str, Any]]:
        """Wrap a graph node so every LLM call is attributed to a named section."""

        def wrapped(*args: Any, **kwargs: Any):
            with self.section(section_name):
                return fn(*args, **kwargs)

        return wrapped

    def record_usage(
        self,
        model_name: str,
        *,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> None:
        """Record the usage for a single model invocation."""
        if input_tokens is None and output_tokens is None:
            return

        input_tokens = int(input_tokens or 0)
        output_tokens = int(output_tokens or 0)

        cost = self._calculate_cost(model_name, input_tokens, output_tokens)
        section = self._section_var.get()

        model_stats = self._model_stats.setdefault(
            model_name,
            {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0},
        )
        model_stats["calls"] += 1
        model_stats["input_tokens"] += input_tokens
        model_stats["output_tokens"] += output_tokens
        model_stats["cost"] += cost

        section_stats = self._section_stats.setdefault(
            section,
            {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0},
        )
        section_stats["calls"] += 1
        section_stats["input_tokens"] += input_tokens
        section_stats["output_tokens"] += output_tokens
        section_stats["cost"] += cost

        self._total_cost += cost
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_calls += 1

    def summary(self) -> Dict[str, Any]:
        """Return a copy of the aggregated statistics."""
        return {
            "currency": self.currency,
            "total_cost": self._total_cost,
            "total_calls": self._total_calls,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "models": deepcopy(self._model_stats),
            "sections": deepcopy(self._section_stats),
        }

    def _calculate_cost(
        self, model_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        pricing = self.pricing_config.get(model_name, {})
        input_rate = pricing.get("input_cost_per_1k_tokens", 0.0)
        output_rate = pricing.get("output_cost_per_1k_tokens", 0.0)

        return (input_tokens / 1000.0) * input_rate + (
            output_tokens / 1000.0
        ) * output_rate


class CostTrackingMixin:
    """Mixin that records token usage from LangChain chat models."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._cost_tracker: Optional[CostTracker] = kwargs.pop("cost_tracker", None)
        super().__init__(*args, **kwargs)

    def _generate(self, *args: Any, **kwargs: Any) -> ChatResult:  # type: ignore[override]
        result = super()._generate(*args, **kwargs)
        self._record_costs(result)
        return result

    async def _agenerate(self, *args: Any, **kwargs: Any) -> ChatResult:  # type: ignore[override]
        result = await super()._agenerate(*args, **kwargs)
        self._record_costs(result)
        return result

    def _record_costs(self, result: ChatResult) -> None:
        if not self._cost_tracker or not result:
            return

        usage = self._extract_usage(result)
        if usage is None:
            return

        self._cost_tracker.record_usage(
            model_name=usage["model_name"],
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
        )

    def _extract_usage(self, result: ChatResult) -> Optional[Dict[str, Any]]:
        model_name = self._resolve_model_name(result)
        llm_output = result.llm_output or {}
        token_usage = self._ensure_dict(llm_output.get("token_usage") or {})

        input_tokens = self._coerce_token_value(
            token_usage, ["input_tokens", "prompt_tokens"]
        )
        output_tokens = self._coerce_token_value(
            token_usage, ["output_tokens", "completion_tokens"]
        )

        if input_tokens is None or output_tokens is None:
            for generation in result.generations:
                message_usage = getattr(generation.message, "usage_metadata", None)
                if not message_usage:
                    continue
                input_tokens = input_tokens or message_usage.get("input_tokens")
                output_tokens = output_tokens or message_usage.get("output_tokens")
                if input_tokens is not None and output_tokens is not None:
                    break

        if input_tokens is None:
            input_tokens = 0
        if output_tokens is None:
            output_tokens = 0

        if input_tokens == 0 and output_tokens == 0:
            return None

        return {
            "model_name": model_name,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
        }

    def _resolve_model_name(self, result: ChatResult) -> str:
        llm_output = result.llm_output or {}
        model_name = llm_output.get("model_name")
        if model_name:
            return model_name
        return getattr(self, "model_name", getattr(self, "model", "unknown-model"))

    def _ensure_dict(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        return {}

    @staticmethod
    def _coerce_token_value(payload: Dict[str, Any], keys: list[str]) -> Optional[int]:
        for key in keys:
            value = payload.get(key)
            if value is not None:
                return int(value)
        return None


class CostTrackingChatOpenAI(CostTrackingMixin, ChatOpenAI):
    """ChatOpenAI wrapper that reports token usage."""


class CostTrackingChatAnthropic(CostTrackingMixin, ChatAnthropic):
    """ChatAnthropic wrapper that reports token usage."""


class CostTrackingChatGoogle(CostTrackingMixin, ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI wrapper that reports token usage."""
