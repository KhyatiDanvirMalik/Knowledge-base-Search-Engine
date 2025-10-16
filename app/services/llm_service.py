import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured. Please set the environment variable.")
        genai.configure(api_key=api_key)
        # Fast, inexpensive; switch to "gemini-1.5-pro" if you prefer
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Initialized Gemini LLM service")

    def generate_answer(self, question: str, context_chunks: list) -> str:
        # Prepare concise context (top chunks)
        parts = []
        for i, c in enumerate(context_chunks[:5], 1):
            txt = c.get("text", "") or ""
            parts.append(f"Context {i} (chunk_index={c.get('metadata', {}).get('chunk_index', i-1)}):\n{txt}")
        context = "\n\n".join(parts) if parts else "No relevant context."
        prompt = (
            "You are a helpful assistant. Answer the question using ONLY the context below. "
            "If the context is insufficient, say you don't have enough information.\n\n"
            f"CONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nANSWER:"
        )
        try:
            resp = self.model.generate_content(prompt)
            return (resp.text or "").strip() if hasattr(resp, "text") else "No answer generated."
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Error generating response: {e}"
