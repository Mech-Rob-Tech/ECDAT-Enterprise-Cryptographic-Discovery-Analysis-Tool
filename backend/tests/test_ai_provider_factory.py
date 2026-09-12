import pytest

import ai.providers.factory as factory

from ai.providers.base import (
    AIProviderConfigurationError,
)


class FakeGroqProvider:
    provider_name = "groq"
    model_name = "fake-model"


def test_factory_defaults_to_groq(
    monkeypatch,
):
    monkeypatch.delenv(
        "ECDAT_AI_PROVIDER",
        raising=False,
    )

    monkeypatch.setattr(
        factory,
        "GroqProvider",
        FakeGroqProvider,
    )

    provider = (
        factory.create_ai_provider()
    )

    assert (
        provider.provider_name
        == "groq"
    )


def test_factory_uses_environment_provider(
    monkeypatch,
):
    monkeypatch.setenv(
        "ECDAT_AI_PROVIDER",
        "groq",
    )

    monkeypatch.setattr(
        factory,
        "GroqProvider",
        FakeGroqProvider,
    )

    provider = (
        factory.create_ai_provider()
    )

    assert (
        provider.model_name
        == "fake-model"
    )


def test_factory_normalizes_provider_name(
    monkeypatch,
):
    monkeypatch.setattr(
        factory,
        "GroqProvider",
        FakeGroqProvider,
    )

    provider = (
        factory.create_ai_provider(
            "  GROQ  "
        )
    )

    assert (
        provider.provider_name
        == "groq"
    )


def test_factory_rejects_unknown_provider():
    with pytest.raises(
        AIProviderConfigurationError,
        match="Unsupported",
    ):
        factory.create_ai_provider(
            "definitely-not-real"
        )