"""Generate concise summaries using an AI model (Google GenAI or OpenAI)."""
import os
import logging

from . import config

logger = logging.getLogger(__name__)


# this example uses the google-genai client, which was installed earlier
try:
    import google.genai as genai
except ImportError:  # fallback / stub
    genai = None


def summarize(text: str, max_tokens: int = 200) -> str:
    """Return a short summary for the given text."""
    if genai and config.OPENAI_API_KEY:
        try:
            client = genai.Client(api_key=config.OPENAI_API_KEY)
            response = client.models.generate_content(
                model="models/gemini-3-pro-preview",
                contents=f"Summarize the following article in 2-3 sentences:\n\n{text}"
            )
            return response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            logger.warning("AI summarization failed: %s", e)
    else:
        logger.warning("GenAI client unavailable; returning first 300 chars")
        return text[:300] + ("..." if len(text) > 300 else "")
