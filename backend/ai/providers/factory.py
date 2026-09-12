import os
from typing import Optional

from ai.providers.base import (
    AIProvider,
    AIProviderConfigurationError,
)
from ai.providers.groq_provider import GroqProvider


DEFAULT_PROVIDER = "groq"


def create_ai_provider(
    provider_name: Optional[str] = None,
) -> AIProvider:
    """
    Create the configured ECDAT AI provider.

    Provider selection is intentionally centralized
    here so API and service layers remain
    provider-independent.
    """

    resolved_provider = (
        provider_name
        or os.getenv(
            "ECDAT_AI_PROVIDER",
            DEFAULT_PROVIDER,
        )
    )

    resolved_provider = (
        str(resolved_provider)
        .strip()
        .lower()
    )

    if not resolved_provider:
        resolved_provider = DEFAULT_PROVIDER

    if resolved_provider == "groq":
        return GroqProvider()

    raise AIProviderConfigurationError(
        "Unsupported ECDAT AI provider: "
        f"{resolved_provider}"
    )