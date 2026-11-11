from __future__ import annotations

import logging
from typing import Any

from google import genai

try:
    from groq import Groq
except Exception:
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
            self.groq_client = Groq(
                api_key=settings.GROQ_API_KEY
            )

        return self.groq_client

    def _get_gemini_client(self) -> genai.Client:

        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        if self.gemini_client is None:
            self.gemini_client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

        return self.gemini_client

    def build_prompt(
        self,
        question: str,
        context: list[dict[str, Any]]
    ) -> str:

        if not context:
            raise ValueError(
                "No relevant ICog context was found for this question."
            )

        context_text = "\n\n".join(
            (
                f"Source {index}: "
                f"{item.get('filename', 'unknown.pdf')} "
                f"(Page {item.get('page_number', 'unknown')}): "
                f"{item.get('text', '').strip()}"
            )
            for index, item in enumerate(context, start=1)
        )

        return (
            "You are an AI assistant answering questions about ICog. "
            "Use ONLY the supplied document context to answer this question. "
            "Do not use outside knowledge or invent facts, dates, policies, "
            "or procedures. If the context does not contain enough information "
            "to answer the question, clearly say that the available documents "
            "do not provide sufficient information. "
            "Use clear and understandable language.\n\n"

            f"Question:\n{question}\n\n"

            f"Retrieved document context:\n{context_text}"
        )
        
    def build_general_prompt(self, question: str) -> str:

        return (
            "You are ICog AI Assistant, an AI assistant developed for "
            "the ICog RAG application. You are powered by an external "
            "LLM provider, but your identity in this application is "
            "ICog AI Assistant, not ChatGPT, Gemini, or Groq.\n\n"

            "IDENTITY RULES:\n"
            "- If someone asks who you are, introduce yourself as ICog AI Assistant.\n"
            "- Never identify yourself as ChatGPT, OpenAI, Gemini, or Groq.\n"
            "- If someone asks who developed you, explain that you are the "
            "ICog AI assistant and that your responses are powered by an LLM.\n"
            "- Do not claim to be a human.\n\n"

            "BEHAVIOR:\n"
            "- Answer general questions using your general knowledge.\n"
            "- Respond naturally to greetings and casual conversations.\n"
            "- Be friendly, helpful, accurate, and concise.\n"
            "- If you are uncertain, acknowledge it.\n"
            "- Do not claim that general answers come from uploaded documents.\n\n"

            f"User question:\n{question}\n\n"
            "Your response:"
        )

    def _generate_with_groq(self, prompt: str) -> str:

        client = self._get_groq_client()

        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
            )

        except Exception as exc:
            logger.exception("Groq API generation failed")
            raise RuntimeError(
                f"Groq API request failed: {exc}"
            ) from exc

        content = getattr(
            response.choices[0].message,
            "content",
            None
        )

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
            raise RuntimeError(
                f"Gemini API request failed: {exc}"
            ) from exc

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            parts = getattr(candidate, "content", None)

            if parts and hasattr(parts, "parts"):
                text_parts = [
                    part.text
                    for part in parts.parts
                    if getattr(part, "text", None)
                ]

                if text_parts:
                    return "\n".join(text_parts).strip()

        raise RuntimeError("Gemini returned an empty response.")


    def _generate_response(self, prompt: str) -> str:

        if settings.GROQ_API_KEY:
            return self._generate_with_groq(prompt)

        if settings.GEMINI_API_KEY:
            return self._generate_with_gemini(prompt)

        raise ValueError(
            "No LLM API key is configured. "
            "Set GROQ_API_KEY or GEMINI_API_KEY."
        )
    def generate_answer(
        self,
        question: str,
        context: list[dict[str, Any]]
    ) -> str:

        prompt = self.build_prompt(
            question,
            context
        )

        return self._generate_response(prompt)

    def generate_general_answer(
        self,
        question: str
    ) -> str:

        prompt = self.build_general_prompt(question)

        return self._generate_response(prompt)