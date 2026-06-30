from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auditbiz_store import AuditBizStore  # noqa: E402


def test_store_creates_resumable_session_with_messages(tmp_path: Path):
    store = AuditBizStore(tmp_path / "audit.sqlite3")
    session = store.create_session(sector_id="bakery", metadata={"channel": "test"})
    assert session["id"].startswith("auditbiz-")
    assert session["sector_id"] == "bakery"
    assert session["current_step"] == "conversation_preferences"

    store.add_message(session["id"], role="client", text="Je suis boulanger à Lille")
    resumed = store.get_session(session["id"])
    assert resumed is not None
    assert resumed["metadata"] == {"channel": "test"}
    assert resumed["messages"][0]["role"] == "client"
    assert "boulanger" in resumed["messages"][0]["text"]


def test_store_persists_facts_hypotheses_questions_and_feedback(tmp_path: Path):
    store = AuditBizStore(tmp_path / "audit.sqlite3")
    session = store.create_session(sector_id="bakery")
    sid = session["id"]

    fact_id = store.add_fact(
        sid,
        field="main_activity",
        value="Sandwicherie / snacking",
        source="user_declared",
        confidence=0.95,
        validated=True,
        step="business_model",
    )
    hypothesis_id = store.add_hypothesis(
        sid,
        hypothesis="Le rush du midi est probablement critique.",
        basis=["activité #1 = snacking", "zone = bureaux"],
        confidence=0.68,
    )
    question_row_id = store.record_question(
        sid,
        question_id="bakery_offer_rank",
        step="business_model",
        question="Classez vos activités par importance réelle pour le business.",
        metadata={"interaction": "rank"},
    )
    feedback_id = store.record_feedback(sid, question_id="bakery_offer_rank", signal="answered", details="réponse structurée")

    assert fact_id > 0
    assert hypothesis_id > 0
    assert question_row_id > 0
    assert feedback_id > 0

    resumed = store.get_session(sid)
    assert resumed is not None
    assert resumed["facts"][0]["validated"] is True
    assert resumed["facts"][0]["source"] == "user_declared"
    assert resumed["hypotheses"][0]["requires_validation"] is True
    assert resumed["hypotheses"][0]["basis"] == ["activité #1 = snacking", "zone = bureaux"]
    assert resumed["questions_asked"][0]["metadata"] == {"interaction": "rank"}
    assert resumed["feedback"][0]["signal"] == "answered"


def test_store_records_skips_and_rejects_invalid_confidence_or_signal(tmp_path: Path):
    store = AuditBizStore(tmp_path / "audit.sqlite3")
    sid = store.create_session(sector_id="bakery")["id"]
    store.record_question(sid, question_id="bakery_finance_1", step="finance_priorities", question="Question finance", outcome="skipped")
    store.record_feedback(sid, question_id="bakery_finance_1", signal="skipped", details="trop tôt")
    resumed = store.get_session(sid)
    assert resumed is not None
    assert resumed["questions_asked"][0]["outcome"] == "skipped"
    assert resumed["feedback"][0]["signal"] == "skipped"

    with pytest.raises(ValueError, match="confidence"):
        store.add_fact(sid, field="ca", value="999", source="user_declared", confidence=1.5, step="finance_priorities")
    with pytest.raises(ValueError, match="invalid feedback"):
        store.record_feedback(sid, question_id="x", signal="auto_learned")
