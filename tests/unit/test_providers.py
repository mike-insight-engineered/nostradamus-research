import json

import pytest

from nostradamus_research.config import PricingConfig, ProviderConfig, ProvidersConfig
from nostradamus_research.models.translation import TokenUsage
from nostradamus_research.translation.providers import (
    MockProvider,
    PaidCallNotAuthorisedError,
    ProviderConfigurationError,
    ProviderError,
    ProviderRequest,
    ProviderResponse,
    RateLimitError,
    RetryPolicy,
    TranslationProvider,
    build_provider,
)
from nostradamus_research.utils.redaction import REDACTED, contains_secret, redact


def _req(task="translate_direct", **md):
    return ProviderRequest(
        task=task,
        system="sys",
        user="user text",
        template_id="direct",
        template_version="1.0.0",
        max_tokens=100,
        metadata={"source_text": "Le clerc dict", "source_sha256": "abc", **md},
    )


class FlakyProvider(TranslationProvider):
    name = "flaky"

    def __init__(self, failures, **kw):
        super().__init__("flaky-model", **kw)
        self.failures = list(failures)
        self.attempts = 0

    def _send(self, request):
        self.attempts += 1
        if self.failures:
            raise self.failures.pop(0)
        return ProviderResponse(text="{}", provider=self.name, model=self.model)


def test_mock_is_deterministic_and_structured():
    a, b = MockProvider(seed=1), MockProvider(seed=1)
    ra, rb = a.complete(_req()), b.complete(_req())
    assert ra.text == rb.text
    payload = json.loads(ra.text)
    assert {"translation_fr", "translation_en", "self_reported_confidence"} <= set(payload)
    assert 0 <= payload["self_reported_confidence"] <= 1
    assert MockProvider(seed=2).complete(_req()).response_id != ra.response_id
    assert ra.usage.input_tokens and ra.usage.output_tokens
    assert a.is_paid is False


def test_mock_confidence_none_mode_and_unsupported_task():
    payload = json.loads(MockProvider(confidence_mode="none").complete(_req()).text)
    assert payload["self_reported_confidence"] is None
    with pytest.raises(ProviderError, match="does not support"):
        MockProvider().complete(_req(task="interpret_prophecy"))


def test_mock_oracle_only_used_for_matching_hash():
    oracle = {"abc": {"fr": "un deux trois quatre cinq", "en": "one two three four five"}}
    p = json.loads(MockProvider(oracle=oracle).complete(_req()).text)
    assert set(p["translation_en"].split()) <= {"one", "two", "three", "four", "five"}


def test_retry_then_success_uses_backoff():
    sleeps = []
    prov = FlakyProvider(
        [RateLimitError("slow down", retry_after=3), ProviderError("503", retryable=True)],
        retry=RetryPolicy(max_retries=3, initial_backoff=1, max_backoff=10),
        sleep=sleeps.append,
    )
    resp = prov.complete(_req())
    assert resp.attempts == 3 and sleeps == [3, 2]


def test_non_retryable_error_raises_immediately():
    prov = FlakyProvider([ProviderError("bad request", retryable=False)], sleep=lambda s: None)
    with pytest.raises(ProviderError, match="bad request"):
        prov.complete(_req())
    assert prov.attempts == 1


def test_retries_exhausted():
    prov = FlakyProvider(
        [ProviderError("x", retryable=True)] * 5,
        retry=RetryPolicy(max_retries=2),
        sleep=lambda s: None,
    )
    with pytest.raises(ProviderError):
        prov.complete(_req())
    assert prov.attempts == 3


def test_rate_limiter_spaces_requests():
    # call 1 records t=0.0; call 2 observes t=0.5 (0.5 s elapsed of a 1.0 s interval), then records t=1.0
    clock = iter([0.0, 0.5, 1.0])
    sleeps = []
    prov = FlakyProvider([], requests_per_minute=60, sleep=sleeps.append, clock=lambda: next(clock))
    prov.complete(_req())
    prov.complete(_req())
    assert sleeps and abs(sleeps[0] - 0.5) < 1e-9


def test_cost_requires_configured_pricing():
    prov = FlakyProvider([])
    assert prov.cost(TokenUsage(input_tokens=10, output_tokens=10)) == (
        None,
        "pricing not configured",
    )
    prov.pricing = PricingConfig(
        input_usd_per_million_tokens=2.0, output_usd_per_million_tokens=10.0
    )
    cost, _ = prov.cost(TokenUsage(input_tokens=1_000_000, output_tokens=100_000))
    assert cost == pytest.approx(3.0)
    assert prov.cost(TokenUsage())[0] is None


def _providers(enabled=False):
    return ProvidersConfig(
        providers={
            "mock": ProviderConfig(type="mock", model="m"),
            "anthropic": ProviderConfig(
                type="anthropic",
                model="some-model",
                api_key_env="ANTHROPIC_API_KEY",
                enabled=enabled,
            ),
            "openai": ProviderConfig(
                type="openai", model="REPLACE_WITH_X", api_key_env="OPENAI_API_KEY", enabled=True
            ),
        }
    )


def test_factory_guards_paid_calls(monkeypatch):
    assert isinstance(build_provider("mock", _providers()), MockProvider)
    with pytest.raises(PaidCallNotAuthorisedError, match="disabled"):
        build_provider("anthropic", _providers(enabled=False), allow_paid=True)
    with pytest.raises(PaidCallNotAuthorisedError, match="--allow-paid-api"):
        build_provider("anthropic", _providers(enabled=True), allow_paid=False)
    with pytest.raises(ProviderConfigurationError, match="ANTHROPIC_API_KEY"):
        build_provider("anthropic", _providers(enabled=True), allow_paid=True)
    with pytest.raises(ProviderConfigurationError, match="real model ID"):
        build_provider("openai", _providers(), allow_paid=True)
    with pytest.raises(ProviderConfigurationError, match="unknown provider"):
        build_provider("nope", _providers())


# Fake key-shaped strings are assembled at runtime so that no key-like literal appears in
# the source tree (the repository secret scan would, correctly, flag one).
FAKE_ANTHROPIC = "sk-" + "ant-api03-" + "X" * 16
FAKE_OPENAI = "sk-" + "proj-" + "y" * 21


def test_redaction():
    text = f'key {FAKE_ANTHROPIC} and {{"api_key": "s3cr3tvalue"}} Bearer abcdefghijklmnop123'
    out = redact(text, extra_secrets=["s3cr3tvalue"])
    assert (
        FAKE_ANTHROPIC not in out and "s3cr3tvalue" not in out and "abcdefghijklmnop123" not in out
    )
    assert REDACTED in out
    assert contains_secret(FAKE_OPENAI)
    assert not contains_secret("no secrets here")
