from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import audit_intelligence as ai  # noqa: E402


def test_sector_references_are_loadable_and_complete():
    refs = ai.load_sector_references()
    expected = {
        "generic_tpe",
        "bakery",
        "restaurant",
        "plumber",
        "florist",
        "lawyer",
        "wealth_manager",
        "marketing_freelance",
        "secretary_independent",
    }
    assert set(refs) >= expected
    for sector_id, ref in refs.items():
        assert ref["sector_id"] == sector_id
        assert ref["labels"]
        assert ref["important_dimensions"]
        assert "activity" in ref["question_blocks"]
        assert ref["risk_flags"]
        assert ref["benchmarks"]["automation_candidates"]


def test_priority_sector_files_are_strong_enough_for_personalized_local_audit():
    refs = ai.load_sector_references()
    for sector_id in ["bakery", "restaurant", "wealth_manager", "lawyer"]:
        ref = refs[sector_id]
        for key in ["core_parameters", "localized_research", "competitor_mapping"]:
            assert key in ref, sector_id
        dimensions = "\n".join(ref["important_dimensions"]).lower()
        for term in ["localisation", "âge", "chiffre", "concurrence"]:
            assert term in dimensions, (sector_id, term)
        assert ref["localized_research"]["consent_required"] is True
        assert ref["localized_research"]["facts_to_collect"]
        assert ref["competitor_mapping"]["direct"]
        assert ref["competitor_mapping"]["indirect"]
        for step in ["activity", "research", "pain", "tools", "risk", "opportunities", "autonomy", "validation"]:
            assert ref["question_blocks"].get(step), (sector_id, step)


def test_detect_sector_from_client_words():
    refs = ai.load_sector_references()
    assert ai.detect_sector("Je suis boulanger à Lille", refs) == "bakery"
    assert ai.detect_sector("cabinet avocat en droit social", refs) == "lawyer"
    assert ai.detect_sector("freelance marketing B2B", refs) == "marketing_freelance"
    assert ai.detect_sector("activité de conseil diverse", refs) == "generic_tpe"


def test_next_question_asks_missing_structuring_fields_before_validation():
    created = ai.create_session({"message": "Je suis boulanger"})
    session = created["session"]
    q = ai.next_question(session, "activity")
    assert q["sector_id"] == "bakery"
    assert "location" in q["missing_fields"]
    assert "taille" in q["question"].lower() or "où" in q["question"].lower()

    result = ai.validate_step(session, "activity")
    assert result["ok"] is False
    assert result["error"] == "step_incomplete"
    assert result["completion"]["completion_pct"] < 100


def test_activity_step_becomes_ready_after_precise_company_context():
    created = ai.create_session()
    session = created["session"]
    ai.add_message(
        session,
        "Je suis boulanger à Lille, boutique de 4 personnes, clients particuliers et entreprises, créée il y a 8 ans, environ 350k€ de CA.",
    )
    result = ai.validate_step(session, "activity")
    assert result["ok"] is True
    assert result["completion"]["ready"] is True
    assert session["sector_id"] == "bakery"
    assert "activity" in session["validated_steps"]
    assert session["current_step"] == "research"


def test_research_step_collects_public_sources_or_explicit_refusal_before_pain():
    created = ai.create_session()
    session = created["session"]
    ai.add_message(
        session,
        "Je suis boulanger à Lille, boutique de 4 personnes, clients particuliers et entreprises, créée il y a 8 ans, environ 350k€ de CA.",
    )
    assert ai.validate_step(session, "activity")["ok"] is True

    blocked = ai.validate_step(session, "research")
    assert blocked["ok"] is False
    assert "public_research_scope" in blocked["completion"]["missing_fields"]

    ai.add_message(session, "L'enseigne s'appelle Pain Nord, site https://pain-nord.example, j'autorise la recherche web publique.")
    result = ai.validate_step(session, "research")
    assert result["ok"] is True
    assert session["current_step"] == "pain"


def test_research_plan_is_sector_localized_and_consent_aware():
    created = ai.create_session()
    session = created["session"]
    ai.add_message(
        session,
        "Je suis avocat en droit social à Lyon, cabinet de 3 collaborateurs, créé il y a 6 ans, environ 420k€ de CA, clients PME et dirigeants.",
    )
    plan = ai.build_research_plan(
        session,
        {
            "consents": {"public_web_search": True, "legal_registry_lookup": True, "social_media_lookup": False},
            "company_public_name": "Cabinet Demo Avocats",
            "website": "https://cabinet-demo.example",
        },
    )
    assert plan["schema"] == "oa_audit_research_plan.v1"
    assert plan["sector_id"] == "lawyer"
    assert plan["safety"]["execute_external_calls"] is False
    assert any(src["status"] == "authorized" for src in plan["sources"])
    assert any(src["status"] == "refused" for src in plan["sources"])
    assert plan["competitors"]["direct"]
    assert plan["competitors"]["indirect"]
    assert any("secret professionnel" in guard.lower() for guard in plan["guardrails"])
    assert any(item["field"] == "company_age" and item["status"] == "present" for item in plan["context_fields"])


def test_conversation_starts_with_tone_and_mode_preferences():
    created = ai.create_session({"message": "Bonjour"})
    session = created["session"]
    q = created["omar"]
    assert session["current_step"] == "intro"
    assert q["step"] == "intro"
    assert "tutoie" in q["question"].lower() or "vouvoie" in q["question"].lower()
    assert any("mode" in item.lower() or "ton" in item.lower() for item in q["validation_criteria"])
    blocked = ai.validate_step(session, "intro")
    assert blocked["ok"] is False
    ai.add_message(session, "Vous pouvez me vouvoyer, je préfère un mode guidé avec questions courtes.")
    result = ai.validate_step(session, "intro")
    assert result["ok"] is True
    assert session["current_step"] == "activity"


def test_each_step_exposes_clear_validation_criteria():
    created = ai.create_session({"message": "Je suis restaurant à Lyon"})
    q = ai.next_question(created["session"], "activity")
    assert q["validation_criteria"]
    assert any("localisation" in item.lower() for item in q["validation_criteria"])
    for step in ["intro", "activity", "research", "pain", "tools", "risk", "opportunities", "autonomy", "validation"]:
        contract = ai.step_contract(step)
        assert contract["goal"]
        assert contract["validation_criteria"], step


def test_client_understanding_summarizes_declared_known_and_missing_context():
    created = ai.create_session()
    session = created["session"]
    ai.add_message(
        session,
        "Je suis restaurant italien à Lyon, 6 salariés, créé il y a 5 ans, 700k€ de CA, clients particuliers et entreprises.",
    )
    understanding = ai.build_client_understanding(session)
    assert understanding["sector_id"] == "restaurant"
    assert understanding["summary"].startswith("Voici ce que j’ai compris")
    assert "restaurant" in understanding["summary"].lower()
    assert any(item["field"] == "location" and item["status"] == "present" for item in understanding["context_fields"])
    assert understanding["next_step"] == "research"


def test_bakery_activity_options_and_address_context_support_micro_validation():
    options = ai.sector_activity_options("bakery")
    labels = [item["label"] for item in options]
    assert "Boulangerie" in labels
    assert "Pâtisserie" in labels
    assert "Viennoiseries" in labels
    assert "Sandwicherie / snacking" in labels

    hyper = ai.infer_location_context("12 rue de la République 69001 Lyon", "bakery")
    assert hyper["density"] == "hypercentre"
    assert any("passage" in clue.lower() for clue in hyper["business_implications"])

    peri = ai.infer_location_context("94 avenue de Flandre 59290 Wasquehal", "bakery")
    assert peri["density"] == "périurbain"
    assert any("voiture" in clue.lower() or "trajets" in clue.lower() for clue in peri["business_implications"])


def test_bakery_deep_facets_are_rich_and_explain_why_questions_matter():
    facets = ai.sector_deep_facets("bakery")
    facet_ids = {facet["id"] for facet in facets}
    for expected in ["savoir_faire", "emplacement", "production_offre", "stocks_achats", "equipe", "experience_client", "finance_pilotage", "reglementaire"]:
        assert expected in facet_ids
    assert len(facets) >= 10
    production = next(facet for facet in facets if facet["id"] == "production_offre")
    assert any("pertes" in q["question"].lower() or "invendus" in q["question"].lower() for q in production["questions"])
    assert all(q.get("why") for facet in facets for q in facet.get("questions", []))


def test_bakery_micro_questions_are_ranked_skippable_and_not_all_open():
    session = ai.create_session({"message": "Je suis boulangerie-pâtisserie à Lille, 5 salariés, créée il y a 6 ans, 500k€ de CA, clients quartier et bureaux."})["session"]
    questions = ai.recommend_micro_questions(session, "activity", limit=6)
    assert questions
    assert any(q["interaction"] == "rank" for q in questions)
    assert any(q["interaction"] == "choice" for q in questions)
    assert all(q["skip_allowed"] is True for q in questions)
    assert all(q["save_resume_allowed"] is True for q in questions)
    assert any("activité" in q["question"].lower() or "classez" in q["question"].lower() for q in questions)


def test_public_research_uses_only_authorized_sources_and_keeps_provenance():
    created = ai.create_session()
    session = created["session"]
    ai.add_message(
        session,
        "Je suis boulanger à Lille, boutique de 4 personnes, clients particuliers et entreprises, créée il y a 8 ans, environ 350k€ de CA.",
    )
    plan = ai.build_research_plan(
        session,
        {
            "company_public_name": "Pain Nord",
            "website": "https://pain-nord.example",
            "consents": {"public_web_search": True, "legal_registry_lookup": True, "social_media_lookup": False},
        },
    )
    research = ai.build_public_research_result(
        plan,
        fetched_pages=[{"url": "https://pain-nord.example", "title": "Pain Nord — Boulangerie artisanale Lille", "text": "Boulangerie artisanale à Lille. Commandes de pains et pâtisseries."}],
        registry_records=[{"source": "recherche-entreprises.api.gouv.fr", "name": "PAIN NORD", "siren": "123456789", "siret": "12345678900010", "activity": "Boulangerie", "city": "LILLE", "address": "12 RUE DES FOURS 59000 LILLE", "financial_summary": "CA 2024 publié : 350k€"}],
    )
    assert research["schema"] == "oa_public_research_result.v1"
    assert research["status"] == "partial"
    assert any(fact["provenance"] == "public_web_authorized" for fact in research["facts"])
    legal_facts = [fact for fact in research["facts"] if fact["provenance"] == "legal_registry_authorized"]
    assert legal_facts
    assert "12 RUE DES FOURS" in legal_facts[0]["value"]
    assert "123456789" not in legal_facts[0]["value"]
    assert "Est-ce que vous validez" in legal_facts[0]["validation_prompt"]
    assert all(fact["confidence"] <= 0.82 for fact in research["facts"])
    assert research["not_executed"]


def test_specialized_connectors_are_planned_by_sector():
    wm = ai.create_session({"message": "Je suis conseiller en gestion de patrimoine à Paris, solo, créé il y a 3 ans, 200k€ de CA, clients dirigeants."})["session"]
    wm_plan = ai.build_research_plan(wm, {"company_public_name": "Cabinet Patrimoine", "consents": {"legal_registry_lookup": True}})
    orias_sources = [source for source in wm_plan["sources"] if "ORIAS" in source["label"]]
    assert orias_sources
    assert orias_sources[0]["official_url"] == "https://www.orias.fr/home/showAdvancedSearch"
    assert orias_sources[0]["execution"] == "manual_review_link_prepared_connector_not_auto_executed"

    lawyer = ai.create_session({"message": "Je suis avocat à Lyon, cabinet de 2 associés, créé il y a 10 ans, 500k€ de CA, clients PME."})["session"]
    lawyer_plan = ai.build_research_plan(lawyer, {"company_public_name": "Cabinet Droit", "consents": {"legal_registry_lookup": True}})
    annuaire_sources = [source for source in lawyer_plan["sources"] if "barreau" in source["label"].lower() or "annuaire" in source["label"].lower()]
    assert annuaire_sources
    assert annuaire_sources[0]["official_url"] == "https://cnb.avocat.fr/annuaire-des-avocats-de-france"
    assert annuaire_sources[0]["execution"] == "manual_review_link_prepared_connector_not_auto_executed"


def test_specialized_connectors_are_visible_as_skipped_until_auto_execution_is_verified():
    session = ai.create_session({"message": "Je suis conseiller en gestion de patrimoine à Paris, solo, créé il y a 3 ans, 200k€ de CA, clients dirigeants."})["session"]
    plan = ai.build_research_plan(session, {"company_public_name": "Cabinet Patrimoine", "consents": {"legal_registry_lookup": True}})
    result = ai.build_public_research_result(
        plan,
        registry_records=[{"source": "recherche-entreprises.api.gouv.fr", "name": "CABINET PATRIMOINE", "siren": "111222333", "activity": "Conseil", "city": "PARIS"}],
    )
    assert any(fact["provenance"] == "legal_registry_authorized" for fact in result["facts"])
    skipped = [item for item in result["not_executed"] if item["reason"] == "specialized_connector_not_auto_executed"]
    assert skipped
    assert skipped[0]["official_url"] == "https://www.orias.fr/home/showAdvancedSearch"


def test_exports_include_markdown_and_linkedin_copy():
    exports = ai.build_exports({"report": {"title": "Première synthèse IA — Boulangerie", "summary": "priorité relances", "diagnostic": ["diagnostic"], "opportunities": ["opportunité"]}})
    assert exports["markdown"].startswith("# Première synthèse IA")
    assert "## Diagnostic" in exports["markdown"]
    assert "LinkedIn" not in exports["linkedin_text"]  # texte prêt à copier, pas un libellé UI
    assert exports["pdf_status"] == "pending_renderer"
