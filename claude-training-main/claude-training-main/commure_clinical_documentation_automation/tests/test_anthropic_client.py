from anthropic_client import resolve_client


def test_force_mock_returns_none():
    assert resolve_client(force_mock=True) is None


def test_no_credentials_returns_none(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    assert resolve_client() is None


def test_explicit_api_key_returns_live_client():
    client = resolve_client(api_key="sk-test-key")
    assert client is not None
    assert client.api_key == "sk-test-key"
