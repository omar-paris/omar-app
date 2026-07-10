from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
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
        if step_id == "public_sources_consent" and not validation.get("ok") and validation.get("error") == "public_research_required":
            session.setdefault("public_research", []).append({
                "created_at": "2026-07-10T00:00:00Z",
                "result": {"schema": "oa_public_research_result.v1", "status": "partial", "facts": [{"value": "DU PAIN ET DES IDEES Paris"}]},
            })
            session.setdefault("state", {}).setdefault("public_sources_consent", {}).setdefault("answers", {})["public_research_validation"] = "Récit Omar validé par le client"
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


def test_business_tech_critique_feedback_does_not_validate_as_business_answer():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    session = ai.add_message(session, "Continuer sans compte")["session"]
    session = ai.validate_step(session, "pacte")["session"]
    session = ai.add_message(session, "La Fournée des Traditions 56 Rue Grande, 13390 Auriol")["session"]
    session = ai.validate_step(session, "identity_public_context")["session"]
    session = ai.add_message(session, "Non, on continue sans recherche")["session"]
    session = ai.validate_step(session, "public_sources_consent")["session"]
    assert "concurrence proche" in ai.next_question(session)["question"]

    critique = (
        "Il faut que tu me poses des vraies questions. Là tu n'as pas un vrai récit, "
        "tu dois regarder la ville d'Auriol, la concurrence directe, les horaires, "
        "le chiffre d'affaires et tu dois utiliser le vocabulaire artisan."
    )
    result = ai.add_message(session, critique)
    session = result["session"]

    answers = session["state"].get("activity_business_model", {}).get("answers", {})
    assert "recit_activite" not in answers
    assert session["feedback"][0]["kind"] == "product_critique"
    assert result["omar"]["interaction"] == "validation_card"
    assert "je vous ai mal accompagné" in result["omar"]["question"].lower()

    validation = ai.validate_step(session, "activity_business_model")
    assert validation["ok"] is False
    assert validation["error"] == "step_incomplete"
    assert "recit_activite" in validation["completion"]["missing_inputs"]


def test_business_tech_product_feedback_after_answer_blocks_auto_validation_until_repaired():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    for text, step in [
        ("Continuer sans compte", "pacte"),
        ("La Fournée des Traditions 56 Rue Grande, 13390 Auriol", "identity_public_context"),
        ("Non, on continue sans recherche", "public_sources_consent"),
    ]:
        session = ai.add_message(session, text)["session"]
        session = ai.validate_step(session, step)["session"]

    session = ai.add_message(session, "Boulangerie-pâtisserie de quartier à Auriol, 4 personnes, boutique et commandes spéciales.")["session"]
    assert ai.validate_step(session, "activity_business_model")["ok"] is True
    # Rewind current step to simulate the live bug: a valid business answer exists,
    # then the user critiques the flow; validation must not silently pass.
    session["current_step"] = "activity_business_model"
    session = ai.add_message(session, "Tes questions sont désagréables, tu passes à la question suivante et le mot récit ne va pas.")["session"]
    validation = ai.validate_step(session, "activity_business_model")
    assert validation["ok"] is False
    assert validation["error"] == "product_feedback_unresolved"
    assert validation["completion"]["blocked_by_feedback"] is True

    session = ai.add_message(session, "Réponse métier réparée : boulangerie-pâtisserie à Auriol, 4 personnes, CA modeste, flux quartier, commandes week-end.")["session"]
    assert ai.validate_step(session, "activity_business_model")["ok"] is True


def test_business_tech_replays_alex_live_transcript_as_feedback_not_completed_session():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    transcript = [
        ("Continuer sans compte", "pacte"),
        ("La Fournée des Traditions 56 Rue Grande, 13390 Auriol", "identity_public_context"),
        ("Oui, recherche publique autorisée", "public_sources_consent"),
        ("Valider les informations publiques et le récit Omar", "public_sources_consent"),
        ("Il faut que ici tu me poses des questions, tu n'as pas un vrai récit, tu dois regarder la ville d'Auriol, la concurrence directe, les horaires, l'équipe et le chiffre d'affaires.", "activity_business_model"),
        ("Le problème c'est que là tu me dis et vous là dedans, tu devrais simplement faire une phrase pour résumer et enchaîner en transition logique.", "activity_business_model"),
        ("C'est horrible, tu dis cette boîte, je suis un artisan, il faut vraiment que tu utilises le vocabulaire de notre cible.", "activity_business_model"),
    ]
    for text, expected_step in transcript:
        assert session["current_step"] == expected_step
        session = ai.add_message(session, text)["session"]
        validation = ai.validate_step(session, expected_step)
        if expected_step == "public_sources_consent" and validation.get("error") == "public_research_required":
            session.setdefault("public_research", []).append({
                "created_at": "2026-07-10T00:00:00Z",
                "result": {"schema": "oa_public_research_result.v1", "status": "not_started", "facts": [], "not_executed": [{"label": "SIRENE/SIRET", "reason": "not_fetched_yet"}]},
            })
            validation = ai.validate_step(session, expected_step)
        if validation.get("ok"):
            session = validation["session"]

    assert session["status"] == "running"
    assert session["current_step"] == "activity_business_model"
    assert "activity_business_model" not in session.get("validated_steps", [])
    assert len(session.get("feedback", [])) >= 3
    assert session["state"].get("activity_business_model", {}).get("answers", {}) == {}


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

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/report",
            data=json.dumps({"activity": "Boulangerie", "repetitive_tasks": "demandes clients"}).encode("utf-8"),
            method="POST",
            headers={"content-type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("incomplete business_tech session generated a fake report")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 409
            assert body["ok"] is False
            assert body["error"] == "audit_session_incomplete"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
