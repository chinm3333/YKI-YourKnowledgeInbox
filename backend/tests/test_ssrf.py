import ipaddress
import pytest
from services.errors import AppError
from services.url_safety import assert_url_safe

def test_rejects_localhost():
    with pytest.raises(AppError) as exc:
        assert_url_safe("http://localhost/notes")
    assert exc.value.status_code == 400
    assert exc.value.code == "ssrf_blocked"

def test_rejects_loopback_ip():
    with pytest.raises(AppError):
        assert_url_safe("http://127.0.0.1/secret")

def test_rejects_private_ip():
    with pytest.raises(AppError):
        assert_url_safe("http://192.168.1.10/admin")

def test_rejects_link_local():
    with pytest.raises(AppError):
        assert_url_safe("http://169.254.169.254/latest/meta-data")

def test_rejects_credentials_in_url():
    with pytest.raises(AppError):
        assert_url_safe("https://user:pass@example.com/path")

def test_allows_public_hostname(monkeypatch):
    monkeypatch.setattr(
        "services.url_safety.socket.getaddrinfo",
        lambda host, port: [
            (None, None, None, None, ("93.184.216.34", 0)),
        ],
    )
    assert ipaddress.ip_address("93.184.216.34").is_global
    assert_url_safe("https://example.com/article")