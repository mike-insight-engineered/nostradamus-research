"""Provider-independent completion interface with retries and rate limiting."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from ...config import PricingConfig
from ...models.translation import TokenUsage
from ...utils.hashing import sha256_text
from ...utils.redaction import redact

log = logging.getLogger("nostradamus_research.providers")


@dataclass(frozen=True)
class ProviderRequest:
    task: str
    system: str
    user: str
    template_id: str
    template_version: str
    max_tokens: int
    temperature: float | None = None
    # Structured inputs. Real providers ignore this (they only see the prompt);
    # the mock provider uses it to produce deterministic structured output.
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def prompt_sha256(self) -> str:
        return sha256_text(f"{self.system}\n\n{self.user}")


@dataclass
class ProviderResponse:
    text: str
    provider: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    response_id: str | None = None
    stop_reason: str | None = None
    attempts: int = 1


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False, retry_after: float | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after


class RateLimitError(ProviderError):
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message, retryable=True, retry_after=retry_after)


class ProviderConfigurationError(ProviderError):
    """Misconfiguration (missing key, SDK not installed, disabled provider)."""


@dataclass
class RetryPolicy:
    max_retries: int = 4
    initial_backoff: float = 2.0
    max_backoff: float = 60.0

    def delay(self, attempt: int, retry_after: float | None) -> float:
        if retry_after is not None:
            return min(retry_after, self.max_backoff)
        return min(self.initial_backoff * (2 ** (attempt - 1)), self.max_backoff)


class TranslationProvider(ABC):
    """Base class: subclasses implement :meth:`_send` for one attempt."""

    name: str = "base"
    is_paid: bool = True

    def __init__(
        self,
        model: str,
        *,
        retry: RetryPolicy | None = None,
        requests_per_minute: float | None = None,
        pricing: PricingConfig | None = None,
        log_prompts: bool = False,
        log_responses: bool = False,
        secrets: tuple[str, ...] = (),
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.model = model
        self.retry = retry or RetryPolicy()
        self.min_interval = 60.0 / requests_per_minute if requests_per_minute else 0.0
        self.pricing = pricing or PricingConfig()
        self.log_prompts = log_prompts
        self.log_responses = log_responses
        self._secrets = secrets
        self._sleep = sleep
        self._clock = clock
        self._last_request: float | None = None

    @abstractmethod
    def _send(self, request: ProviderRequest) -> ProviderResponse: ...

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name, "model": self.model, "is_paid": self.is_paid}

    def _throttle(self) -> None:
        if self.min_interval and self._last_request is not None:
            wait = self.min_interval - (self._clock() - self._last_request)
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        attempt = 0
        while True:
            attempt += 1
            self._throttle()
            self._log_request(request, attempt)
            try:
                response = self._send(request)
            except ProviderConfigurationError:
                raise
            except ProviderError as exc:
                if not exc.retryable or attempt > self.retry.max_retries:
                    log.warning("provider %s failed after %d attempt(s): %s", self.name, attempt,
                                redact(str(exc), self._secrets))  # fmt: skip
                    raise
                delay = self.retry.delay(attempt, exc.retry_after)
                log.info("provider %s retryable error (attempt %d), sleeping %.1fs: %s", self.name,
                         attempt, delay, redact(str(exc), self._secrets))  # fmt: skip
                self._sleep(delay)
                continue
            response.attempts = attempt
            self._log_response(response)
            return response

    def cost(self, usage: TokenUsage) -> tuple[float | None, str | None]:
        p = self.pricing
        if p.input_usd_per_million_tokens is None or p.output_usd_per_million_tokens is None:
            return None, "pricing not configured"
        if usage.input_tokens is None or usage.output_tokens is None:
            return None, "provider did not report token usage"
        return (
            usage.input_tokens * p.input_usd_per_million_tokens / 1e6
            + usage.output_tokens * p.output_usd_per_million_tokens / 1e6,
            "estimated from configured pricing",
        )

    # -- logging (secrets always redacted; prompt bodies only if opted in) -------
    def _log_request(self, request: ProviderRequest, attempt: int) -> None:
        body = (
            redact(request.user, self._secrets)
            if self.log_prompts
            else f"<{len(request.user)} chars sha256={request.prompt_sha256[:12]}>"
        )
        log.debug("request provider=%s model=%s task=%s template=%s@%s attempt=%d prompt=%s",
                  self.name, self.model, request.task, request.template_id,
                  request.template_version, attempt, body)  # fmt: skip

    def _log_response(self, response: ProviderResponse) -> None:
        body = (
            redact(response.text, self._secrets)
            if self.log_responses
            else f"<{len(response.text)} chars sha256={sha256_text(response.text)[:12]}>"
        )
        log.debug("response provider=%s model=%s usage=%s stop=%s body=%s", self.name,
                  response.model, response.usage.model_dump(), response.stop_reason, body)  # fmt: skip
