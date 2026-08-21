import logging
import time
from fastapi import APIRouter
from config import settings
from schemas import QueryRequest, QueryResponse, SourceSnippet
from services.errors import AppError
from services.llm import answer_question
from services.vector import query_chunks
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/query", response_model=QueryResponse)
def query(body: QueryRequest) -> QueryResponse:
    started = time.perf_counter()
    top_k = body.top_k or settings.default_top_k
    try:
        hits = query_chunks(body.question, top_k)
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Vector query failed")
        raise AppError("Search failed", status_code=502, code="search_failed") from exc
    if not hits:
        logger.info(
            "Query with no hits",
            extra={"top_k": top_k, "latency_ms": round((time.perf_counter() - started) * 1000, 1)},
        )
        return QueryResponse(
            answer="I don't know from your saved notes. Ingest a note or URL first, or try a question closer to what you saved.",
            sources=[],
        )
    try:
        answer = answer_question(body.question, hits)
    except AppError:
        raise
    except Exception as exc:
        logger.exception("LLM call failed")
        raise AppError("Answer generation failed", status_code=502, code="llm_failed") from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    logger.info("Query completed", extra={"top_k": len(hits), "latency_ms": latency_ms})
    return QueryResponse(
        answer=answer,
        sources=[SourceSnippet(**hit) for hit in hits],
    )