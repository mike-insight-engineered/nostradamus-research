"""OpenAI adapter (optional dependency: ``uv sync --extra openai``)."""

from __future__ import annotations

import os
from typing import Any

from ...models.translation import TokenUsage
from .base import (
    ProviderConfigurationError,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
    RateLimitError,
    TranslationProvider,
)


def _retry_after(exc: Any) -> float | None:
    try:
        value = exc.response.headers.get("retry-after")
        return float(value) if value is not None else None
    except (AttributeError, ValueError, TypeError):
        return None


class OpenAIProvider(TranslationProvider):
    name = "openai"
    is_paid = True

    def __init__(self, model: str, *, api_key_env: str, timeout: float = 120.0, **kwargs: Any):
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ProviderConfigurationError(
                f"environment variable {api_key_env} is not set; API keys are read only from the "
                "environment (see .env.example)"
            )
        try:
            import openai
        except ImportError as exc:
            raise ProviderConfigurationError(
                "the 'openai' package is not installed; run `uv sync --extra openai`"
            ) from exc
        super().__init__(model, secrets=(api_key,), **kwargs)
        self._sdk = openai
        self._client = openai.OpenAI(api_key=api_key, max_retries=0, timeout=timeout)

    def _send(self, request: ProviderRequest) -> ProviderResponse:
        sdk = self._sdk
        params: dict[str, Any] = {
            "model": self.model,
            "max_completion_tokens": request.max_tokens,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
        }
        if request.temperature is not None:
            params["temperature"] = request.temperature
        try:
            resp = self._client.chat.completions.create(**params)
        except sdk.RateLimitError as exc:
            raise RateLimitError(f"rate limited: {exc}", retry_after=_retry_after(exc)) from exc
        except (sdk.APITimeoutError, sdk.APIConnectionError) as exc:
            raise ProviderError(f"connection error: {exc}", retryable=True) from exc
        except sdk.APIStatusError as exc:
            retryable = getattr(exc, "status_code", 0) in (408, 409, 429, 500, 502, 503, 504)
            raise ProviderError(f"API error {getattr(exc, 'status_code', '?')}: {exc}",
                                retryable=retryable, retry_after=_retry_after(exc)) from exc  # fmt: skip
        choice = resp.choices[0] if resp.choices else None
        usage = getattr(resp, "usage", None)
        return ProviderResponse(
            text=(choice.message.content or "") if choice else "",
            provider=self.name,
            model=getattr(resp, "model", self.model),
            usage=TokenUsage(
                input_tokens=getattr(usage, "prompt_tokens", None),
                output_tokens=getattr(usage, "completion_tokens", None),
            ),
            response_id=getattr(resp, "id", None),
            stop_reason=getattr(choice, "finish_reason", None) if choice else None,
        )
