"""LLM abstraction layer for AI-powered recommendations."""

from abc import ABC, abstractmethod
from typing import Optional

from app.core.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a completion from the LLM.

        Args:
            system_prompt: The system/context prompt.
            user_prompt: The user's message.

        Returns:
            The LLM's response text.
        """
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._client: Optional["anthropic.AsyncAnthropic"] = None

    @property
    def client(self) -> "anthropic.AsyncAnthropic":
        if self._client is None:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client: Optional["openai.AsyncOpenAI"] = None

    @property
    def client(self) -> "openai.AsyncOpenAI":
        if self._client is None:
            import openai

            self._client = openai.AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider.

    Returns:
        An LLM provider instance based on settings.

    Raises:
        ValueError: If no API key is configured for the selected provider.
    """
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
        )
    elif settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


# Singleton instance
llm_provider: Optional[LLMProvider] = None


def get_llm() -> LLMProvider:
    """Get or create the LLM provider singleton."""
    global llm_provider
    if llm_provider is None:
        llm_provider = get_llm_provider()
    return llm_provider
