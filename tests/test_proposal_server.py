from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import proposal_server  # noqa: E402
# Token d'API requis depuis app#13 (refus de démarrer sans auth >=32 chars).
API_TOKEN = "x" * 40
AUTH_HEADERS = {"content-type": "application/json", "authorization": f"Bearer {API_TOKEN}"}


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_server(tmp_path: Path):
    import os
    port = free_port()
    proc = subprocess.Popen(
        ["python3", "src/proposal_server.py", "--host", "127.0.0.1", "--port", str(port), "--data-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "OA_PROPOSALS_TOKEN": API_TOKEN},
    )
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.2).read()
            return proc, port
        except Exception:
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=1)
                raise AssertionError(f"server exited early\nOUT={out}\nERR={err}")
            time.sleep(0.05)
    proc.terminate()
    raise AssertionError("server did not become ready")


def request_json(method: str, url: str, payload: dict | None = None, headers: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=headers or {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=3) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_vault_secret_uses_only_scoped_omar_app_token(monkeypatch, tmp_path):
    calls = []

    def fake_check_output(cmd, text, stderr, env):
        calls.append({"cmd": cmd, "env": env})
        return json.dumps({"data": {"data": {"STRIPE_SECRET_KEY": "stripe-test-key"}}})

    monkeypatch.setenv("VAULT_TOKEN", "root-token-must-not-be-used")
    monkeypatch.setenv("OA_APP_VAULT_TOKEN", "scoped-omar-app-token")
    monkeypatch.setattr(proposal_server, "DEFAULT_VAULT_ADDR", "http://vault.local:8200")
    monkeypatch.setattr(proposal_server, "DEFAULT_VAULT_TOKEN_FILE", tmp_path / "missing-token")
    monkeypatch.setattr(proposal_server.subprocess, "check_output", fake_check_output)

    assert proposal_server._vault_secret("secret/stripe/test", "STRIPE_SECRET_KEY") == "stripe-test-key"
    assert len(calls) == 1
    assert calls[0]["cmd"] == ["/usr/bin/vault", "kv", "get", "-format=json", "secret/stripe/test"]
    assert calls[0]["env"]["VAULT_ADDR"] == "http://vault.local:8200"
    assert calls[0]["env"]["VAULT_TOKEN"] == "scoped-omar-app-token"


def test_vault_secret_ignores_inherited_root_token_without_service_token(monkeypatch, tmp_path):
    calls = []

    def fake_check_output(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("vault CLI must not be called without omar-app service token")

    monkeypatch.delenv("OA_APP_VAULT_TOKEN", raising=False)
    monkeypatch.setenv("VAULT_TOKEN", "root-token-must-not-be-used")
    monkeypatch.setattr(proposal_server, "DEFAULT_VAULT_TOKEN_FILE", tmp_path / "missing-token")
    monkeypatch.setattr(proposal_server.subprocess, "check_output", fake_check_output)

    assert proposal_server._vault_secret("secret/stripe/test", "STRIPE_SECRET_KEY") == ""
    assert calls == []


def test_vault_secret_rejects_unscoped_path_or_field(monkeypatch):
    calls = []

    def fake_check_output(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("vault CLI must not be called for unscoped secrets")

    monkeypatch.setenv("OA_APP_VAULT_TOKEN", "scoped-omar-app-token")
    monkeypatch.setattr(proposal_server.subprocess, "check_output", fake_check_output)

    assert proposal_server._vault_secret("secret/stripe/test", "UNRELATED_SECRET") == ""
    assert proposal_server._vault_secret("secret/other/service", "STRIPE_SECRET_KEY") == ""
    assert calls == []


def test_proposal_api_stores_pending_human_go_json_without_secrets(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {
            "type": "configuration_proposal",
            "status": "pending_human_go",
            "client_profile": {"company_name": "Client Démo", "contact_email": "client@example.com"},
            "hetzner_payload": {"mode": "dry_run_no_paid_resource", "create_server_payload": {"server_type": "cax21"}},
            "apps_l1": [{"slug": "hub"}],
            "safety": {"paid_actions": "none"},
        }
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/proposals", payload, AUTH_HEADERS)
        assert status == 201
        assert created["ok"] is True
        assert created["proposal"]["status"] == "pending_human_go"
        assert created["proposal"]["id"].startswith("proposal-")
        stored_path = tmp_path / "proposals" / f"{created['proposal']['id']}.json"
        assert stored_path.exists()
        stored_text = stored_path.read_text(encoding="utf-8")
        assert "client@example.com" in stored_text
        for forbidden in ["HCLOUD_TOKEN", "Authorization", "Bearer ", "sk-"]:
            assert forbidden not in stored_text

        get_status, fetched = request_json("GET", f"http://127.0.0.1:{port}/api/proposals/{created['proposal']['id']}", None, AUTH_HEADERS)
        assert get_status == 200
        assert fetched["proposal"]["hetzner_payload"]["create_server_payload"]["server_type"] == "cax21"
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_proposal_api_rejects_paid_or_invalid_payloads(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        bad = {
            "type": "configuration_proposal",
            "status": "approved",
            "safety": {"paid_actions": "POST /servers"},
            "hetzner_payload": {"mode": "live"},
        }
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/proposals",
            data=json.dumps(bad).encode("utf-8"),
            method="POST",
            headers=AUTH_HEADERS,
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("invalid payload accepted")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 422
            assert body["ok"] is False
            assert "pending_human_go" in body["error"] or "paid" in body["error"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_pricing_endpoint_is_read_only_and_reports_unconfigured_token(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        status, data = request_json("GET", f"http://127.0.0.1:{port}/api/hetzner/pricing")
        assert status == 200
        assert data["ok"] is True
        assert data["provider"] == "hetzner"
        assert data["mode"] in {"live_readonly", "static_fallback"}
        assert data["paid_actions"] == "none"
        assert {p["id"] for p in data["packs"]} >= {"starter", "pro", "max"}
    finally:
        proc.terminate()
        proc.wait(timeout=3)
