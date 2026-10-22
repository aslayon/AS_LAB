import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.domain import initial_state
from app.ollama_provider import OllamaProvider
from app.settings import Settings


def valid_response(request):
    payload = json.loads(request.content)
    if payload['format'].get('title') == 'DialogueReview':
        return {"model": payload["model"], "done": True, "message": {"role": "assistant", "content": json.dumps({"consistent": True, "issues": []})}}
    proposal = {key: field["const"] for key, field in payload["format"]["properties"].items() if "const" in field}
    current = payload["messages"][-1]["content"]
    proposal["dialogue"] = "현재 발언에 대한 대사: " + current[:80]
    return {"model": payload["model"], "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(proposal)},
            "total_duration": 1000000000, "load_duration": 100000000, "eval_count": 50}


def test_settings_select_mock_and_ollama(tmp_path, monkeypatch):
    monkeypatch.delenv("CHARACTER_CHAT_PROVIDER", raising=False)
    with TestClient(create_app(tmp_path / "mock.sqlite3")) as client:
        assert client.get("/api/health").json() == {"status": "ok", "provider": "MockProvider", "model": None}
    monkeypatch.setenv("CHARACTER_CHAT_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:4b-instruct-2507-q4_K_M")
    with TestClient(create_app(tmp_path / "ollama.sqlite3")) as client:
        assert client.get("/api/health").json()["model"] == "qwen3:4b-instruct-2507-q4_K_M"
    monkeypatch.setenv("CHARACTER_CHAT_PROVIDER", "typo")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_structured_call_success_and_metrics_not_persisted(tmp_path):
    seen = []
    def handle(request):
        payload = json.loads(request.content)
        seen.append(payload)
        assert str(request.url) == "http://127.0.0.1:11434/api/chat"
        assert payload["stream"] is False
        assert payload["think"] is False
        if payload["format"].get("title") != "DialogueReview":
            assert payload["format"]["properties"]["outcome"]["const"] == "warning"
        return httpx.Response(200, json=valid_response(request))
    provider = OllamaProvider(Settings(provider="ollama"), transport=httpx.MockTransport(handle))
    with TestClient(create_app(tmp_path / "success.sqlite3", provider=provider)) as client:
        branch = client.post("/api/games").json()
        result = client.post(f"/api/branches/{branch['id']}/chat", json={"text": "접근한다", "action": "force_access", "revision": 0})
        assert result.status_code == 200
        after = result.json()
        assert after["state"]["trust"] == 15
        assert after["state"]["guard"] == 45
        assert after["generation"]["model"] == "exaone3.5:7.8b-instruct-q4_K_M"
        assert after["generation"]["elapsed_ms"] >= 0
        stored = client.get(f"/api/branches/{branch['id']}").json()
        assert stored["state"] == after["state"]
        assert "generation" not in stored
        assert len(seen) == 2


@pytest.mark.parametrize("failure", ["connect", "timeout", "http404", "http500", "outer_json", "inner_json", "shape", "duplicate", "wrong_verdict", "extra", "incomplete", "length", "oversize", "blank"])
def test_ollama_failures_do_not_save_turn_or_checkpoint(tmp_path, failure):
    def handle(request):
        if failure == "connect": raise httpx.ConnectError("private detail", request=request)
        if failure == "timeout": raise httpx.ReadTimeout("private detail", request=request)
        if failure.startswith("http"): return httpx.Response(int(failure[4:]), text="private detail")
        if failure == "outer_json": return httpx.Response(200, text="private detail")
        if failure == "oversize": return httpx.Response(200, content=b"x" * 131073)
        body = valid_response(request)
        value = json.loads(body["message"]["content"])
        if failure == "inner_json": body["message"]["content"] = "private detail"
        if failure == "duplicate": body["message"]["content"] = '{"dialogue":"a","dialogue":"b"}'
        if failure == "shape": body["message"] = []
        if failure == "wrong_verdict": value["trust_delta"] = 5
        if failure == "extra": value["config"] = "rewrite"
        if failure == "blank": value["dialogue"] = " "
        if failure in ("wrong_verdict", "extra", "blank"): body["message"]["content"] = json.dumps(value)
        if failure == "incomplete": body["done"] = False
        if failure == "length": body["done_reason"] = "length"
        return httpx.Response(200, json=body)
    provider = OllamaProvider(Settings(provider="ollama"), transport=httpx.MockTransport(handle))
    with TestClient(create_app(tmp_path / "failure.sqlite3", provider=provider)) as client:
        branch = client.post("/api/games").json()
        result = client.post(f"/api/branches/{branch['id']}/chat", json={"text": "hello", "revision": 0})
        assert result.status_code == 502
        assert "private detail" not in result.text
        assert client.get(f"/api/branches/{branch['id']}").json() == branch
        assert client.get(f"/api/branches/{branch['id']}/checkpoints").json() == []


def test_ollama_context_after_restore_excludes_future_and_links(tmp_path):
    seen = []
    def handle(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=valid_response(request))
    provider = OllamaProvider(Settings(provider="ollama"), transport=httpx.MockTransport(handle))
    with TestClient(create_app(tmp_path / "context.sqlite3", provider=provider)) as client:
        branch = client.post("/api/games").json()
        base = f"/api/branches/{branch['id']}"
        first = client.post(base + "/chat", json={"text": "과거", "revision": 0}).json()
        future = client.post(base + "/chat", json={"text": "FUTURE_SECRET_42", "action": "force_access", "revision": 1}).json()
        restored = client.post(base + "/regress", json={"turn_number": 1, "revision": 2}).json()
        assert restored["state"] == first["state"]
        response = client.post(f"/api/branches/{restored['id']}/chat", json={"text": "new", "revision": 0})
        assert response.status_code == 200
        payload = json.dumps(seen[-1], ensure_ascii=False)
        assert "FUTURE_SECRET_42" not in payload
        assert "checkpoint_id" not in payload
        assert future["state"]["messages"][-2]["checkpoint_id"] not in payload


def test_context_budget_rejects_without_request(tmp_path):
    def handle(request):
        raise AssertionError("must not call Ollama")
    provider = OllamaProvider(Settings(provider="ollama", num_ctx=2048), transport=httpx.MockTransport(handle))
    with TestClient(create_app(tmp_path / "budget.sqlite3", provider=provider)) as client:
        branch = client.post("/api/games").json()
        result = client.post(f"/api/branches/{branch['id']}/chat", json={"text": "가" * 2000, "revision": 0})
        assert result.status_code == 502
        assert "문맥 예산" in result.json()["detail"]
        assert client.get(f"/api/branches/{branch['id']}").json() == branch
        assert client.get(f"/api/branches/{branch['id']}/checkpoints").json() == []


@pytest.mark.parametrize("kind", ["exact", "near", "whitespace"])
def test_valid_repeated_dialogue_commits_without_retry(tmp_path, kind):
    seen = []
    dialogue = initial_state()["messages"][0]["content"]
    if kind == "near":
        dialogue = dialogue.replace("저는", "전")
    if kind == "whitespace":
        dialogue = "\n " + dialogue + "  "
    def handle(request):
        seen.append(json.loads(request.content))
        body = valid_response(request)
        if seen[-1]["format"].get("title") == "DialogueReview":
            return httpx.Response(200, json=body)
        value = json.loads(body["message"]["content"])
        value["dialogue"] = dialogue
        body["message"]["content"] = json.dumps(value)
        return httpx.Response(200, json=body)
    provider = OllamaProvider(Settings(provider="ollama"), transport=httpx.MockTransport(handle))
    with TestClient(create_app(tmp_path / "repeat.sqlite3", provider=provider)) as client:
        branch = client.post("/api/games").json()
        for revision in range(2):
            response = client.post(f"/api/branches/{branch['id']}/chat", json={"text": "안녕", "revision": revision})
            assert response.status_code == 200
            after = response.json()
            assert after["generation"]["attempts"] == 1
            assert after["revision"] == revision + 1
            assert after["state"]["messages"][-1]["content"] == dialogue
            assert len(after["state"]["messages"]) == 3 + revision * 2
        assert len(seen) == 4
        assert len(client.get(f"/api/branches/{branch['id']}/checkpoints").json()) == 2
        assert [m["role"] for m in seen[0]["messages"]] == ["system", "user"]
        assert '"안녕"' in seen[0]["messages"][-1]["content"]
        assert all(sum(m["role"] == "system" for m in payload["messages"]) == 1 for payload in seen)
