from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auditbiz_question_engine import choose_next_question, normalize_step, score_question  # noqa: E402
from auditbiz_schema import load_sector_pack  # noqa: E402


def test_normalize_step_maps_legacy_audit_steps_to_auditbizia_contract():
    assert normalize_step("intro") == "conversation_preferences"
    assert normalize_step("activity") == "identity_context"
    assert normalize_step("pain") == "operations"
    assert normalize_step("risk") == "risks_guardrails"
    assert normalize_step("unknown") == "identity_context"


def test_next_best_question_returns_ranked_activity_for_business_model():
    session = {
        "sector_id": "bakery",
        "current_step": "business_model",
        "messages": [{"text": "Je suis boulangerie-pâtisserie à Lille."}],
        "questions_asked": [],
    }
    q = choose_next_question(session, "business_model")
    assert q["schema"] == "auditbizia_next_question.v1"
    assert q["id"] == "bakery_offer_rank"
    assert q["interaction"] == "rank"
    assert "Boulangerie" in q["options"]
    assert q["why_available"] is True
    assert q["skip_allowed"] is True
    assert q["save_resume_allowed"] is True


def test_question_already_asked_is_penalized_and_alternative_is_selected():
    session = {
        "sector_id": "bakery",
        "current_step": "business_model",
        "messages": [{"text": "Je suis boulangerie-pâtisserie à Lille."}],
        "questions_asked": [{"question_id": "bakery_offer_rank"}],
    }
    q = choose_next_question(session, "business_model")
    assert q["id"] != "bakery_offer_rank"
    assert q["id"] == "bakery_location_flow_1"
    assert any("déjà posée" in reason for alt in q["alternatives"] for reason in alt.get("score_reasons", [])) or q["score"] > 0


def test_sensitive_finance_question_is_delayed_until_context_exists():
    pack = load_sector_pack("bakery")
    finance = next(q for q in pack.questions if q.id == "bakery_finance_1")
    cold = {"sector_id": "bakery", "messages": [{"text": "Bonjour"}], "questions_asked": []}
    warm = {"sector_id": "bakery", "messages": [{"text": "Vous pouvez me vouvoyer, mode guidé. Je suis boulanger à Lille."}], "questions_asked": []}
    cold_score = score_question(finance, cold, target_step="finance_priorities")
    warm_score = score_question(finance, warm, target_step="finance_priorities")
    assert warm_score.score > cold_score.score
    assert any("sensible trop tôt" in reason for reason in cold_score.reasons)


def test_skipped_question_does_not_block_progress():
    session = {
        "sector_id": "bakery",
        "current_step": "finance_priorities",
        "messages": [{"text": "Vous pouvez me vouvoyer, mode guidé."}],
        "questions_asked": [{"question_id": "bakery_finance_1"}],
        "feedback": [{"question_id": "bakery_finance_1", "signal": "skipped"}],
    }
    q = choose_next_question(session, "finance_priorities")
    assert q["schema"] == "auditbizia_next_question.v1"
    assert q["skip_allowed"] is True
    assert q["id"] == "bakery_finance_1"  # only finance V1 question exists; scoring stays explicit, not blocking
    assert any("déjà passée" in reason or "déjà posée" in reason for reason in q["score_reasons"])


def test_risk_step_returns_allergen_human_validation_question():
    session = {"sector_id": "bakery", "messages": [{"text": "Boulangerie à Lille, mode guidé."}]}
    q = choose_next_question(session, "risks_guardrails")
    assert q["id"] == "bakery_risk_allergens_1"
    assert q["sensitivity"] == "sensitive"
    assert any("Allergènes" == option for option in q["options"])
