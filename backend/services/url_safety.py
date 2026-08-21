import ipaddress
import socket
from urllib.parse import urlparse
from services.errors import AppError
_BLOCKED_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.google.com",
}

def assert_url_safe(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise AppError("URL must be http or https", status_code=400, code="validation_error")
    host = parsed.hostname.lower().rstrip(".")
    if host in _BLOCKED_HOSTS or host.endswith(".localhost"):
        raise AppError("URL host is not allowed", status_code=400, code="ssrf_blocked")
    if parsed.username or parsed.password:
        raise AppError("URLs with credentials are not allowed", status_code=400, code="ssrf_blocked")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        _reject_bad_ip(ip)
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise AppError("Could not resolve URL host", status_code=422, code="fetch_failed") from exc
    if not infos:
        raise AppError("Could not resolve URL host", status_code=422, code="fetch_failed")
    for info in infos:
        _reject_bad_ip(ipaddress.ip_address(info[4][0]))

def _reject_bad_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if ip.is_global:
        return
    raise AppError("URL host is not allowed", status_code=400, code="ssrf_blocked")