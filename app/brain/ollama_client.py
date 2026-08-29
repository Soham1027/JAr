import ollama

from app.config.settings import settings


class OllamaClient:

    def __init__(self):
        self.client = ollama.Client(
            host=settings.ollama_base_url
        )
        self.primary_model = settings.ollama_model
        self.fallback_model = settings.ollama_fallback_model
        self.active_model = self.primary_model

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:

        if self.active_model == self.fallback_model:
            return self._chat(self.fallback_model, messages, tools)

        try:
            return self._chat(self.primary_model, messages, tools)
        except Exception:
            return self._chat(self.fallback_model, messages, tools)

    def _chat(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:

        kwargs = {
            "model": model,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.chat(**kwargs)
        self.active_model = model
        return self._as_dict(response["message"])

    def _as_dict(self, message) -> dict:

        if isinstance(message, dict):
            return message

        if hasattr(message, "model_dump"):
            return message.model_dump(exclude_none=True)

        return {
            "role": getattr(message, "role", "assistant"),
            "content": getattr(message, "content", "") or "",
            "tool_calls": getattr(message, "tool_calls", None),
        }
