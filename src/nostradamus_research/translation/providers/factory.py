"""Construct providers from configuration, enforcing the paid-call guard.

A paid provider is only built when ALL of the following hold:

1. the provider entry in ``config/providers.yaml`` has ``enabled: true``;
2. the caller passes ``allow_paid=True`` (CLI: ``--allow-paid-api``);
3. the named API-key environment variable is set.
"""

from __future__ import annotations

from typing import Any

from ...config import ProvidersConfig
from .base import ProviderConfigurationError, RetryPolicy, TranslationProvider
from .mock import FixtureOracle, MockProvider


class PaidCallNotAuthorisedError(ProviderConfigurationError):
    pass


def build_provider(
    name: str,
    providers: ProvidersConfig,
    *,
    allow_paid: bool = False,
    oracle: FixtureOracle | None = None,
    model_override: str | None = None,
) -> TranslationProvider:
    if name not in providers.providers:
        raise ProviderConfigurationError(
            f"unknown provider {name!r}; configured: {sorted(providers.providers)}"
        )
    cfg = providers.providers[name]
    model = model_override or cfg.model
    common: dict[str, Any] = {
        "retry": RetryPolicy(cfg.max_retries, cfg.initial_backoff_seconds, cfg.max_backoff_seconds),
        "requests_per_minute": cfg.requests_per_minute,
        "pricing": cfg.pricing,
        "log_prompts": providers.logging.log_prompts,
        "log_responses": providers.logging.log_responses,
    }
    if cfg.type == "mock":
        return MockProvider(model, oracle=oracle, **common)

    if not cfg.enabled:
        raise PaidCallNotAuthorisedError(
            f"provider {name!r} is disabled. Copy config/providers.example.yaml to "
            "config/providers.yaml and set enabled: true to authorise paid calls."
        )
    if not allow_paid:
        raise PaidCallNotAuthorisedError(
            f"provider {name!r} makes paid API calls; re-run with --allow-paid-api to confirm"
        )
    if model.startswith("REPLACE_WITH"):
        raise ProviderConfigurationError(
            f"set a real model ID for provider {name!r} in providers.yaml"
        )
    assert cfg.api_key_env is not None  # enforced by ProviderConfig validation
    if cfg.type == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            model, api_key_env=cfg.api_key_env, timeout=cfg.timeout_seconds, **common
        )
    from .openai_provider import OpenAIProvider

    return OpenAIProvider(model, api_key_env=cfg.api_key_env, timeout=cfg.timeout_seconds, **common)
