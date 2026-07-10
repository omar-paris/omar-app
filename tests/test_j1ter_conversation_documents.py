from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import audit_intelligence as ai  # noqa: E402


def _answer_and_validate(session: dict, step_id: str, answers: dict) -> dict:
    result = ai.add_message(session, json.dumps({"step_id": step_id, "answers": answers}, ensure_ascii=False))
    session = result["session"]
    validated = ai.validate_step(session, step_id)
    if not validated.get("ok") and validated.get("error") == "public_research_required":
        session.setdefault("public_research", []).append({
            "created_at": "2026-07-10T00:00:00Z",
            "result": {"schema": "oa_public_research_result.v1", "status": "partial", "facts": [{"label": "Nom", "value": "Boulangerie test"}]},
        })
        session.setdefault("state", {}).setdefault("public_sources_consent", {}).setdefault("answers", {})["public_research_validation"] = "Faits publics validés par le client"
        validated = ai.validate_step(session, step_id)
    assert validated["ok"], validated
    return validated["session"]


def _prepare_bakery_session_at_activity_model() -> dict:
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    session = _answer_and_validate(session, "pacte", {"sauvegarde_choix": "Continuer sans compte"})
    session = _answer_and_validate(session, "identity_public_context", {"nom_entreprise": "Boulangerie test Paris", "sirene_match": "À corriger"})
    session = _answer_and_validate(session, "public_sources_consent", {"consents": {"web_public": True, "sirene_detail": True}})
    return session


def _prepare_bakery_session_at_operations_week() -> dict:
    session = _prepare_bakery_session_at_activity_model()
    session = _answer_and_validate(
        session,
        "activity_business_model",
        {"recit_activite": "Boulangerie pâtisserie à Paris, vente en boutique", "type_clients": "Des particuliers", "taille_equipe": "6-20", "canaux_vente": "Sur place"},
    )
    session = _answer_and_validate(
        session,
        "person_and_goals",
        {"objectifs_racontes": "Je veux gagner du temps sur les demandes clients", "niveau_digital": "Ça va"},
    )
    return session


def test_j1ter_pacte_quick_start_records_required_answers_and_advances():
    created = ai.create_session({"tree_id": "business_tech"})
    session = created["session"]
    assert session["current_step"] == "pacte"

    result = ai.add_message(session, "Continuer sans compte")
    session = result["session"]
    validated = ai.validate_step(session, "pacte")

    assert validated["ok"], validated
    assert validated["session"]["current_step"] == "identity_public_context"
    answers = validated["session"]["state"]["pacte"]["answers"]
    assert answers["sauvegarde_choix"] == "Continuer sans compte"
    assert answers["tutoiement"] == "Restons au vous"
    assert answers["rythme"] == "Droit au but"


def test_j1ter_identity_free_text_records_company_name_and_advances_like_live_user():
    created = ai.create_session({"tree_id": "business_tech"})
    session = created["session"]
    session = _answer_and_validate(session, "pacte", {"sauvegarde_choix": "Continuer sans compte"})

    result = ai.add_message(session, "Boulangerie Dupont à Paris 11e")
    session = result["session"]
    answers = session["state"]["identity_public_context"]["answers"]

    assert answers["nom_entreprise"] == "Boulangerie Dupont à Paris 11e"
    validated = ai.validate_step(session, "identity_public_context")
    assert validated["ok"], validated
    assert validated["session"]["current_step"] == "public_sources_consent"


def test_j1ter_natural_free_text_flow_completes_and_generates_documents_like_live_smoke():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    natural_answers = [
        ("pacte", "Continuer sans compte"),
        ("identity_public_context", "Boulangerie Dupont à Paris 11e"),
        ("public_sources_consent", "Oui pour les sources publiques, pas de réseaux sociaux"),
        ("activity_business_model", "Boulangerie artisanale, vente boutique, particuliers du quartier, équipe de 6 personnes, sandwichs midi, pâtisseries le week-end"),
        ("person_and_goals", "Je dirige avec mon épouse, objectif gagner du temps sans perdre le contact client, niveau digital correct"),
        ("operations_week", "Tout : commandes fournisseurs, planning, caisse, demandes clients, factures"),
        ("admin_finance_purchasing", "Factures fournisseurs, achats farine beurre énergie, suivi marge manuel"),
        ("digital_tools_data", "Beaucoup Excel, caisse, Google Business, Instagram un peu"),
        ("risks_limits", "Ne pas envoyer de message automatique sans validation, garder le secret recette"),
        ("documents", "Oui, générez les documents"),
        ("diagnosis", "Oui"),
        ("recommendations", "Oui"),
        ("validation", "Oui je valide la synthèse finale"),
    ]

    for step_id, text in natural_answers:
        result = ai.add_message(session, text)
        session = result["session"]
        validated = ai.validate_step(session, step_id)
        if step_id == "public_sources_consent" and not validated.get("ok") and validated.get("error") == "public_research_required":
            session.setdefault("public_research", []).append({
                "created_at": "2026-07-10T00:00:00Z",
                "result": {"schema": "oa_public_research_result.v1", "status": "partial", "facts": [{"label": "Nom", "value": "Boulangerie Dupont"}]},
            })
            session = ai.add_message(session, "Valider les informations")["session"]
            validated = ai.validate_step(session, step_id)
        assert validated["ok"], {"step": step_id, "validated": validated, "state": session.get("state", {}).get(step_id)}
        session = validated["session"]

    assert session["status"] == "complete"
    assert session["current_step"] == "validation"
    assert session["completion"]["complete"] is True
    docs = ai.build_j1ter_documents(session)
    assert docs["schema"] == "oa.j1ter.documents.v1"
    assert docs["structured_audit"]["profile"]["sector_id"] == "bakery"
    assert docs["structured_audit"]["profile"]["company_name"] == "Boulangerie Dupont à Paris 11e"


def test_j1ter_public_research_consent_is_backend_state_not_front_fragile_yes():
    created = ai.create_session({"tree_id": "business_tech"})
    session = created["session"]

    session = _answer_and_validate(
        session,
        "pacte",
        {"sauvegarde_choix": "Continuer sans compte"},
    )
    session = _answer_and_validate(
        session,
        "identity_public_context",
        {"nom_entreprise": "Boulangerie test Paris", "sirene_match": "À corriger"},
    )

    assert session["current_step"] == "public_sources_consent"
    q = ai.next_question(session)
    assert q["step"] == "public_sources_consent"
    assert "sources" in q["question"].lower() or "autorise" in q["question"].lower()

    result = ai.add_message(session, "Oui")
    session = result["session"]

    assert session["current_step"] == "public_sources_consent"
    answers = session["state"]["public_sources_consent"]["answers"]
    assert answers["consents"]["web_public"] is True
    assert answers["consents"]["sirene_detail"] is True
    assert session["runtime"]["source_consent_status"] == "authorized"
    assert result["omar"]["step"] == "public_sources_consent"
    assert any(action["intent"] == "confirm" for action in result["omar"]["actions"])


def test_j1ter_authorized_public_research_must_be_attempted_before_next_step():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    session = _answer_and_validate(session, "pacte", {"sauvegarde_choix": "Continuer sans compte"})
    session = _answer_and_validate(
        session,
        "identity_public_context",
        {"nom_entreprise": "Boulangerie du Parc Monceau", "adresse": "51 Rue de Prony, 75017 Paris"},
    )

    result = ai.add_message(session, "Oui, recherche publique autorisée")
    session = result["session"]
    blocked = ai.validate_step(session, "public_sources_consent")

    assert blocked["ok"] is False
    assert blocked["error"] == "public_research_required"
    assert blocked["completion"]["ready"] is False
    assert blocked["completion"]["missing_inputs"] == ["public_research_validation"]
    assert "recherche publique" in blocked["omar"]["question"].lower()

    session.setdefault("public_research", []).append({
        "created_at": "2026-07-10T00:00:00Z",
        "result": {"schema": "oa_public_research_result.v1", "status": "partial", "facts": [{"label": "Nom", "value": "Boulangerie du Parc Monceau"}]},
    })
    session.setdefault("state", {}).setdefault("public_sources_consent", {}).setdefault("answers", {})["public_research_validation"] = "Faits publics validés par le client"
    validated = ai.validate_step(session, "public_sources_consent")

    assert validated["ok"] is True
    assert validated["session"]["current_step"] == "activity_business_model"


def test_j1ter_public_research_correction_does_not_validate_or_advance():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    session = _answer_and_validate(session, "pacte", {"sauvegarde_choix": "Continuer sans compte"})
    session = _answer_and_validate(
        session,
        "identity_public_context",
        {"nom_entreprise": "Boulangerie du Parc Monceau", "adresse": "51 Rue de Prony, 75017 Paris"},
    )

    session = ai.add_message(session, "Oui, recherche publique autorisée")["session"]
    session.setdefault("public_research", []).append({
        "created_at": "2026-07-10T00:00:00Z",
        "result": {"schema": "oa_public_research_result.v1", "status": "partial", "facts": [{"label": "Nom", "value": "Mauvaise boulangerie"}]},
    })
    session = ai.add_message(session, "Ce n'est pas la bonne entreprise, corriger avec Boulangerie du Parc Monceau")["session"]
    blocked = ai.validate_step(session, "public_sources_consent")

    assert blocked["ok"] is False
    assert blocked["error"] == "public_research_validation_required"
    assert session["current_step"] == "public_sources_consent"
    answers = session["state"]["public_sources_consent"]["answers"]
    assert answers["public_research_validation_status"] == "correction_requested"
    assert "public_research_validation" not in answers
    assert answers["public_research_correction"].startswith("Ce n'est pas la bonne entreprise")


def test_j1ter_broad_answer_tout_on_bakery_irritants_becomes_priority_not_repeat():
    session = _prepare_bakery_session_at_operations_week()
    assert session["current_step"] == "operations_week"
    before = ai.next_question(session)

    result = ai.add_message(session, "Tout")
    session = result["session"]
    after = result["omar"]

    answers = session["state"]["operations_week"]["answers"]
    assert answers["semaine"] == "Tout"
    assert answers["interpreted_intent"] == "answer_broad"
    assert answers["detected_irritants"] == ["horaires", "disponibilité", "commandes", "allergènes", "prix"]
    assert after["question"] != before["question"]
    assert "priorité" in after["question"].lower() or "premier" in after["question"].lower()
    assert [action["intent"] for action in after["actions"]] == ["prioritize", "clarify", "explain"]


def test_j1ter_vague_answer_beaucoup_on_tools_becomes_contextual_clarification():
    session = _prepare_bakery_session_at_operations_week()
    session = _answer_and_validate(
        session,
        "operations_week",
        {"semaine": "Demandes clients, commandes, horaires", "top_caillou": "Commandes"},
    )
    session = _answer_and_validate(
        session,
        "admin_finance_purchasing",
        {"admin_racontee": "Factures fournisseurs et caisse prennent du temps"},
    )
    assert session["current_step"] == "digital_tools_data"
    before = ai.next_question(session)

    result = ai.add_message(session, "Beaucoup")
    session = result["session"]
    after = result["omar"]

    answers = session["state"]["digital_tools_data"]["answers"]
    assert answers["outils_racontes"] == "Beaucoup"
    assert answers["interpreted_intent"] == "answer_vague"
    assert after["question"] != before["question"]
    assert "lesquels" in after["question"].lower() or "commencer simple" in after["question"].lower()
    assert any(action["intent"] == "choose_tool_family" for action in after["actions"])


def test_j1ter_business_tech_questions_use_native_vouvoiement_without_broken_conjugation():
    session = _prepare_bakery_session_at_operations_week()
    first_ops = ai.next_question(session)["question"]
    after_broad = ai.add_message(session, "Tout")["omar"]["question"]

    session = _answer_and_validate(
        session,
        "operations_week",
        {"semaine": "Demandes clients, commandes, horaires", "top_caillou": "Commandes"},
    )
    session = _answer_and_validate(
        session,
        "admin_finance_purchasing",
        {"admin_racontee": "Factures fournisseurs et caisse prennent du temps"},
    )
    first_tools = ai.next_question(session)["question"]
    after_vague = ai.add_message(session, "Beaucoup")["omar"]["question"]

    displayed = "\n".join([first_ops, after_broad, first_tools, after_vague])
    forbidden = ["vous fais", "vous veux", "vous aimerais", "vous utilises", "vous aurais", "vous as", "ressaisissezs", "ressaisissezsez", "ton ", " ta ", " tes "]
    for fragment in forbidden:
        assert fragment not in displayed, displayed
    assert "vous faites" in displayed or "votre" in displayed



def test_j1ter_documents_are_generated_from_structured_tree_outputs_not_raw_transcript():
    session = _prepare_bakery_session_at_operations_week()
    session = _answer_and_validate(
        session,
        "operations_week",
        {"semaine": "Commandes clients, horaires, allergènes", "top_caillou": "Commandes"},
    )
    session = _answer_and_validate(
        session,
        "admin_finance_purchasing",
        {"admin_racontee": "Factures fournisseurs et caisse prennent du temps"},
    )
    session = _answer_and_validate(
        session,
        "digital_tools_data",
        {"outils_racontes": "Téléphone, WhatsApp, caisse", "outils_confirm": ["Téléphone", "WhatsApp", "Caisse"]},
    )
    session = _answer_and_validate(
        session,
        "risks_limits",
        {"lignes_rouges": "Allergènes et paiements", "donnees_sensibles": ["Bancaire clients"], "validation_humaine": "Je valide tout au début"},
    )

    docs = ai.build_j1ter_documents(session)

    assert docs["schema"] == "oa.j1ter.documents.v1"
    assert docs["structured_audit"]["source"] == "audit_tree.business_tech.v1.yaml"
    assert docs["structured_audit"]["profile"]["sector_id"] == "bakery"
    assert "transcript" not in docs["manifest_business"].lower()
    assert "boulangerie" in docs["manifest_business"].lower()
    assert docs["owner_identity"]["digital_maturity"] == "Ça va"
    assert docs["agent_profile"]["human_gates"] == ["Je valide tout au début"]
    assert "Allergènes" in docs["local_constitution"]
    assert docs["open_questions"]


def test_j1ter_documents_endpoint_exposes_generated_artifacts(tmp_path):
    import json
    import os
    import socket
    import subprocess
    import time
    import urllib.request

    def free_port() -> int:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def request_json(method: str, url: str, payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

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
        for step_id, answers in [
            ("pacte", {"sauvegarde_choix": "Continuer sans compte"}),
            ("identity_public_context", {"nom_entreprise": "Boulangerie API Paris", "sirene_match": "À corriger"}),
            ("public_sources_consent", {"consents": {"web_public": True, "sirene_detail": True}}),
            ("activity_business_model", {"recit_activite": "Boulangerie pâtisserie à Paris", "type_clients": "Des particuliers", "taille_equipe": "6-20", "canaux_vente": "Sur place"}),
            ("person_and_goals", {"objectifs_racontes": "gagner du temps", "niveau_digital": "Ça va"}),
        ]:
            request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/message", {"message": json.dumps({"step_id": step_id, "answers": answers}, ensure_ascii=False)})
            if step_id == "public_sources_consent":
                status, research = request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/public-research", {"dry_run": True})
                assert status == 200
                assert research["research_result"]["schema"] == "oa_public_research_result.v1"
                request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/message", {"message": "Valider les informations"})
            request_json("POST", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/validate-step", {"step": step_id})
        status, docs = request_json("GET", f"http://127.0.0.1:{port}/api/audit-sessions/{sid}/documents")
        assert status == 200
        assert docs["ok"] is True
        assert docs["documents"]["schema"] == "oa.j1ter.documents.v1"
        assert docs["documents"]["structured_audit"]["profile"]["sector_id"] == "bakery"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
