import logging
from groq import Groq, NotFoundError
from config import settings
from services.errors import AppError
logger = logging.getLogger(__name__)
SYSTEM_PROMPT = """You are a knowledge inbox assistant.
Answer the user's question using ONLY the numbered context chunks.
If the context is insufficient, say you do not know from the saved notes.
Cite sources inline like [1] or [1][2] when you use a chunk.
Do not invent URLs, titles, or facts that are not in the context.
Keep answers concise."""
_client: Groq | None = None

def _client_or_raise() -> Groq:
    global _client
    if not settings.groq_api_key:
        raise AppError("GROQ_API_KEY is not set", status_code=500, code="config_error")
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client

def answer_question(question: str, chunks: list[dict]) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        label = chunk.get("title") or chunk.get("source") or chunk.get("item_id")
        context_blocks.append(f"[{i}] ({chunk.get('type')}, {label})\n{chunk.get('snippet')}")
    user_prompt = (
        "Context:\n"
        + "\n\n".join(context_blocks)
        + "\n\nQuestion:\n"
        + question
    )
    try:
        response = _client_or_raise().chat.completions.create(
            model=settings.groq_model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    except NotFoundError as exc:
        raise AppError(
            f"Groq model '{settings.groq_model}' is not available. "
            "Set GROQ_MODEL in backend/.env to an active id "
            "(current Groq replacement for Llama 3.1 8B Instant: openai/gpt-oss-20b).",
            status_code=502,
            code="llm_model_not_found",
        ) from exc
    content = response.choices[0].message.content or ""
    logger.info("Groq completion ok", extra={"top_k": len(chunks)})
    return content.strip()