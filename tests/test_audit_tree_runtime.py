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



def test_business_tech_contextual_free_text_maps_consultant_side_steps():
    session = ai.create_session({"tree_id": "business_tech"})["session"]

    session["current_step"] = "marketing_sales"
    session = ai.add_message(session, "Les clients viennent par vitrine, bouche-à-oreille, Google Business et Instagram. On perd des demandes quand on répond trop tard.")["session"]
    validation = ai.validate_step(session, "marketing_sales")
    assert validation["ok"], validation

    session["current_step"] = "hr_team_organization"
    session = ai.add_message(session, "Planning papier, deux vendeurs, un apprenti, consignes dans WhatsApp, remplacements parfois confus.")["session"]
    validation = ai.validate_step(session, "hr_team_organization")
    assert validation["ok"], validation

    marketing = session["state"]["marketing_sales"]["answers"]
    assert marketing["parcours_client_raconte"].startswith("Les clients viennent")
    assert marketing["perte_identifiee"] == "Je réponds trop tard"
    team = session["state"]["hr_team_organization"]["answers"]
    assert team["equipe_racontee"].startswith("Planning papier")
    assert team["friction_equipe"] == "Plannings"



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


def test_business_tech_next_question_exposes_agent_frame_and_business_analysis():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    for text, step in [
        ("Continuer sans compte", "pacte"),
        ("La Fournée des Traditions 56 Rue Grande, 13390 Auriol", "identity_public_context"),
        ("Non, on continue sans recherche", "public_sources_consent"),
    ]:
        session = ai.add_message(session, text)["session"]
        session = ai.validate_step(session, step)["session"]

    q = ai.next_question(session)
    frame = q["agent_frame"]
    assert frame["schema"] == "oa.audit-agent-frame.v1"
    assert frame["mission"]["primary_goal"].startswith("Comprendre")
    assert frame["step"]["id"] == "activity_business_model"
    assert frame["step"]["objective"]
    assert frame["evidence"]["declared_client"]
    assert "La Fournée des Traditions" in " ".join(frame["evidence"]["declared_client"])
    assert frame["analysis"]["sector_id"] == "bakery"
    assert frame["analysis"]["useful_axes"]
    assert {"question", "why", "facet_id"} <= set(frame["next_best_question"])
    assert frame["controls"] == ["Pourquoi cette question", "Passer cette question", "Enregistrer et reprendre plus tard", "Corriger ce que j’ai compris"]
    assert frame["guardrails"]["paid_actions"] == "none"
    assert frame["guardrails"]["external_actions"] == "none_without_explicit_human_go"
    assert "agent_frame" in q


def _complete_bakery_consulting_session() -> dict:
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    answers = {
        "pacte": "Continuer sans compte",
        "identity_public_context": "La Fournée des Traditions, 56 Rue Grande, 13390 Auriol",
        "public_sources_consent": "Non, on continue sans recherche",
        "activity_business_model": "Boulangerie-pâtisserie artisanale à Auriol, 4 personnes, boutique de quartier, commandes week-end et clients particuliers.",
        "person_and_goals": "Je veux libérer du temps, mieux piloter la marge et préparer une transmission plus sereine. J'ai déjà testé l'IA un peu.",
        "operations_week": "Les appels pour horaires, commandes, allergènes et disponibilités prennent 4 h par semaine, surtout avant week-end.",
        "admin_finance_purchasing": "Achats farine beurre emballages, factures fournisseur et marge par famille produit sont suivis surtout sur Excel.",
        "digital_tools_data": "Téléphone, WhatsApp, caisse, Excel, fiche Google et Instagram ; on recopie les commandes à la main.",
        "risks_limits": "Allergènes, prix, acomptes et avis négatifs doivent rester validés par un humain.",
    }
    for step, text in answers.items():
        session = ai.add_message(session, text)["session"]
        validation = ai.validate_step(session, step)
        assert validation["ok"], validation
        session = validation["session"]
    return session


def test_business_tech_build_agent_brief_uses_all_acquired_data_without_mixing_sources():
    session = _complete_bakery_consulting_session()

    brief = ai.build_agent_brief(session)
    assert brief["schema"] == "oa.omar-agent-brief.v1"
    assert brief["sector_id"] == "bakery"
    assert brief["company_context"]["identity"]
    assert "La Fournée" in brief["company_context"]["identity"]
    assert brief["evidence_contract"]["verified_public"] == []
    assert any("allerg" in item.casefold() for item in brief["guardrails"]["human_validation_required"])
    assert len(brief["analysis"]["recommendations"])
    assert len(brief["analysis"]["unknowns"])
    assert all(item["origin"] in {"declared_client", "omar_hypothesis"} for item in brief["analysis"]["recommendations"])
    assert brief["agent_operating_contract"]["mode"] == "draft_agent_after_audit"
    assert brief["agent_operating_contract"]["allowed_actions"]
    assert brief["agent_operating_contract"]["forbidden_actions"]


def test_business_tech_premium_consulting_report_follows_deep_search_appomar_contract():
    session = _complete_bakery_consulting_session()

    report = ai.build_premium_consulting_report(session)

    assert report["schema"] == "oa.premium-consulting-report.v1"
    assert report["method"]["reference_doc"].endswith("2026-07-08-audit-business-tech-appomar-deep-search-result.md")
    assert {"France Num", "Bpifrance", "ANSSI", "CNIL"} <= set(report["method"]["frameworks"])
    assert [d["id"] for d in report["diagnostic_dimensions"]] == [
        "identity_official_context",
        "business_model_value_proposition",
        "operations_week_mental_load",
        "cyber_hygiene_minimal",
        "digital_ai_maturity_subjective",
        "customer_acquisition_journey",
        "admin_finance_e_invoicing",
        "team_organization",
        "data_ai_readiness_objective",
    ]
    assert all({"id", "integration_level", "target_indicators", "maturity_level", "evidence", "implication", "next_test"} <= set(d) for d in report["diagnostic_dimensions"])
    assert report["scores"]["schema"] == "oa.audit-scores.explainable.v1"
    assert set(report["scores"]["indices"]) == {"cyber_hygiene", "operational_friction", "digital_ai_maturity"}
    assert all({"score", "why", "limits", "how_to_improve"} <= set(index) for index in report["scores"]["indices"].values())
    assert report["traceability"]["schema"] == "oa.audit-traceability.dvfh.v1"
    assert report["traceability"]["declared_client"]
    assert report["traceability"]["verified_public"] == []
    assert report["traceability"]["hypotheses_omar"]
    assert report["traceability"]["unknowns_or_future_checks"]
    assert len(report["final_report_outline"]) == 17
    assert len(report["final_report_sections"]) == 17
    assert [section["title"] for section in report["final_report_sections"]] == report["final_report_outline"]
    assert all({"id", "title", "status", "source_buckets", "content", "evidence", "limits", "next_action"} <= set(section) for section in report["final_report_sections"])
    assert any(section["id"] == "automation_matrix" and section["content"].get("items") for section in report["final_report_sections"])
    automation_text = json.dumps(next(section for section in report["final_report_sections"] if section["id"] == "automation_matrix"), ensure_ascii=False).casefold()
    assert "commande" in automation_text or "allerg" in automation_text or "avis google" in automation_text
    assert any(section["id"] == "quick_wins_7_days" and len(section["content"].get("actions", [])) >= 3 for section in report["final_report_sections"])
    assert report["conversation_depth_contract"]["schema"] == "oa.audit-step-depth-contract.v1"
    assert len(report["conversation_depth_contract"]["steps"]) >= 14
    assert all({"step_id", "goal", "expected_evidence", "validation_criteria", "repair_behaviors", "report_impact"} <= set(step) for step in report["conversation_depth_contract"]["steps"])
    assert report["agent_profile"]["status"] == "draft_pending_human_validation"
    assert report["agent_profile"]["mission"]["success_criteria"]
    assert report["devis_model"]["non_intrusive"] is True
    assert all({"reference", "recommendation_source", "proof_required", "benefit_expected", "prerequisites", "limits", "human_gate", "status"} <= set(item) for item in report["devis_model"]["line_items"])
    narrative = report["executive_narrative"]
    assert isinstance(narrative, str)
    assert len(narrative.split("\n\n")) >= 5
    assert "La Fournée" in narrative
    assert "France Num" in narrative
    assert "ANSSI" in narrative
    assert "CNIL" in narrative
    assert "facturation électronique" in narrative
    assert "déclar" in narrative.casefold()
    assert "hypothèse" in narrative.casefold()
    assert "allerg" in narrative.casefold()
    assert "- " not in narrative

    docs = ai.build_j1ter_documents(session)
    assert docs["premium_consulting_report"]["schema"] == "oa.premium-consulting-report.v1"
    assert "RAPPORT DE DIAGNOSTIC BUSINESS & TECH" in docs["premium_consulting_markdown"]


def test_business_tech_final_client_document_bundle_has_six_presentable_documents():
    session = _complete_bakery_consulting_session()

    bundle = ai.build_final_client_document_bundle(session)

    assert bundle["schema"] == "oa.final-client-document-bundle.v1"
    assert [doc["id"] for doc in bundle["documents"]] == [
        "audit_report",
        "business_manifesto",
        "local_constitution",
        "agent_profile",
        "action_plan_and_devis",
        "open_questions_and_evidence",
    ]
    assert all({"id", "title", "status", "audience", "markdown", "source_refs", "next_action"} <= set(doc) for doc in bundle["documents"])
    assert all(len(doc["markdown"].split()) >= 80 for doc in bundle["documents"])
    assert all("à préciser" not in doc["markdown"].casefold() for doc in bundle["documents"][:5])
    assert "manifeste" in bundle["documents"][1]["title"].casefold()
    assert "constitution" in bundle["documents"][2]["title"].casefold()
    assert "validation humaine" in bundle["documents"][2]["markdown"].casefold()
    assert "devis" in bundle["documents"][4]["title"].casefold()
    assert bundle["quality_gate"]["ready_for_client_review"] is True
    assert bundle["quality_gate"]["document_count"] == 6


def test_business_tech_priority_sectors_have_consultant_micro_questions_and_artifact_hooks():
    cases = {
        "bakery": "Boulangerie-pâtisserie de quartier, commandes week-end, allergènes et avis Google.",
        "restaurant": "Restaurant bistronomique avec réservations, no-show, menu allergènes et avis publics.",
        "lawyer": "Cabinet avocat droit social, dossiers confidentiels, relances clients et secret professionnel.",
        "plumber": "Plombier chauffagiste, urgences, devis, planning tournées et avis Google.",
        "secretary_independent": "Secrétaire indépendante, appels entrants, relances administratives, facturation clients.",
        "wealth_manager": "Conseiller en gestion de patrimoine, prospects, conformité, documents sensibles et rendez-vous.",
    }
    expected_terms = {
        "bakery": ["allerg", "commande", "avis"],
        "restaurant": ["réservation", "allerg", "no-show"],
        "lawyer": ["secret", "dossier", "juridique"],
        "plumber": ["urgence", "devis", "planning"],
        "secretary_independent": ["administr", "relance", "appel"],
        "wealth_manager": ["patrimoine", "conform", "rendez-vous"],
    }
    for sector_id, activity in cases.items():
        session = ai.create_session({"tree_id": "business_tech"})["session"]
        session["sector_id"] = sector_id
        session = ai.add_message(session, json.dumps({"step_id": "activity_business_model", "answers": {"recit_activite": activity, "type_clients": "Les deux", "taille_equipe": "2-5", "canaux_vente": "Google/web"}}, ensure_ascii=False))["session"]
        questions = ai.recommend_micro_questions(session, "pain", limit=4)
        text = json.dumps(questions, ensure_ascii=False).casefold()
        assert len(questions) >= 3, {"sector": sector_id, "questions": questions}
        assert any(term in text for term in expected_terms[sector_id]), {"sector": sector_id, "text": text}
        assert all({"question", "why", "facet_id", "follow_up", "skip_allowed", "save_resume_allowed"} <= set(q) for q in questions)
        assert len({q["question"] for q in questions}) == len(questions)


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


def test_business_tech_rejects_weak_confused_or_hostile_inputs_instead_of_autocompleting_steps():
    session = ai.create_session({"tree_id": "business_tech"})["session"]
    for text, step in [
        ("Continuer sans compte", "pacte"),
        ("Boulangerie B&B 2 Bd du Bois le Prêtre", "identity_public_context"),
        ("Non, on continue sans recherche", "public_sources_consent"),
    ]:
        session = ai.add_message(session, text)["session"]
        validated = ai.validate_step(session, step)
        assert validated["ok"], validated
        session = validated["session"]

    weak_cases = [
        ("activity_business_model", "oui", "recit_activite"),
        ("person_and_goals", "heu tu me posees une question ou c'est une affirmation?", "objectifs_racontes"),
        ("operations_week", "je ne sais pas", "semaine"),
        ("admin_finance_purchasing", "je ne sais pas, tu m'aides à trouver", "admin_racontee"),
        ("digital_tools_data", "a la la la", "outils_racontes"),
        ("risks_limits", "tu valides tout tout seul ?", "lignes_rouges"),
        ("diagnosis", "n'importe quoi", "swot_reaction"),
    ]
    for step, text, required_field in weak_cases:
        isolated = json.loads(json.dumps(session, ensure_ascii=False))
        isolated["current_step"] = step
        after_message = ai.add_message(isolated, text)
        isolated = after_message["session"]
        validation = ai.validate_step(isolated, step)
        assert validation["ok"] is False, {"step": step, "text": text, "validation": validation, "answers": isolated.get("state", {}).get(step)}
        assert validation["error"] in {"step_incomplete", "product_feedback_unresolved", "answer_not_actionable"}
        assert required_field in validation["completion"]["missing_inputs"] or validation["completion"].get("blocked_by_feedback") is True
        assert step not in isolated.get("validated_steps", [])


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
