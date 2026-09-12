from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


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
        """Human-readable provider identifier."""
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

        Implementations should return a dictionary.

        Provider-specific networking, authentication,
        rate limits and response parsing belong here.
        """
        raise NotImplementedError