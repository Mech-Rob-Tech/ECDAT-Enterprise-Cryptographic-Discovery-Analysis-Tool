import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import groq
from dotenv import load_dotenv
from groq import Groq

from ai.providers.base import (
    AIProvider,
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderResponseError,
)


_BACKEND_DIR = Path(
    __file__
).resolve().parents[2]

_ENV_FILE = _BACKEND_DIR / ".env"

load_dotenv(
    dotenv_path=_ENV_FILE,
    override=False,
)


class GroqProvider(AIProvider):
    """
    Groq-backed ECDAT AI provider.

    This adapter is responsible only for:

    - provider configuration
    - sending prompts
    - enforcing structured model output
    - converting provider failures into ECDAT
      provider exceptions

    It does not perform ECDAT grounding or make
    cryptographic decisions.
    """

    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        self._model = (
            model
            or os.getenv("ECDAT_AI_MODEL")
            or self.DEFAULT_MODEL
        ).strip()

        if not self._model:
            raise AIProviderConfigurationError(
                "Groq model must not be empty."
            )

        # Client injection is intentionally supported
        # so provider behavior can be unit tested
        # without making network calls.
        if client is not None:
            self._client = client
            return

        resolved_api_key = (
            api_key
            or os.getenv("GROQ_API_KEY")
            or ""
        ).strip()

        if not resolved_api_key:
            raise AIProviderConfigurationError(
                "GROQ_API_KEY is not configured."
            )

        try:
            self._client = Groq(
                api_key=resolved_api_key,
                timeout=timeout,
                max_retries=max_retries,
            )

        except Exception as exc:
            raise AIProviderConfigurationError(
                "Unable to initialize Groq client."
            ) from exc

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model

    def _build_response_format(
        self,
        response_schema: Optional[
            Dict[str, Any]
        ],
    ) -> Dict[str, Any]:
        """
        Build the Groq structured-output request.

        When an ECDAT response schema is available,
        strict JSON Schema mode is used.

        Otherwise JSON-object mode is used as a
        defensive fallback.
        """

        if response_schema is None:
            return {
                "type": "json_object",
            }

        if not isinstance(
            response_schema,
            dict,
        ):
            raise AIProviderConfigurationError(
                "response_schema must be a dictionary."
            )

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ecdat_ai_response",
                "strict": True,
                "schema": response_schema,
            },
        }

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
        Generate one structured ECDAT AI response.

        The returned dictionary is not automatically
        trusted. Higher layers must still parse it into
        AIResponse and enforce ECDAT evidence grounding.
        """

        if not str(system_prompt).strip():
            raise AIProviderConfigurationError(
                "System prompt must not be empty."
            )

        if not str(user_prompt).strip():
            raise AIProviderConfigurationError(
                "User prompt must not be empty."
            )

        response_format = (
            self._build_response_format(
                response_schema
            )
        )

        try:
            completion = (
                self._client
                .chat
                .completions
                .create(
                    model=self._model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        },
                    ],
                    response_format=response_format,
                    temperature=0,
                )
            )

        except groq.AuthenticationError as exc:
            raise AIProviderConfigurationError(
                "Groq authentication failed."
            ) from exc

        except groq.RateLimitError as exc:
            raise AIProviderError(
                "Groq rate limit reached."
            ) from exc

        except groq.APIConnectionError as exc:
            raise AIProviderError(
                "Unable to reach Groq API."
            ) from exc

        except groq.APIStatusError as exc:
            status_code = getattr(
                exc,
                "status_code",
                "unknown",
            )

            raise AIProviderError(
                "Groq API request failed with "
                f"status {status_code}."
            ) from exc

        except groq.APIError as exc:
            raise AIProviderError(
                "Groq API request failed."
            ) from exc

        try:
            message = (
                completion
                .choices[0]
                .message
            )

        except (
            AttributeError,
            IndexError,
            TypeError,
        ) as exc:
            raise AIProviderResponseError(
                "Groq returned no usable "
                "completion message."
            ) from exc

        refusal = getattr(
            message,
            "refusal",
            None,
        )

        if refusal:
            raise AIProviderResponseError(
                "Groq refused to generate the "
                "requested structured response."
            )

        content = getattr(
            message,
            "content",
            None,
        )

        if not isinstance(content, str):
            raise AIProviderResponseError(
                "Groq returned an empty or invalid "
                "response body."
            )

        content = content.strip()

        if not content:
            raise AIProviderResponseError(
                "Groq returned an empty response."
            )

        try:
            payload = json.loads(content)

        except json.JSONDecodeError as exc:
            raise AIProviderResponseError(
                "Groq returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise AIProviderResponseError(
                "Groq response must be a JSON object."
            )

        return payload