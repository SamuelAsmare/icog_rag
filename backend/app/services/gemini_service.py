from __future__ import annotations

import logging
from typing import Any

from google import genai

try:
    from groq import Groq
except Exception:  # pragma: no cover - dependency remains optional until installed
    Groq = None  # type: ignore[assignment]

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self) -> None:
        self.gemini_client: genai.Client | None = None
        self.groq_client: Any | None = None

    def _get_groq_client(self) -> Any:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured.")
        if Groq is None:
            raise RuntimeError("The Groq Python package is not installed.")
        if self.groq_client is None:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        return self.groq_client

    def _get_gemini_client(self) -> genai.Client:
        if settings.GEMINI_API_KEY:
            if self.gemini_client is None:
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            return self.gemini_client
        raise ValueError("GEMINI_API_KEY is not configured.")

    def build_prompt(self, question: str, context: list[dict[str, Any]]) -> str:
        if not context:
            raise ValueError("No relevant ICog context was found for this question.")

        context_text = "\n\n".join(
            (
                f"Source {index}: {item.get('filename', 'unknown.pdf')} "
                f"(Page {item.get('page_number', 'unknown')}): {item.get('text', '').strip()}"
            )
            for index, item in enumerate(context, start=1)
        )

        return (
            "You are answering an ICog question using only the provided document context. "
            "Answer based strictly on the retrieved information and do not invent facts, dates, policies, "
            "or procedures that are absent from the supplied context. If the retrieved information does not answer the question, "
            "say so clearly and explain that the context is insufficient. Use clear and understandable language.\n\n"
            f"Question: {question}\n\n"
            f"Retrieved ICog context:\n{context_text}"
        )

    def _generate_with_groq(self, prompt: str) -> str:
        client = self._get_groq_client()
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except Exception as exc:
            logger.exception("Groq API generation failed")
            raise RuntimeError(f"Groq API request failed: {exc}") from exc

        content = getattr(response.choices[0].message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()

        raise RuntimeError("Groq returned an empty response.")

    def _generate_with_gemini(self, prompt: str) -> str:
        client = self._get_gemini_client()
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
        except Exception as exc:
            logger.exception("Gemini API generation failed")
            raise RuntimeError(f"Gemini API request failed: {exc}") from exc

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            parts = getattr(candidate, "content", None)
            if parts and hasattr(parts, "parts"):
                text_parts = [part.text for part in parts.parts if getattr(part, "text", None)]
                if text_parts:
                    return "\n".join(text_parts).strip()

        raise RuntimeError("Gemini returned an empty response.")

    def generate_answer(self, question: str, context: list[dict[str, Any]]) -> str:
        prompt = self.build_prompt(question, context)

        if settings.GROQ_API_KEY:
            return self._generate_with_groq(prompt)

        if settings.GEMINI_API_KEY:
            return self._generate_with_gemini(prompt)

        raise ValueError("No LLM API key is configured. Set GROQ_API_KEY or GEMINI_API_KEY.")
