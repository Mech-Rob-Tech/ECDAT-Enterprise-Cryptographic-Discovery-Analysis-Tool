from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIProviderError(RuntimeError):
    """
    Base exception for failures in an AI provider.
    """


class AIProviderConfigurationError(AIProviderError):
    """
    Raised when a provider is incorrectly configured.
    """


class AIProviderResponseError(AIProviderError):
    """
    Raised when a provider returns an unusable response.
    """


class AIProvider(ABC):
    """
    Provider-independent interface for ECDAT AI.

    Provider implementations may use Groq, Gemini,
    local inference, or another compatible service.

    Providers generate language.
    They do not own ECDAT analytical decisions.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Human-readable provider identifier.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Model identifier used by the provider.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured response.

        Implementations must return a dictionary.

        Provider-specific networking, authentication,
        rate limits and response parsing belong here.

        Implementations must raise AIProviderError or
        one of its subclasses when provider output cannot
        be safely consumed by ECDAT.
        """
        raise NotImplementedError