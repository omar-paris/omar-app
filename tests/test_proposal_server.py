from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import proposal_server  # noqa: E402
# Token d'API requis depuis app#13 (refus de démarrer sans auth >=32 chars).
API_TOKEN = "x" * 40
AUTH_HEADERS = {"content-type": "application/json", "authorization": f"Bearer {API_TOKEN}"}
OWNER_HEADERS = {"accept": "application/json", "X-Auth-Request-Email": "client@example.com"}
INTRUDER_HEADERS = {"accept": "application/json", "X-Auth-Request-Email": "intrus@example.com"}


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


def test_server_serves_public_lifecycle_contract_json(tmp_path):
    # Build artifacts are expected to exist in public/api; server must expose them
    # because app.omar.paris proxies /api/* to proposal_server.py, not static files.
    proc, port = start_server(tmp_path)
    try:
        for endpoint, schema in [
            ("/api/appomar-lifecycle.json", "oa.appomar-lifecycle/v1"),
            ("/api/oa-system-contracts.json", "oa.system-contracts/v1"),
        ]:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{endpoint}", timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert payload["schema"] == schema
            serialized = json.dumps(payload, ensure_ascii=False)
            for forbidden in ["BEGIN OPENSSH", "ghp_", "sk-proj-", "-----BEGIN", "Authorization:"]:
                assert forbidden not in serialized
    finally:
        proc.terminate()
        proc.wait(timeout=3)


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
        assert re.fullmatch(r"proposal-[A-Za-z0-9_-]{43}", created["proposal"]["id"])
        assert "client-demo" not in created["proposal"]["id"].lower()
        stored_path = tmp_path / "proposals" / f"{created['proposal']['id']}.json"
        assert stored_path.exists()
        stored_text = stored_path.read_text(encoding="utf-8")
        assert "client@example.com" in stored_text
        for forbidden in ["HCLOUD_TOKEN", "Authorization", "Bearer ", "sk-"]:
            assert forbidden not in stored_text

        get_status, fetched = request_json("GET", f"http://127.0.0.1:{port}/api/proposals/{created['proposal']['id']}", None, OWNER_HEADERS)
        assert get_status == 200
        assert fetched["proposal"]["hetzner_payload"]["create_server_payload"]["server_type"] == "cax21"
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_proposal_api_rejects_enumeration_by_non_owner(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {
            "type": "configuration_proposal",
            "status": "pending_human_go",
            "client_profile": {"company_name": "Client Live", "contact_email": "client@example.com"},
            "hetzner_payload": {"mode": "dry_run_no_paid_resource"},
            "safety": {"paid_actions": "none"},
        }
        _, created = request_json("POST", f"http://127.0.0.1:{port}/api/proposals", payload, AUTH_HEADERS)
        pid = created["proposal"]["id"]

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/proposals/{pid}",
            method="GET",
            headers=INTRUDER_HEADERS,
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("non-owner fetched proposal PII")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code in {403, 404}
            assert body["ok"] is False
            assert "client@example.com" not in json.dumps(body)

        anon_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/proposals/{pid}",
            method="GET",
            headers={"accept": "application/json"},
        )
        try:
            urllib.request.urlopen(anon_req, timeout=3)
            raise AssertionError("anonymous fetched proposal PII")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 404
            assert body == {"ok": False, "error": "proposal_not_found"}
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_proposal_api_keeps_legacy_uuid_slug_readable_only_for_owner(tmp_path):
    legacy_id = "proposal-0123456789abcdef0123456789abcdef-client-live"
    stored = {
        "id": legacy_id,
        "type": "configuration_proposal",
        "status": "pending_human_go",
        "client_profile": {"company_name": "Client Live", "contact_email": "client@example.com"},
        "hetzner_payload": {"mode": "dry_run_no_paid_resource"},
        "safety": {"paid_actions": "none"},
    }
    proposals = tmp_path / "proposals"
    proposals.mkdir(parents=True)
    (proposals / f"{legacy_id}.json").write_text(json.dumps(stored), encoding="utf-8")

    proc, port = start_server(tmp_path)
    try:
        status, fetched = request_json(
            "GET", f"http://127.0.0.1:{port}/api/proposals/{legacy_id}", None, OWNER_HEADERS
        )
        assert status == 200
        assert fetched["proposal"]["id"] == legacy_id

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/proposals/{legacy_id}",
            method="GET",
            headers=INTRUDER_HEADERS,
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("non-owner fetched legacy proposal PII")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 404
            assert body == {"ok": False, "error": "proposal_not_found"}
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
        assert report["schema"] == "oa_audit_report.business_tech.v1"
        assert report["legacy_schema"] == "oa_audit_report.fable_v0"
        assert report["section_count"] == 17
        assert len(report["sections"]) == 17
        assert all(section["sources"] for section in report["sections"])
        assert report["declared_by_client"]
        assert report["omar_hypotheses"]
        assert report["do_not_automate"]
        assert created["onboarding_pack"]["schema"] == "onboarding_pack.v1"
        assert created["onboarding_pack"]["dry_run_contract"]["paid_actions"] == "none"
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
        assert created["omar"]["step"] == "intro"
        assert created["omar"]["missing_fields"] == []
        assert created["omar"]["question"].startswith("Bonjour, je suis Omar, un agent formé par Alexandre Willemetz")
        assert created["omar"]["options"] == ["En savoir plus sur cet Audit.", "On commence !"]

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
        assert valid["session"]["current_step"] == "real_week"
        assert valid["next"]["act"] == "plongee"
        assert valid["next"]["ui"]["rule"] == "70_30_open_questions_buttons_confirm"

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
            {"message": "La semaine dernière j'ai perdu 4 heures sur les réponses WhatsApp, les devis de gâteaux et les relances commandes."},
        )
        assert status == 200
        status, valid2 = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/validate-step",
            {"step": "real_week"},
        )
        assert status == 200
        assert valid2["session"]["current_step"] == "tools"

        status, poison = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/message",
            {"message": "POISON_TRANSCRIPT_BRUT à ne jamais recopier dans le rapport"},
        )
        assert status == 200

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
        assert report["report"]["schema"] == "oa_audit_report.business_tech.v1"
        assert report["report"]["report_contract_version"] == "business_tech.v1"
        assert report["report"]["section_count"] == 17
        assert [section["id"] for section in report["report"]["sections"]] == proposal_server.report_contract_sections()
        assert all(section["items"] for section in report["report"]["sections"])
        assert all(section["sources"] for section in report["report"]["sections"])
        assert "POISON_TRANSCRIPT_BRUT" not in json.dumps(report["report"], ensure_ascii=False)
        stored_audit = json.loads((tmp_path / "audits" / f"{report['audit']['id']}.json").read_text(encoding="utf-8"))
        assert "transcript" not in stored_audit["input"]
        assert "POISON_TRANSCRIPT_BRUT" not in json.dumps(stored_audit, ensure_ascii=False)
        assert report["onboarding_pack"]["schema"] == "onboarding_pack.v1"
        assert report["agent_brief"]["schema"] == "oa.omar-agent-brief.v1"
        assert report["agent_brief"]["agent_operating_contract"]["mode"] == "draft_agent_after_audit"
        assert report["agent_brief"]["evidence_contract"]["verified_public"] == []
        assert all(item["origin"] in {"declared_client", "omar_hypothesis"} for item in report["agent_brief"]["analysis"]["recommendations"])
        get_brief_status, brief_payload = request_json("GET", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/agent-brief")
        assert get_brief_status == 200
        assert brief_payload["agent_brief"]["schema"] == "oa.omar-agent-brief.v1"
        assert report["share"]["exports"]["markdown"].startswith("# ")
        assert report["share"]["exports"]["pdf_status"] == "pending_renderer"
        assert "share_url" in report["share"]

        get_status, share = request_json("GET", f"http://127.0.0.1:{port}/api/audits/{report['audit']['id']}/share")
        assert get_status == 200
        assert share["share"]["exports"]["linkedin_text"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_business_tech_report_api_exposes_premium_consulting_artifacts(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions", {"tree_id": "business_tech"})
        assert status == 201
        sid = created["session"]["id"]
        answers_by_step = {
            "pacte": {"sauvegarde_choix": "Continuer sans compte"},
            "identity_public_context": {"nom_entreprise": "La Fournée API, 56 Rue Grande, 13390 Auriol", "sirene_match": "À corriger"},
            "public_sources_consent": {"consents": {"web_public": False, "sirene_detail": False, "site_web": False, "fiche_google": False, "reseaux": False}},
            "activity_business_model": {"recit_activite": "Boulangerie-pâtisserie artisanale à Auriol, 4 personnes, boutique de quartier et commandes week-end.", "type_clients": "Des particuliers", "taille_equipe": "Solo", "canaux_vente": "Sur place"},
            "person_and_goals": {"objectifs_racontes": "Libérer du temps, mieux piloter la marge et préparer une transmission sereine.", "niveau_digital": "Ça va"},
            "operations_week": {"semaine": "Les appels pour horaires, commandes, allergènes et disponibilités prennent 4 h par semaine.", "top_caillou": "Réponses commandes"},
            "marketing_sales": {"parcours_client_raconte": "Les clients arrivent par boutique, bouche à oreille, fiche Google et appels téléphoniques.", "perte_identifiee": "Je réponds trop tard"},
            "admin_finance_purchasing": {"admin_racontee": "Achats farine beurre emballages, factures fournisseur et marge par famille produit sont suivis sur Excel."},
            "digital_tools_data": {"outils_racontes": "Téléphone, WhatsApp, caisse, Excel, fiche Google et Instagram ; on recopie les commandes à la main.", "outils_confirm": ["Téléphone", "WhatsApp", "Excel"]},
            "risks_limits": {"lignes_rouges": "Allergènes, prix, acomptes et avis négatifs doivent rester validés par un humain.", "donnees_sensibles": ["Bancaire clients"], "validation_humaine": "Je valide tout au début"},
            "diagnosis": {"swot_reaction": "OK", "matrice_reaction": "OK"},
            "recommendations": {"recos_validees": "relances et réponses commandes", "priorisation": ["réponses commandes", "relances"]},
            "validation": {"synthese_finale": "OK pour le rapport", "suite": "Chiffrer ça (devis)"},
        }
        for step_id, answers in answers_by_step.items():
            status, _ = request_json(
                "POST",
                f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/message",
                {"message": json.dumps({"step_id": step_id, "answers": answers}, ensure_ascii=False)},
            )
            assert status == 200
            status, validated = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/validate-step", {"step": step_id})
            assert status == 200, {"step": step_id, "validated": validated}
        assert validated["session"]["status"] == "complete"

        status, report = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/report", {})
        assert status == 201
        premium = report["premium_consulting_report"]
        assert premium["schema"] == "oa.premium-consulting-report.v1"
        assert len(premium["diagnostic_dimensions"]) == 9
        assert len(premium["final_report_sections"]) == 17
        assert premium["conversation_depth_contract"]["schema"] == "oa.audit-step-depth-contract.v1"
        assert premium["agent_profile"]["status"] == "draft_pending_human_validation"
        assert report["premium_consulting_markdown"].startswith("## RAPPORT DE DIAGNOSTIC BUSINESS & TECH")
        bundle = report["final_client_document_bundle"]
        assert bundle["schema"] == "oa.final-client-document-bundle.v1"
        assert bundle["quality_gate"]["ready_for_client_review"] is True
        assert [doc["id"] for doc in bundle["documents"]] == [
            "audit_report",
            "business_manifesto",
            "local_constitution",
            "agent_profile",
            "action_plan_and_devis",
            "open_questions_and_evidence",
        ]
        assert report["session"]["id"] == sid
        assert report["session"]["status"] == "complete"
        assert report["session"]["message_count"] > 0
        assert "messages" not in report["session"]
        assert "chat_history" not in report["session"]
        assert "state" not in report["session"]
        serialized_response = json.dumps(report, ensure_ascii=False)
        assert "first_message_keys" not in serialized_response
        stored_audit = json.loads((tmp_path / "audits" / f"{report['audit']['id']}.json").read_text(encoding="utf-8"))
        assert stored_audit["premium_consulting_report"]["schema"] == "oa.premium-consulting-report.v1"
        assert stored_audit["premium_consulting_markdown"].startswith("## RAPPORT DE DIAGNOSTIC BUSINESS & TECH")
        assert stored_audit["final_client_document_bundle"]["quality_gate"]["document_count"] == 6
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_audit_session_final_report_creates_devis_and_lead_from_oauth_email(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        headers = {"content-type": "application/json", "X-Auth-Request-Email": "prospect@example.com"}
        status, created = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions",
            {"message": "Je suis boulanger à Lille"},
            headers,
        )
        assert status == 201
        sid = created["session"]["id"]
        assert created["session"]["prospect"]["email"] == "prospect@example.com"

        status, report = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/report",
            {
                "activity": "Boulangerie artisanale à Lille",
                "repetitive_tasks": "réponses WhatsApp, devis de gâteaux, relances commandes",
                "current_tools": "WhatsApp, email, Excel",
                "constraints": "allergènes, prix, validation humaine",
            },
            headers,
        )
        assert status == 201
        aid = report["audit"]["id"]
        assert report["lead"]["path"] == f"var/leads/lead-{aid}.json"
        lead = json.loads((tmp_path / "leads" / f"lead-{aid}.json").read_text(encoding="utf-8"))
        assert lead["email"] == "prospect@example.com"
        assert lead["audit_session_id"] == sid
        assert lead["source"] == "app.omar.paris/audit"
        assert lead["safety"]["paid_actions"] == "none"

        status, devis_created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {"audit_id": aid})
        assert status == 201
        devis = devis_created["devis"]
        assert devis["client"]["email"] == "prospect@example.com"
        assert devis["total_mensuel_eur"] == 67
        assert any(line["id"] == "formule-starter" for line in devis["lignes"])

        status, placeholder_devis = request_json(
            "POST",
            f"http://127.0.0.1:{port}/api/devis",
            {"audit_id": aid, "client": {"email": "prospect " + "OAuth Google"}},
        )
        assert status == 201
        assert placeholder_devis["devis"]["client"]["email"] == "prospect@example.com"
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
        assert created["devis"]["total_mensuel_eur"] == 67
        assert created["devis"]["total_unique_eur"] == 150
        assert [line["id"] for line in created["devis"]["lignes"]] == ["formule-starter", "presta-onboarding"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_devis_api_accepts_catalogue_v1_ids_with_honest_runtime_status(tmp_path):
    required = [
        "presence-google-business-avis",
        "recrutement-annonces-candidats",
        "secretaire-tri-demandes",
        "secretaire-redaction-reponses",
        "secretaire-taches-relances",
        "secretaire-documents-devis-syntheses",
        "secretaire-connexions-surveillance",
    ]
    catalog_ids = {item["id"] for item in proposal_server.load_catalog()["products"]}
    assert set(required) <= catalog_ids

    proc, port = start_server(tmp_path)
    try:
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {"items": required})
        assert status == 201
        lines = created["devis"]["lignes"]
        assert [line["id"] for line in lines] == required
        assert all(line["label"].strip() for line in lines)
        assert all(line["catalogue_id"] == line["id"] for line in lines)
        assert {line["capability_status"] for line in lines} == {"potential"}
        assert {line["proof_tier"] for line in lines} == {"potential"}
        assert {line["runtime_scope"] for line in lines} == {"catalogue_only"}
        assert {line["runtime_status"] for line in lines} == {"unknown"}
        assert {line["cost_status"] for line in lines} == {"unknown"}
        for line in lines:
            assert line["proof_scope"].startswith("Catalogue/AppOmar refs only")
            assert line["evidence_refs"]
            assert line["measurement_state"] == {
                "ram_mb": None,
                "disk_mb": None,
                "runtime_cost": None,
                "state": "unknown",
                "measured_at": None,
                "measurement_ref": None,
            }
            assert line["durable_gate_artifact_ref"] == ""
            assert line["human_approval_required"] is True
            assert line["safe_claim"].strip()
            assert line["do_not_claim"]
        serialized = json.dumps(lines, ensure_ascii=False).lower()
        for forbidden in ["installed", "enabled", "healthy", "live"]:
            assert forbidden not in serialized
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_public_audit_onboarding_funnel_exposes_pr56_proof_without_upgrading_v1_modules(tmp_path):
    catalog = {item["id"]: item for item in proposal_server.load_catalog()["products"]}
    proof = catalog["appomar-public-audit-onboarding-funnel"]

    assert proof["proof_status"] == "proven"
    assert proof["proof_tier"] == "proven"
    assert proof["capability_status"] == "proven"
    assert proof["source_task"] == "t_d5dda7f0"
    assert proof["pr"] == 56
    assert proof["release_gate_ref"] == "PR#56"
    assert proof["durable_gate_artifact_ref"]
    assert proof["sensitive_endpoints_protected"] is True
    assert proof["runtime_client_proven"] is False
    assert proof["ram_mb"] == "unknown"
    assert proof["disk_mb"] == "unknown"
    assert proof["measurement_state"] == {
        "ram_mb": None,
        "disk_mb": None,
        "runtime_cost": None,
        "state": "unknown",
        "measured_at": None,
        "measurement_ref": None,
    }
    assert proof["live_smoke"]["public_endpoints"] == {
        "/audit/": 200,
        "/onboarding/": 200,
        "/api/oa-start-packs.json": 200,
        "/api/apps-l1.json": 200,
        "/api/connector-readiness.json": 200,
    }
    assert proof["live_smoke"]["sensitive_endpoints"] == {
        "/api/onboarding/status": 401,
        "/api/proposals": 401,
    }

    v1_ids = {
        "presence-google-business-avis",
        "recrutement-annonces-candidats",
        "secretaire-tri-demandes",
        "secretaire-redaction-reponses",
        "secretaire-taches-relances",
        "secretaire-documents-devis-syntheses",
        "secretaire-connexions-surveillance",
    }
    for item_id in v1_ids:
        item = catalog[item_id]
        assert item["capability_status"] == "potential"
        assert item["proof_tier"] == "potential"
        assert item["runtime_status"] == "unknown"
        assert item["cost_status"] == "unknown"
        assert item["runtime_client_proven"] is False
        assert item["ram_mb"] == "unknown"
        assert item["disk_mb"] == "unknown"

    proc, port = start_server(tmp_path)
    try:
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {"items": ["appomar-public-audit-onboarding-funnel"]})
        assert status == 201
        line = created["devis"]["lignes"][0]
        assert line["id"] == "appomar-public-audit-onboarding-funnel"
        assert line["proof_status"] == "proven"
        assert line["proof_tier"] == "proven"
        assert line["source_task"] == "t_d5dda7f0"
        assert line["pr"] == 56
        assert line["live_smoke"]["public_endpoints"]["/audit/"] == 200
        assert line["live_smoke"]["sensitive_endpoints"]["/api/proposals"] == 401
        assert line["sensitive_endpoints_protected"] is True
        assert line["runtime_client_proven"] is False
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_legacy_modules_map_to_catalogue_v1_refs_in_devis(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {"items": ["mod-presence", "mod-paperasse"]}
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", payload)
        assert status == 201
        lines_by_id = {line["id"]: line for line in created["devis"]["lignes"]}
        assert lines_by_id["mod-presence"]["catalogue_refs"] == ["presence-google-business-avis"]
        assert set(lines_by_id["mod-paperasse"]["catalogue_refs"]) >= {
            "secretaire-tri-demandes",
            "secretaire-redaction-reponses",
            "secretaire-taches-relances",
            "secretaire-documents-devis-syntheses",
        }
        assert created["devis"]["total_mensuel_eur"] == 45
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
        assert created["onboarding_pack"]["schema"] == "onboarding_pack.v1"
        assert created["onboarding_pack"]["dry_run_contract"]["schema"] == "omartop.provisioning-contract.v1"
        assert created["devis_source"]["schema"] == "oa_devis_source.v1"
        assert created["devis_source"]["governance"]["requires_user_validation_before_checkout"] is True
        assert created["consent_snapshot"]["schema"] == "oa_audit_consent.v1"
        assert created["consent_snapshot"]["permissions"]["public_web_search"] is True
        assert created["consent_snapshot"]["improvement_opt_in"] is False
        assert {s["type"] for s in created["sources_used"]} >= {"user_answer", "uploaded_document", "sector_reference", "public_web_authorized", "legal_registry_authorized"}
        assert {s["evidence_origin"] for s in created["sources_used"]} >= {"declared_client", "provided_document", "verified_public", "omar_hypothesis"}
        assert created["report"]["source_separation"] == ["declared_client", "verified_public", "omar_hypothesis", "provided_document"]
        assert created["report"]["cyber_baseline"]["checks"]
        assert created["report"]["regulatory_baseline"]["facturation_electronique_2027"]["included"] is True
        assert all({"score", "why", "evidence", "limits", "how_to_improve"} <= set(score) for score in created["report"]["scores"].values())
        assert any(item["catalog_id"] == "formule-starter" for item in created["devis_source"]["recommended_items"])
        assert all(item["recommendation_ref"] and item["evidence"] for item in created["devis_source"]["recommended_items"])

        aid = created["audit"]["id"]
        status, devis_created = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {"audit_id": aid})
        assert status == 201
        devis = devis_created["devis"]
        assert devis["statut"] == "a_valider"
        assert devis["audit_id"] == aid
        assert devis["justification"]
        assert devis["total_mensuel_eur"] >= 67

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

def test_audit_to_prefilled_onboarding_and_justified_devis_contract_public(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        payload = {
            "activity": "Boulangerie artisanale à Lille",
            "urgency": "répondre plus vite aux commandes et devis",
            "ai_level": "débutant",
            "repetitive_tasks": "réponses WhatsApp, devis de gâteaux, relances commandes",
            "current_tools": "WhatsApp, email, Excel",
            "constraints": "allergènes, prix, validation humaine avant envoi",
        }
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/audits", payload)
        assert status == 201
        aid = created["audit"]["id"]

        status, prefill = request_json("GET", f"http://127.0.0.1:{port}/api/onboarding/prefill?audit_id={aid}")
        assert status == 200
        assert prefill["ok"] is True
        assert prefill["audit_id"] == aid
        assert prefill["onboarding"]["schema"] == "appomar.onboarding_prefill.v1"
        assert prefill["onboarding"]["record"]["activite"] == "Boulangerie artisanale à Lille"
        assert "produire_documents" in prefill["onboarding"]["record"]["objectifs"]
        assert prefill["onboarding"]["agent_profile"]["modules"]
        assert prefill["onboarding"]["source_summary"]["title"] == "Voici ce que l'audit a compris — confirme/corrige"

        status, created_devis = request_json("POST", f"http://127.0.0.1:{port}/api/devis", {"audit_id": aid})
        assert status == 201
        devis = created_devis["devis"]
        assert devis["audit_id"] == aid
        assert devis["public_session_scope"] == {"kind": "audit_id", "id": aid}
        assert devis["devis_contract"]["template"] == "{item} — recommandé parce que {reco_source}"
        assert devis["devis_contract"]["lines"]
        assert all(line["display"].startswith(line["item"]) for line in devis["devis_contract"]["lines"])
        assert all("recommandé parce que" in line["display"] for line in devis["devis_contract"]["lines"] if not line["optional"])
        assert any(not line["optional"] for line in devis["devis_contract"]["lines"])
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_public_onboarding_prefill_escapes_audit_summary_before_innerhtml_render():
    onboarding_html = (ROOT / "pages-app" / "onboarding.html").read_text(encoding="utf-8")
    devis_html = (ROOT / "pages-app" / "devis.html").read_text(encoding="utf-8")

    assert "function escText" in onboarding_html
    assert "<p>${escText(s.summary" in onboarding_html
    assert "box.innerHTML=`<h2>${escText" in onboarding_html
    assert "<p>${s.summary" not in onboarding_html
    assert "${w.display||''}" not in devis_html
    assert "${esc(w.display" in devis_html


def test_public_tunnel_pages_wire_audit_id_between_report_onboarding_and_devis():
    audit_html = (ROOT / "pages-app" / "audit.html").read_text(encoding="utf-8")
    onboarding_html = (ROOT / "pages-app" / "onboarding.html").read_text(encoding="utf-8")
    devis_html = (ROOT / "pages-app" / "devis.html").read_text(encoding="utf-8")

    assert "/onboarding/?audit_id=" in audit_html
    assert "api/onboarding/prefill?audit_id" in onboarding_html
    assert "Voici ce que l'audit a compris — confirme/corrige" in onboarding_html
    assert "/devis/?audit_id=" in onboarding_html
    assert "audit_id" in devis_html
    assert "recommandé parce que" in devis_html


def test_devis_requires_user_validation_before_checkout_then_reports_unconfigured_payment_provider(tmp_path):
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
            assert body["error"] == "payment_provider_unconfigured"
            assert body["payment_provider_target"] == "not_configured"
            assert body["legacy_provider_disabled"] is True
            assert body["total_mensuel_eur"] == 67
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
        assert devis["total_mensuel_eur"] == 134
        assert devis["total_unique_eur"] == 150
        assert devis["lignes"][0]["qty"] == 2

        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/devis/{devis['id']}.pdf", method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            body = response.read()
            assert response.status == 200
            assert response.headers["content-type"] == "application/pdf"
            assert body.startswith(b"%PDF-1.4")
            assert b"Omar & Alex" in body
            assert b"Formule Starter: 67 EUR/mois x2 = 134 EUR/mois" in body
            assert b"Total mensuel HT: 134 EUR" in body
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


def onboarding_payload(**overrides):
    payload = {
        "record": {
            "identite": "Marie",
            "entreprise": "Atelier Démo",
            "activite": "Artisan / BTP",
            "email": "marie@example.test",
            "domaine": "non",
            "objectifs": ["tri_messages", "produire_documents"],
            "outils": ["google_workspace"],
            "infra": "hybride",
            "appareils": ["pc_windows", "smartphone"],
        },
        "agent_profile": {
            "agent_name": "Omar",
            "modules": ["tri_messages", "produire_documents"],
            "infra": "hybride",
            "devices": [{"id": "pc_windows", "type": "pc", "state": "inconnu"}],
            "pc_smoke": "pending",
        },
        "completed_sections": ["identite", "objectifs"],
        "current_step": 2,
        "autosave": True,
    }
    payload.update(overrides)
    return payload


def test_onboarding_api_persists_resume_record_and_updates_same_id(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/onboarding", onboarding_payload())
        assert status == 201
        assert created["ok"] is True
        oid = created["onboarding"]["id"]
        assert re.fullmatch(r"onboarding-[A-Za-z0-9_-]{43}", oid)
        assert "Atelier" not in oid
        assert "Demo" not in oid
        assert "Démo" not in oid
        assert not re.search(r"20\d{6}T\d{6}Z", oid)
        assert created["onboarding"]["resume_url"] == f"/onboarding/?record_id={oid}"
        assert created["onboarding"]["completed_sections"] == ["identite", "objectifs"]
        assert created["onboarding"]["safety"]["paid_actions"] == "none"

        guessed_oid = "onboarding-20260701T220331Z-atelier-demo-confidentiel"
        with pytest.raises(urllib.error.HTTPError) as guessed_exc:
            request_json("GET", f"http://127.0.0.1:{port}/api/onboarding/{guessed_oid}")
        assert guessed_exc.value.code == 404

        status, fetched = request_json("GET", f"http://127.0.0.1:{port}/api/onboarding/{oid}")
        assert status == 200
        assert fetched["onboarding"]["record"]["entreprise"] == "Atelier Démo"
        assert fetched["onboarding"]["current_step"] == 2

        updated_payload = onboarding_payload(
            record_id=oid,
            completed_sections=["identite", "objectifs", "outils"],
            current_step=3,
        )
        updated_payload["record"]["outils"] = ["microsoft_365", "crm"]
        status, updated = request_json("POST", f"http://127.0.0.1:{port}/api/onboarding", updated_payload)
        assert status == 200
        assert updated["onboarding"]["id"] == oid
        assert updated["onboarding"]["completed_sections"] == ["identite", "objectifs", "outils"]
        assert updated["onboarding"]["record"]["outils"] == ["microsoft_365", "crm"]
        assert (tmp_path / "clients" / f"{oid}.json").exists()
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_onboarding_simulation_preview_is_dry_run_and_secret_safe(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/onboarding", onboarding_payload())
        assert status == 201
        oid = created["onboarding"]["id"]
        simulation = {}
        for target, expected in {
            "hybride": "hybride",
            "vps_managé": "vps",
            "inconnu": "vps",
            "pc": "pc",
        }.items():
            status, simulated = request_json("POST", f"http://127.0.0.1:{port}/api/onboarding/{oid}/simulate", {"target": target})
            assert status == 200
            simulation = simulated["simulation"]
            assert simulation["schema"] == "appomar.onboarding_simulation.v1"
            assert simulation["source_onboarding_id"] == oid
            assert simulation["provisioning_preview"]["target"] == expected
        assert simulation["agent_spec"]["agent_name"] == "Omar"
        assert simulation["provisioning_preview"]["mode"] == "dry-run"
        assert simulation["provisioning_preview"]["paid_actions"] == "none"
        assert simulation["safety"]["paid_actions"] == "none"
        assert simulation["next_steps"][0]["route"] == "/devis/"
        raw = json.dumps(simulation, ensure_ascii=False)
        for forbidden in ["HCLOUD_TOKEN", "Authorization", "Bearer ", "sk-"]:
            assert forbidden not in raw
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_call_audit_agent_uses_file_prompt_and_minimal_env(monkeypatch):
    captured = {}

    def fake_run(args, capture_output, text, timeout, env):
        captured["args"] = args
        captured["env"] = env
        query = args[args.index("-q") + 1]
        assert "PROSPECT_SECRET" not in " ".join(args)
        assert "Fichier: " in query
        prompt_path = query.rsplit("Fichier: ", 1)[1]
        captured["prompt_path"] = prompt_path
        assert Path(prompt_path).exists()
        assert oct(Path(prompt_path).stat().st_mode & 0o777) == "0o600"
        assert "PROSPECT_SECRET" in Path(prompt_path).read_text(encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, stdout="session_id: abc\nRéponse Omar", stderr="")

    monkeypatch.setattr(proposal_server, "AUDIT_PROFILES", ["oa-audit"])
    monkeypatch.setenv("HCLOUD_TOKEN", "SERVER_SECRET_SHOULD_NOT_INHERIT")
    monkeypatch.setenv("OA_PROPOSALS_TOKEN", "APP_SECRET_SHOULD_NOT_INHERIT")
    monkeypatch.setattr(proposal_server.subprocess, "run", fake_run)

    result = proposal_server.call_audit_agent("Client dit PROSPECT_SECRET")

    assert result == ("Réponse Omar", "oa-audit")
    assert captured["args"][:4] == [proposal_server.HERMES_BIN, "-p", "oa-audit", "chat"]
    assert captured["args"][-2:] == ["-t", "file"]
    assert "PROSPECT_SECRET" not in " ".join(captured["args"])
    assert captured["env"]["PYTHONUNBUFFERED"] == "1"
    assert "HCLOUD_TOKEN" not in captured["env"]
    assert "OA_PROPOSALS_TOKEN" not in captured["env"]
    assert not Path(captured["prompt_path"]).exists()
