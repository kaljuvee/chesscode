"""LLM Provider for XAI (Grok) integration."""
import os
from langchain_openai import ChatOpenAI


class LLMProvider:
    """Multi-provider LLM abstraction."""

    @staticmethod
    def get_model(model: str = None, provider: str = None, temperature: float = 0.7):
        """Get an LLM instance based on provider."""
        model = model or os.getenv("MODEL", "grok-4-fast-reasoning")
        provider = provider or os.getenv("MODEL_PROVIDER", "xai")

        if provider == "xai":
            api_key = os.getenv("XAI_API_KEY")
            if not api_key:
                raise ValueError("XAI_API_KEY environment variable is required")
            
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url="https://api.x.ai/v1",
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
