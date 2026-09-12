import json
from types import SimpleNamespace

import groq
import pytest

from ai.prompts import AI_RESPONSE_JSON_SCHEMA
from ai.providers.base import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderResponseError,
)
from ai.providers.groq_provider import GroqProvider


class FakeCompletions:
    def __init__(
        self,
        *,
        content=None,
        refusal=None,
        exception=None,
    ):
        self.content = content
        self.refusal = refusal
        self.exception = exception
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        if self.exception is not None:
            raise self.exception

        message = SimpleNamespace(
            content=self.content,
            refusal=self.refusal,
        )

        choice = SimpleNamespace(
            message=message,
        )

        return SimpleNamespace(
            choices=[choice],
        )


class FakeClient:
    def __init__(
        self,
        *,
        content=None,
        refusal=None,
        exception=None,
    ):
        completions = FakeCompletions(
            content=content,
            refusal=refusal,
            exception=exception,
        )

        self.chat = SimpleNamespace(
            completions=completions,
        )


def build_valid_payload():
    return {
        "answer": "RSA usage was detected.",
        "confidence": "high",
        "evidence_refs": [
            {
                "reference_id": "artifact:rsa",
                "reference_type": "artifact",
                "source": None,
                "description": None,
            }
        ],
        "assumptions": [],
        "missing_context": [],
        "advisory_only": True,
    }


def test_provider_identity():
    provider = GroqProvider(
        client=FakeClient(),
    )

    assert provider.provider_name == "groq"

    assert (
        provider.model_name
        == "openai/gpt-oss-120b"
    )


def test_custom_model_is_preserved():
    provider = GroqProvider(
        client=FakeClient(),
        model="custom/test-model",
    )

    assert (
        provider.model_name
        == "custom/test-model"
    )


def test_structured_request_uses_json_schema():
    payload = build_valid_payload()

    client = FakeClient(
        content=json.dumps(payload)
    )

    provider = GroqProvider(
        client=client,
    )

    result = provider.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_schema=(
            AI_RESPONSE_JSON_SCHEMA
        ),
    )

    assert result == payload

    call = (
        client
        .chat
        .completions
        .calls[0]
    )

    assert (
        call["model"]
        == "openai/gpt-oss-120b"
    )

    assert call["temperature"] == 0

    assert (
        call["response_format"]["type"]
        == "json_schema"
    )

    json_schema = (
        call["response_format"][
            "json_schema"
        ]
    )

    assert (
        json_schema["strict"]
        is True
    )

    assert (
        json_schema["schema"]
        == AI_RESPONSE_JSON_SCHEMA
    )


def test_provider_uses_json_object_without_schema():
    payload = {
        "answer": "test",
    }

    client = FakeClient(
        content=json.dumps(payload)
    )

    provider = GroqProvider(
        client=client,
    )

    result = provider.generate_structured(
        system_prompt="system",
        user_prompt="user",
    )

    assert result == payload

    call = (
        client
        .chat
        .completions
        .calls[0]
    )

    assert call["response_format"] == {
        "type": "json_object",
    }


def test_empty_system_prompt_is_rejected():
    provider = GroqProvider(
        client=FakeClient()
    )

    with pytest.raises(
        AIProviderConfigurationError
    ):
        provider.generate_structured(
            system_prompt="   ",
            user_prompt="user",
        )


def test_empty_user_prompt_is_rejected():
    provider = GroqProvider(
        client=FakeClient()
    )

    with pytest.raises(
        AIProviderConfigurationError
    ):
        provider.generate_structured(
            system_prompt="system",
            user_prompt="   ",
        )


def test_invalid_schema_is_rejected():
    provider = GroqProvider(
        client=FakeClient()
    )

    with pytest.raises(
        AIProviderConfigurationError
    ):
        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_schema="invalid",
        )


def test_invalid_json_is_rejected():
    provider = GroqProvider(
        client=FakeClient(
            content="definitely not json"
        )
    )

    with pytest.raises(
        AIProviderResponseError
    ):
        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )


def test_non_object_json_is_rejected():
    provider = GroqProvider(
        client=FakeClient(
            content='["not", "object"]'
        )
    )

    with pytest.raises(
        AIProviderResponseError
    ):
        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )


def test_empty_response_is_rejected():
    provider = GroqProvider(
        client=FakeClient(
            content="   "
        )
    )

    with pytest.raises(
        AIProviderResponseError
    ):
        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )


def test_refusal_is_rejected():
    provider = GroqProvider(
        client=FakeClient(
            content=None,
            refusal="Request refused",
        )
    )

    with pytest.raises(
        AIProviderResponseError
    ):
        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )


def test_missing_api_key_is_rejected(
    monkeypatch,
):
    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    with pytest.raises(
        AIProviderConfigurationError
    ):
        GroqProvider(
            api_key=None,
            client=None,
        )


def test_rate_limit_becomes_provider_error(
    monkeypatch,
):
    class FakeRateLimitError(Exception):
        pass

    monkeypatch.setattr(
        groq,
        "RateLimitError",
        FakeRateLimitError,
    )

    client = FakeClient(
        exception=FakeRateLimitError(
            "rate limit"
        )
    )

    provider = GroqProvider(
        client=client,
    )

    with pytest.raises(
        AIProviderError,
        match="rate limit",
    ):
        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )