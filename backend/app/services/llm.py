"""LLM abstraction layer for AI-powered recommendations."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from app.core.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a completion from the LLM."""
        pass

    @abstractmethod
    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        """Stream a completion from the LLM, yielding text chunks."""
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

    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text


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

    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider."""
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
