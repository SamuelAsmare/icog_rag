from __future__ import annotations

from typing import Any

from google import genai

from app.core.config import settings


class GeminiService:
    def __init__(self) -> None:
        self.client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if settings.GEMINI_API_KEY:
            if self.client is None:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            return self.client
        raise ValueError("GEMINI_API_KEY is not configured.")

    def build_prompt(self, question: str, context: list[dict[str, Any]]) -> str:
        if not context:
            raise ValueError("No relevant university context was found for this question.")

        context_text = "\n\n".join(
            (
                f"Source {index}: {item.get('filename', 'unknown.pdf')} "
                f"(Page {item.get('page_number', 'unknown')}): {item.get('text', '').strip()}"
            )
            for index, item in enumerate(context, start=1)
        )

        return (
            "You are answering a university question using only the provided document context. "
            "Answer based strictly on the retrieved university information and do not invent "
            "policies, deadlines, requirements, or procedures that are not present in the supplied context. "
            "If the retrieved information does not answer the question, say so clearly and explain that the context is insufficient. "
            "Use clear and understandable language. Do not treat unrelated information as university policy.\n\n"
            f"Question: {question}\n\n"
            f"Retrieved university context:\n{context_text}"
        )

    def generate_answer(self, question: str, context: list[dict[str, Any]]) -> str:
        client = self._get_client()
        prompt = self.build_prompt(question, context)

        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
        except Exception as exc:  # pragma: no cover - covered by API error handling
            raise RuntimeError("Gemini API request failed while generating the answer.") from exc

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
