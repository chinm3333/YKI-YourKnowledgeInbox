import logging
from urllib.parse import urljoin, urlparse
import httpx
import trafilatura
from config import settings
from services.errors import AppError
from services.url_safety import assert_url_safe
logger = logging.getLogger(__name__)
USER_AGENT = "KnowledgeInbox/1.0 (interview demo; content extract)"
MAX_REDIRECTS = 3

def fetch_url_text(url: str) -> tuple[str, str]:
    html, final_url = _download(url)
    extracted = trafilatura.extract(
        html,
        url=final_url,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not extracted or not extracted.strip():
        raise AppError(
            "Could not extract readable text from the page",
            status_code=422,
            code="extract_failed",
        )
    text = extracted.strip()
    if len(text) > settings.max_content_chars:
        text = text[: settings.max_content_chars]
    meta = trafilatura.extract_metadata(html)
    host = urlparse(final_url).netloc
    page_title = (meta.title if meta and meta.title else None) or host
    logger.info("Extracted URL content", extra={"source_type": "url"})
    return page_title[:200], text

def _download(url: str) -> tuple[str, str]:
    current = url
    with httpx.Client(
        follow_redirects=False,
        timeout=settings.url_timeout_seconds,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            assert_url_safe(current)
            try:
                response = client.get(current)
            except httpx.TimeoutException as exc:
                raise AppError("Timed out fetching URL", status_code=422, code="fetch_failed") from exc
            except httpx.RequestError as exc:
                raise AppError(f"Could not fetch URL: {exc}", status_code=422, code="fetch_failed") from exc
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise AppError("Redirect missing Location header", status_code=422, code="fetch_failed")
                current = urljoin(str(response.url), location)
                continue
            if response.status_code >= 400:
                raise AppError(
                    f"URL returned HTTP {response.status_code}",
                    status_code=422,
                    code="fetch_failed",
                )
            content_type = response.headers.get("content-type", "")
            if content_type and "html" not in content_type and "text/plain" not in content_type:
                raise AppError(
                    f"Unsupported content type: {content_type}",
                    status_code=422,
                    code="extract_failed",
                )
            raw = response.content[: settings.url_max_bytes]
            html = raw.decode(response.encoding or "utf-8", errors="replace")
            return html, str(response.url)
    raise AppError("Too many redirects", status_code=422, code="fetch_failed")