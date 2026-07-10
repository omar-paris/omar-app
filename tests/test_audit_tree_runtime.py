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


def test_business_tech_tree_loads_v0_scope_and_enforces_server_policy():
    tree = ai.load_business_tech_tree()
    assert tree["schema"] == "oa.audit-tree/1"
    assert len(tree["steps"]) == 14
    assert tree["principles"]["message_max_lignes"] == 3

    evidence = tree["evidence_contract"]
    assert {item["id"] for item in evidence["origins"]} == {
        "declared_client",
        "verified_public",
        "omar_hypothesis",
        "provided_document",
    }
    assert evidence["required_fields"] == ["origin", "confidence", "source_ref"]

    consent = tree["consent_contract"]
    assert {source["id"] for source in consent["sources"]} >= {
        "sirene_detail",
        "site_web",
        "fiche_google",
        "reseaux",
        "documents",
    }
    assert consent["refusal_policy"] == "non_blocking"
    assert {case["id"] for case in consent["error_handling"]} >= {"multiple_establishments", "sirene_non_diffusible", "obsolete_public_data"}

    scoring = tree["scoring_contract"]
    assert {score["id"] for score in scoring["scores"]} >= {
        "cyber_hygiene_score",
        "operational_friction_score",
        "digital_data_ai_maturity_score",
        "automation_value_score",
        "automation_risk_score",
    }
    for score in scoring["scores"]:
        assert {"signals", "why", "limits", "how_to_improve"} <= set(score)

    onboarding = tree["onboarding_contract"]
    assert {"role", "mission", "tone", "channels", "allowed_connectors", "forbidden_data", "human_gates", "initial_routines", "test_scenarios", "success_criteria"} <= set(onboarding["required_fields"])

    session = ai.create_session({"tree_id": "business_tech", "message": "Bonjour"})["session"]
    assert session["schema"] == "oa_audit_session.business_tech.v1"
    assert session["runtime"]["v0_scope"] == tree["v0_scope"]["steps"]
    q = ai.next_question(session)
    assert q["step"] == "pacte"
    assert q["interaction"] == "quick_replies"
    assert q["policy"]["regle_70_30"] is True
    assert q["policy"]["message_max_lignes"] == 3
    assert len(q["question"].splitlines()) <= 3
    assert set(q["allowed_interactions_v0"]) == {"free_text", "quick_replies", "validation_card", "rank"}


def test_business_tech_tree_session_persists_structured_outputs_and_branches_hr_solo():
    created = ai.create_session({"tree_id": "business_tech"})
    session = created["session"]
    answers = {
        "pacte": {"sauvegarde_choix": "Continuer sans compte"},
        "identity_public_context": {"nom_entreprise": "DU PAIN ET DES IDEES Paris", "sirene_match": "C'est bien moi"},
        "public_sources_consent": {"consents": {"web_public": True, "sirene_detail": True, "site_web": False, "fiche_google": False, "reseaux": False}},
        "activity_business_model": {"recit_activite": "Boulangerie à Paris", "type_clients": "Des particuliers", "taille_equipe": "Solo", "canaux_vente": "Sur place"},
        "person_and_goals": {"objectifs_racontes": "gagner du temps", "niveau_digital": "Ça va"},
        "operations_week": {"semaine": "devis et commandes prennent 3 h par semaine", "top_caillou": "Devis"},
        "admin_finance_purchasing": {"admin_racontee": "factures et fournisseurs sur Excel"},
        "digital_tools_data": {"outils_racontes": "Excel, WhatsApp", "outils_confirm": ["Excel", "WhatsApp"]},
        "risks_limits": {"lignes_rouges": "paiements et données clients", "donnees_sensibles": ["Bancaire clients"], "validation_humaine": "Je valide tout au début"},
        "diagnosis": {"swot_reaction": "OK", "matrice_reaction": "OK"},
        "recommendations": {"recos_validees": "relances", "priorisation": ["relances", "devis"]},
        "validation": {"synthese_finale": "OK pour le rapport", "suite": "Chiffrer ça (devis)"},
    }
    for step_id in list(session["runtime"]["v0_scope"]):
        result = ai.add_message(session, json.dumps({"step_id": step_id, "answers": answers[step_id]}, ensure_ascii=False))["session"]
        session = result
        validation = ai.validate_step(session, step_id)
        assert validation["ok"], validation
        session = validation["session"]

    assert session["status"] == "complete"
    assert session["completion"]["complete"] is True
    assert "hr_team_organization" in session["runtime"]["skipped_steps"]
    for bucket in ["report", "onboarding", "devis"]:
        assert session["outputs"][bucket], bucket
    assert "identite_officielle" in session["outputs"]["report"]
    assert session["outputs"]["devis"]["devis_source"]["source_step"] == "validation"



def test_business_tech_continue_without_account_records_pacte_and_advances():
    created = ai.create_session({"tree_id": "business_tech"})
    session = created["session"]

    assert session["current_step"] == "pacte"
    assert ai.validate_step(session, "pacte")["ok"] is False

    session = ai.add_message(session, "Continuer sans compte")["session"]
    pacte_answers = session["state"]["pacte"]["answers"]
    assert pacte_answers["sauvegarde_choix"] == "Continuer sans compte"
    assert pacte_answers["tutoiement"] == "Restons au vous"

    validation = ai.validate_step(session, "pacte")
    assert validation["ok"] is True, validation
    assert validation["session"]["current_step"] == "identity_public_context"

def test_business_tech_sector_pack_relance_is_depth_limited():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    ai.add_message(session, json.dumps({"step_id": "activity_business_model", "answers": {"recit_activite": "Je suis boulanger", "type_clients": "Des particuliers", "taille_equipe": "2-5"}}, ensure_ascii=False))
    q1 = ai.next_question(session, "operations_week")
    assert q1["sector_pack_relance"]["depth"] == 1
    assert q1["sector_pack_relance"]["question"]
    ai.add_message(session, json.dumps({"step_id": "operations_week", "answers": {"relance_pack": "stocks et invendus"}}, ensure_ascii=False))
    q2 = ai.next_question(session, "operations_week")
    assert q2["sector_pack_relance"] is None


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_json(method: str, url: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=4) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_audit_session_endpoint_uses_tree_runtime_when_requested(tmp_path):
    port = free_port()
    proc = subprocess.Popen(
        ["python3", "src/proposal_server.py", "--host", "127.0.0.1", "--port", str(port), "--data-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "OA_PROPOSALS_TOKEN": "x" * 40},
    )
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.2).read()
                break
            except Exception:
                if proc.poll() is not None:
                    out, err = proc.communicate(timeout=1)
                    raise AssertionError(f"server exited early\nOUT={out}\nERR={err}")
                time.sleep(0.05)
        status, created = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions", {"tree_id": "business_tech"})
        assert status == 201
        sid = created["session"]["id"]
        assert created["session"]["schema"] == "oa_audit_session.business_tech.v1"
        assert len(created["omar"]["question"].splitlines()) <= 3
        status, posted = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/message", {"message": json.dumps({"step_id": "pacte", "answers": {"sauvegarde_choix": "Continuer sans compte"}}, ensure_ascii=False)})
        assert status == 200
        assert posted["session"]["state"]["pacte"]["answers"]["sauvegarde_choix"] == "Continuer sans compte"
        assert posted["omar"]["step"] == "pacte"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
