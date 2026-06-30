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


def start_server(tmp_path: Path, clients_dir: Path | None = None):
    import os
    port = free_port()
    cmd = ["python3", "src/proposal_server.py", "--host", "127.0.0.1", "--port", str(port), "--data-dir", str(tmp_path)]
    if clients_dir is not None:
        cmd.extend(["--clients-dir", str(clients_dir)])
    proc = subprocess.Popen(
        cmd,
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


def test_oauth_client_can_only_read_own_proposals(tmp_path):
    clients_dir = tmp_path / "clients"
    (clients_dir / "client-a").mkdir(parents=True)
    (clients_dir / "client-b").mkdir(parents=True)
    (clients_dir / "client-a" / "app-emails.txt").write_text("alice@example.com\n", encoding="utf-8")
    (clients_dir / "client-b" / "app-emails.txt").write_text("bob@example.com\n", encoding="utf-8")
    proc, port = start_server(tmp_path / "data", clients_dir)
    try:
        payload = {
            "type": "configuration_proposal",
            "status": "pending_human_go",
            "client_profile": {"company_name": "Client A", "contact_email": "alice@example.com"},
            "hetzner_payload": {"mode": "dry_run_no_paid_resource"},
            "safety": {"paid_actions": "none"},
        }
        alice_headers = {"content-type": "application/json", "X-Auth-Request-Email": "alice@example.com"}
        bob_headers = {"content-type": "application/json", "X-Auth-Request-Email": "bob@example.com"}
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/proposals", payload, alice_headers)
        assert status == 201
        pid = created["proposal"]["id"]
        assert created["proposal"]["owner_client_id"] == "client-a"

        get_status, fetched = request_json("GET", f"http://127.0.0.1:{port}/api/proposals/{pid}", None, alice_headers)
        assert get_status == 200
        assert fetched["proposal"]["id"] == pid

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/proposals/{pid}", method="GET", headers=bob_headers
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("cross-client proposal read accepted")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 403
            assert body["ok"] is False
            assert body["error"] == "forbidden"
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_unknown_oauth_email_cannot_create_proposal(tmp_path):
    clients_dir = tmp_path / "clients"
    (clients_dir / "client-a").mkdir(parents=True)
    (clients_dir / "client-a" / "app-emails.txt").write_text("alice@example.com\n", encoding="utf-8")
    proc, port = start_server(tmp_path / "data", clients_dir)
    try:
        payload = {
            "type": "configuration_proposal",
            "status": "pending_human_go",
            "client_profile": {"company_name": "Intrus", "contact_email": "intrus@example.com"},
            "hetzner_payload": {"mode": "dry_run_no_paid_resource"},
            "safety": {"paid_actions": "none"},
        }
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/proposals",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"content-type": "application/json", "X-Auth-Request-Email": "intrus@example.com"},
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("unknown OAuth email accepted")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 401
            assert body["ok"] is False
            assert body["error"] == "unauthorized"
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_audit_api_stores_personalized_report_without_paid_actions_or_secrets(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {
            "activity": "Boulangerie artisanale",
            "urgency": "mieux répondre aux clients",
            "ai_level": "débutant",
            "repetitive_tasks": "relances clients\ndevis",
            "current_tools": "email, Excel, WhatsApp",
            "constraints": "données clients, publication externe",
            "email": "marie@example.com",
        }
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/audits", payload)
        assert status == 201
        assert created["ok"] is True
        assert created["audit"]["id"].startswith("audit-")
        assert created["audit"]["status"] == "draft_report_ready"
        report = created["report"]
        assert "Boulangerie artisanale" in report["title"]
        assert any("relances clients" in item for item in report["opportunities"])
        assert report["prompts"]
        assert report["commands"] == ["mkdir -p ~/audit-ia-test/{documents,prompts,resultats}"]
        stored_path = tmp_path / "audits" / f"{created['audit']['id']}.json"
        stored = json.loads(stored_path.read_text(encoding="utf-8"))
        assert stored["safety"]["paid_actions"] == "none"
        assert stored["safety"]["provisioning"] == "none"
        for forbidden in ["HCLOUD_TOKEN", "Authorization", "Bearer ", "sk-"]:
            assert forbidden not in stored_path.read_text(encoding="utf-8")

        get_status, fetched = request_json("GET", f"http://127.0.0.1:{port}/api/audits/{created['audit']['id']}")
        assert get_status == 200
        assert fetched["audit"]["id"] == created["audit"]["id"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)

def test_audit_api_rejects_missing_required_fields_and_secret_like_payloads(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        for payload in [
            {"activity": "", "repetitive_tasks": "relances"},
            {"activity": "Commerce", "repetitive_tasks": "token sk-test-123"},
        ]:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/audits",
                data=json.dumps(payload).encode("utf-8"),
                method="POST",
                headers={"content-type": "application/json"},
            )
            try:
                urllib.request.urlopen(req, timeout=3)
                raise AssertionError("invalid audit payload accepted")
            except urllib.error.HTTPError as exc:
                body = json.loads(exc.read().decode("utf-8"))
                assert exc.code == 422
                assert body["ok"] is False
    finally:
        proc.terminate()
        proc.wait(timeout=3)

def test_audit_session_backend_drives_sector_questions_and_exports(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        status, created = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions",
            {"message": "Je suis boulanger"},
        )
        assert status == 201
        sid = created["session"]["id"]
        assert created["session"]["sector_id"] == "bakery"
        assert created["omar"]["missing_fields"]
        assert "question" in created["omar"]

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/validate-step",
            data=json.dumps({"step": "activity"}).encode("utf-8"),
            method="POST",
            headers={"content-type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("incomplete activity step accepted")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 409
            assert body["error"] == "step_incomplete"
            assert "location" in body["completion"]["missing_fields"]

        status, msg = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/message",
            {"message": "Boulangerie à Lille, boutique de 4 personnes, clients particuliers et entreprises, environ 350k€ de CA, créée il y a 8 ans."},
        )
        assert status == 200
        assert msg["session"]["sector_id"] == "bakery"

        status, valid = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/validate-step",
            {"step": "activity"},
        )
        assert status == 200
        assert valid["completion"]["ready"] is True
        assert valid["session"]["current_step"] == "research"

        status, research = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/research-plan",
            {
                "company_public_name": "Boulangerie Demo Lille",
                "website": "https://demo-boulangerie.example",
                "consents": {"public_web_search": True, "legal_registry_lookup": True, "social_media_lookup": False},
            },
        )
        assert status == 200
        assert research["research_plan"]["schema"] == "oa_audit_research_plan.v1"
        assert research["research_plan"]["sector_id"] == "bakery"
        assert research["research_plan"]["safety"]["execute_external_calls"] is False
        assert research["research_plan"]["competitors"]["direct"]
        assert research["research_plan"]["context_fields"]

        status, public_research = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/public-research",
            {
                "company_public_name": "Boulangerie Demo Lille",
                "website": "https://demo-boulangerie.example",
                "consents": {"public_web_search": True, "legal_registry_lookup": True, "social_media_lookup": False},
                "dry_run": True,
            },
        )
        assert status == 200
        assert public_research["research_result"]["schema"] == "oa_public_research_result.v1"
        assert public_research["research_result"]["safety"]["external_calls_attempted"] is False
        assert public_research["research_result"]["not_executed"]

        status, msg2 = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/message",
            {"message": "J'autorise la recherche web publique sur le site, la fiche Google et les concurrents proches."},
        )
        assert status == 200
        status, valid2 = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/validate-step",
            {"step": "research"},
        )
        assert status == 200
        assert valid2["session"]["current_step"] == "pain"

        status, report = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/report",
            {
                "activity": "Boulangerie artisanale à Lille",
                "repetitive_tasks": "réponses WhatsApp, devis de gâteaux, relances commandes",
                "current_tools": "WhatsApp, email, Excel",
                "constraints": "allergènes, prix, validation humaine",
            },
        )
        assert status == 201
        assert report["audit"]["id"].startswith("audit-")
        assert "réponses WhatsApp" in "\n".join(report["report"]["diagnostic"] + report["report"]["opportunities"])
        assert report["share"]["exports"]["markdown"].startswith("# ")
        assert report["share"]["exports"]["pdf_status"] == "pending_renderer"
        assert "share_url" in report["share"]

        get_status, share = request_json("GET", f"http://127.0.0.1:{port}/api/audits/{report['audit']['id']}/share")
        assert get_status == 200
        assert share["share"]["exports"]["linkedin_text"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)

def test_devis_api_accepts_item_objects_from_frontend_without_crashing(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {"items": [{"id": "formule-starter"}, {"id": "presta-onboarding"}]}
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", payload)
        assert status == 201
        assert created["ok"] is True
        assert created["devis"]["total_mensuel_eur"] == 49
        assert created["devis"]["total_unique_eur"] == 150
        assert [line["id"] for line in created["devis"]["lignes"]] == ["formule-starter", "presta-onboarding"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)

def test_rigorous_audit_persists_consents_sources_devis_source_and_delete(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {
            "activity": "Boulangerie artisanale à Lille",
            "urgency": "répondre plus vite aux clients sans erreur",
            "ai_level": "débutant",
            "repetitive_tasks": "réponses WhatsApp, devis de gâteaux, relances commandes",
            "current_tools": "WhatsApp, email, Excel",
            "constraints": "allergènes, prix, validation humaine avant envoi",
            "consents": {
                "public_web_search": True,
                "legal_registry_lookup": True,
                "social_media_lookup": False,
                "document_analysis": True,
                "market_trends_lookup": True,
                "anonymized_improvement": False,
            },
            "uploaded_documents": [{"name": "business-plan.pdf", "kind": "business_plan"}],
        }
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/audits", payload)
        assert status == 201
        assert created["devis_source"]["schema"] == "oa_devis_source.v0"
        assert created["devis_source"]["governance"]["requires_user_validation_before_checkout"] is True
        assert created["consent_snapshot"]["permissions"]["public_web_search"] is True
        assert created["consent_snapshot"]["improvement_opt_in"] is False
        assert {s["type"] for s in created["sources_used"]} >= {"user_answer", "uploaded_document", "sector_reference", "public_web_authorized", "legal_registry_authorized"}
        assert any(item["catalog_id"] == "formule-starter" for item in created["devis_source"]["recommended_items"])

        aid = created["audit"]["id"]
        status, devis_created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {"audit_id": aid})
        assert status == 201
        devis = devis_created["devis"]
        assert devis["statut"] == "a_valider"
        assert devis["audit_id"] == aid
        assert devis["justification"]
        assert devis["total_mensuel_eur"] >= 49

        status, deleted = request_json("POST", f"http://127.0.0.1:{port}/api/audits/{aid}/delete", {"confirm_delete": True})
        assert status == 200
        assert deleted["audit"]["status"] == "deleted"
        stored = json.loads((tmp_path / "audits" / f"{aid}.json").read_text(encoding="utf-8"))
        assert stored["personal_data_removed"] is True
        assert "report" not in stored
        assert "devis_source" not in stored
    finally:
        proc.terminate()
        proc.wait(timeout=3)

def test_devis_requires_user_validation_before_checkout_then_reports_unconfigured_stripe(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {"items": ["formule-starter", "presta-onboarding"]})
        assert status == 201
        did = created["devis"]["id"]
        assert created["devis"]["statut"] == "a_valider"

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/checkout",
            data=json.dumps({"devis_id": did}).encode("utf-8"),
            method="POST",
            headers={"content-type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("unvalidated checkout accepted")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 409
            assert body["error"] == "devis_not_validated"

        status, validated = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/devis/{did}/validate",
            {"accepted": True, "email": "client@example.test", "understood": "devis lu, limites comprises"},
        )
        assert status == 200
        assert validated["devis"]["statut"] == "user_validated"

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/checkout",
            data=json.dumps({"devis_id": did}).encode("utf-8"),
            method="POST",
            headers={"content-type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("checkout unexpectedly configured")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 503
            assert body["error"] == "stripe_non_configure"
            assert body["total_mensuel_eur"] == 49
            assert body["total_unique_eur"] == 150
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


def test_devis_accepts_dict_items_and_exports_pdf(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {
            "client": {"nom": "Smoke Maryse", "email": "maryse@example.test"},
            "items": [{"id": "formule-starter", "qty": 2}, {"id": "presta-onboarding", "qty": 1}],
        }
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", payload)
        assert status == 201
        devis = created["devis"]
        assert devis["statut"] == "a_valider"
        assert devis["total_mensuel_eur"] == 98
        assert devis["total_unique_eur"] == 150
        assert devis["lignes"][0]["qty"] == 2

        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/devis/{devis['id']}.pdf", method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            body = response.read()
            assert response.status == 200
            assert response.headers["content-type"] == "application/pdf"
            assert body.startswith(b"%PDF-1.4")
            assert b"Omar & Alex" in body
            assert b"Formule Starter: 49 EUR/mois x2 = 98 EUR/mois" in body
            assert b"Total mensuel HT: 98 EUR" in body
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_devis_rejects_unknown_items_instead_of_empty_quote(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {"client": {"nom": "Smoke"}, "items": [{"id": "unknown", "qty": 1}]}
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/devis",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"content-type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("unknown-only devis accepted")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 422
            assert body["error"] == "aucun item catalogue valide"
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_appomar_creates_provisioning_dry_run_contract_from_devis(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        _, created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {
            "client": {"nom": "Maryse"},
            "items": ["formule-starter", "presta-onboarding"],
        })
        did = created["devis"]["id"]
        status, payload = request_json("POST", f"http://127.0.0.1:{port}/api/provisioning/dry-run", {
            "devis_id": did,
            "target": "hybride",
        })
        assert status == 201
        contract = payload["provisioning"]
        assert contract["schema"] == "omartop.provisioning-contract.v1"
        assert contract["source_devis_id"] == did
        assert contract["target"] == "hybride"
        assert contract["mode"] == "dry-run"
        assert contract["paid_actions"] == "none"
        assert contract["status"] == "pending_go"
        assert contract["pc_smoke"]["present"] is True
        assert contract["vps_smoke"]["present"] is True

        get_status, fetched = request_json("GET", f"http://127.0.0.1:{port}/api/provisioning/{did}")
        assert get_status == 200
        assert fetched["provisioning"]["source_devis_id"] == did
    finally:
        proc.terminate()
        proc.wait(timeout=3)
