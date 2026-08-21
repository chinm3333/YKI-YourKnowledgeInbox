import logging
import time
from uuid import uuid4
from fastapi import APIRouter
from config import settings
from schemas import IngestRequest, IngestResponse
from services.chunk import chunk_text
from services.errors import AppError
from services.extract import fetch_url_text
from services import store
from services.vector import delete_chunks, upsert_chunks
router = APIRouter()
logger = logging.getLogger(__name__)

def _title_from_note(text: str) -> str:
    first_line = text.split("\n", 1)[0].strip()
    return (first_line or "Untitled note")[:120]

@router.post("/ingest", response_model=IngestResponse, status_code=201)
def ingest(body: IngestRequest) -> IngestResponse:
    started = time.perf_counter()
    if body.type == "url":
        title, content = fetch_url_text(body.content)
        source = body.content
    else:
        content = body.content[: settings.max_content_chars]
        title = _title_from_note(content)
        source = None
    chunks = chunk_text(content, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise AppError(
            "Nothing to index after cleaning the content",
            status_code=422,
            code="extract_failed",
        )
    item_id = str(uuid4())
    try:
        chunk_count = upsert_chunks(
            item_id,
            chunks,
            {"title": title, "type": body.type, "source": source or ""},
        )
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Vector upsert failed", extra={"item_id": item_id})
        raise AppError(
            "Failed to index content",
            status_code=502,
            code="index_failed",
        ) from exc
    try:
        item = store.create_item(body.type, title, content, source, item_id=item_id)
    except Exception as exc:
        delete_chunks(item_id)
        logger.exception("SQLite insert failed after index", extra={"item_id": item_id})
        raise AppError(
            "Failed to save item",
            status_code=500,
            code="store_failed",
        ) from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    logger.info(
        "Ingested item",
        extra={
            "item_id": item["id"],
            "source_type": body.type,
            "chunk_count": chunk_count,
            "latency_ms": latency_ms,
        },
    )
    return IngestResponse(
        id=item["id"],
        type=item["type"],
        title=item["title"],
        source=item["source"],
        created_at=item["created_at"],
        chunk_count=chunk_count,
    )