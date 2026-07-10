from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import audit_intelligence as ai  # noqa: E402
from audit_telemetry import append_telemetry_event  # noqa: E402


def _events(session: dict) -> list[dict]:
    return session["metrics"]["telemetry_events"]


def test_append_telemetry_event_rejects_free_text_and_pii():
    session = {"id": "audit-session-20260710T120000Z-12345678", "schema": "oa_audit_session.business_tech.v1"}
    event = {
        "event": "button_clicked",
        "step": "pacte",
        "action_id": "continue_without_account",
        "privacy": {"pii": False, "contains_free_text": False},
    }

    out = append_telemetry_event(session, event)

    assert _events(out)[0]["schema"] == "oa.audit.telemetry_event.v1"
    assert _events(out)[0]["privacy"] == {"pii": False, "contains_free_text": False, "retention": "product_analytics_90d"}
    assert "label" not in _events(out)[0]

    for unsafe in [
        {"event": "button_clicked", "privacy": {"pii": True, "contains_free_text": False}},
        {"event": "button_clicked", "privacy": {"pii": False, "contains_free_text": True}},
    ]:
        try:
            append_telemetry_event(session, unsafe)
            raise AssertionError("unsafe telemetry event accepted")
        except ValueError as exc:
            assert "PII/free-text" in str(exc)


def test_tester_events_have_zero_weight():
    session = {"id": "audit-session-20260710T120000Z-12345678", "runtime": {"tester": "alex"}}

    out = append_telemetry_event(session, {"event": "session_created", "privacy": {"pii": False, "contains_free_text": False}})

    event = _events(out)[0]
    assert event["is_tester"] is True
    assert event["telemetry_weight"] == 0.0


def test_business_tech_tester_session_events_have_zero_weight():
    session = ai.create_session({"tree_id": "business_tech", "runtime": {"tester": "alex"}})["session"]

    assert {event["telemetry_weight"] for event in _events(session)} == {0.0}
    assert all(event["is_tester"] is True for event in _events(session))


def test_business_tech_session_created_records_minimal_telemetry_without_text():
    created = ai.create_session({"tree_id": "business_tech", "message": "Bonjour je suis la boulangerie Demo"})
    session = created["session"]
    serialized = json.dumps(_events(session), ensure_ascii=False)

    assert session["metrics"]["schema"] == "oa.audit.session_metrics.v1"
    assert [event["event"] for event in _events(session)] == ["session_created", "button_displayed"]
    assert all(event["privacy"]["pii"] is False and event["privacy"]["contains_free_text"] is False for event in _events(session))
    assert "boulangerie Demo" not in serialized
    assert all("label" not in json.dumps(event, ensure_ascii=False) for event in _events(session))


def test_business_tech_validate_step_records_step_validated_without_answer_text():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    session = ai.add_message(session, "Continuer sans compte")["session"]

    result = ai.validate_step(session, "pacte")

    event = _events(result["session"])[-1]
    assert event["event"] == "step_validated"
    assert event["step"] == "pacte"
    assert event["next_step"] == "identity_public_context"
    assert "Continuer sans compte" not in json.dumps(event, ensure_ascii=False)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_json(method: str, url: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=4) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def start_server(tmp_path: Path):
    port = free_port()
    proc = subprocess.Popen(
        ["python3", "src/proposal_server.py", "--host", "127.0.0.1", "--port", str(port), "--data-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "OA_PROPOSALS_TOKEN": "x" * 40},
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
    proc.wait(timeout=3)
    raise AssertionError("server did not become ready")


def test_public_research_records_research_run_without_public_name_or_url(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        _, created = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions", {"tree_id": "business_tech"})
        sid = created["session"]["id"]
        status, data = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/public-research",
            {"company_public_name": "Boulangerie Demo", "website": "https://demo.example", "dry_run": True},
        )

        event = _events(data["session"])[-1]
        serialized = json.dumps(event, ensure_ascii=False)
        assert status == 200
        assert event["event"] == "research_run"
        assert "Boulangerie Demo" not in serialized
        assert "demo.example" not in serialized
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_button_clicked_endpoint_records_action_metadata_without_reply_label(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        _, created = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions", {"tree_id": "business_tech"})
        sid = created["session"]["id"]
        status, data = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/telemetry",
            {"event": "button_clicked", "step": "pacte", "action_id": "continue_without_account", "intent": "confirm", "rank": 2, "label": "Continuer sans compte"},
        )

        event = _events(data["session"])[-1]
        assert status == 202
        assert event["event"] == "button_clicked"
        assert event["action_id"] == "continue_without_account"
        assert event["rank"] == 2
        assert "Continuer sans compte" not in json.dumps(event, ensure_ascii=False)
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_report_created_records_opaque_audit_id_only(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        _, created = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions", {"tree_id": "business_tech"})
        sid = created["session"]["id"]
        # Le rapport business_tech est maintenant bloqué tant que la session n'est
        # pas complète. Ce test ne vérifie pas le moteur conversationnel, seulement
        # que l'événement report_created reste opaque une fois le gate passé.
        session_path = tmp_path / "audit_sessions" / f"{sid}.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["status"] = "complete"
        session["completion"] = {"complete": True, "completion_pct": 100, "required_steps": [], "validated_steps": []}
        session_path.write_text(json.dumps(session, ensure_ascii=False), encoding="utf-8")
        status, data = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/report",
            {"structured_fields": {"repetitive_tasks": "transcript secret client"}},
        )
        stored = json.loads((tmp_path / "audit_sessions" / f"{sid}.json").read_text(encoding="utf-8"))

        event = _events(stored)[-1]
        assert status == 201
        assert event["event"] == "report_created"
        assert event["audit_id"].startswith("audit-")
        assert "repetitive_tasks" not in event
        assert "transcript secret client" not in json.dumps(event, ensure_ascii=False)
        assert data["session"]["metrics"]["telemetry_events"][-1]["event"] == "report_created"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
