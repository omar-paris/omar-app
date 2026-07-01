from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from auditbiz_schema import AuditQuestion, SectorPack, load_sector_pack

LEGACY_STEP_TO_AUDITBIZ = {
    "intro": "conversation_preferences",
    "activity": "identity_context",
    "research": "sources",
    "pain": "operations",
    "tools": "operations",
    "risk": "risks_guardrails",
    "opportunities": "ai_opportunities",
    "autonomy": "ai_opportunities",
    "validation": "final_validation",
}

AUDITBIZ_TO_LEGACY_STEP = {value: key for key, value in LEGACY_STEP_TO_AUDITBIZ.items()}
AUDITBIZ_TO_LEGACY_STEP.update({"business_model": "activity", "clients_market": "research", "finance_priorities": "pain"})

STEP_ORDER = [
    "conversation_preferences",
    "identity_context",
    "sources",
    "business_model",
    "operations",
    "clients_market",
    "finance_priorities",
    "risks_guardrails",
    "ai_opportunities",
    "final_validation",
]

REPORT_IMPACT_WEIGHT = {"low": 1.0, "medium": 2.0, "high": 3.5}


@dataclass(frozen=True)
class ScoredQuestion:
    question: AuditQuestion
    score: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = self.question.to_dict()
        data.update({"score": round(self.score, 2), "score_reasons": list(self.reasons)})
        return data


def normalize_step(step: str | None) -> str:
    raw = str(step or "identity_context").strip()
    return LEGACY_STEP_TO_AUDITBIZ.get(raw, raw if raw in STEP_ORDER else "identity_context")


def _session_text(session: dict[str, Any]) -> str:
    parts: list[str] = []
    for msg in session.get("messages", []) or []:
        if isinstance(msg, dict):
            parts.append(str(msg.get("text") or ""))
        else:
            parts.append(str(msg))
    for fact in session.get("facts", []) or []:
        if isinstance(fact, dict):
            parts.append(str(fact.get("field") or ""))
            parts.append(str(fact.get("value") or ""))
    for value in (session.get("answers") or {}).values() if isinstance(session.get("answers"), dict) else []:
        parts.append(str(value))
    return "\n".join(parts).casefold()


def _asked_question_ids(session: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for item in session.get("questions_asked", []) or []:
        if isinstance(item, dict):
            ids.add(str(item.get("question_id") or item.get("id") or ""))
    for item in session.get("asked_questions", []) or []:
        if isinstance(item, dict):
            ids.add(str(item.get("question_id") or item.get("id") or ""))
    return {x for x in ids if x}


def _feedback_by_question(session: dict[str, Any]) -> dict[str, list[str]]:
    feedback: dict[str, list[str]] = {}
    for item in session.get("feedback", []) or []:
        if not isinstance(item, dict):
            continue
        qid = str(item.get("question_id") or "")
        signal = str(item.get("signal") or "")
        if qid and signal:
            feedback.setdefault(qid, []).append(signal)
    return feedback


def _missing_signal_bonus(question: AuditQuestion, text: str) -> tuple[float, str | None]:
    missing = [signal for signal in question.expected_signal if signal.casefold() not in text]
    if missing:
        return min(3.0, 0.75 * len(missing)), "comble un signal manquant"
    return 0.0, None


def score_question(question: AuditQuestion, session: dict[str, Any], *, target_step: str) -> ScoredQuestion:
    score = REPORT_IMPACT_WEIGHT.get(question.report_impact, 2.0)
    reasons: list[str] = [f"impact rapport {question.report_impact}"]
    text = _session_text(session)
    asked = _asked_question_ids(session)
    feedback = _feedback_by_question(session)

    if question.step == target_step:
        score += 4.0
        reasons.append("étape courante")
    else:
        score -= 2.0

    bonus, reason = _missing_signal_bonus(question, text)
    score += bonus
    if reason:
        reasons.append(reason)

    if question.id in asked:
        score -= 7.0
        reasons.append("déjà posée")

    signals = feedback.get(question.id, [])
    if signals.count("skipped"):
        score -= 4.0 * signals.count("skipped")
        reasons.append("déjà passée par le client")
    if "too_deep" in signals:
        score -= 3.0
        reasons.append("jugée trop profonde")
    if "useful" in signals or "answered" in signals:
        score += 0.8
        reasons.append("signal utile historique")

    trust_markers = ["mode guid", "vouvoi", "tutoi", "synthèse", "synthese", "conversation libre"]
    trust_context = any(marker in text for marker in trust_markers)
    business_context = any(marker in text for marker in ["boulanger", "boutique", "équipe", "equipe", "client", "lille", "paris", "lyon"])
    if question.sensitivity == "sensitive" and not (trust_context and business_context):
        score -= 5.0
        reasons.append("sensible trop tôt")
    elif question.sensitivity == "sensitive":
        score -= 0.75
        reasons.append("sensible à manier prudemment")

    fatigue = int(session.get("fatigue", 0) or 0)
    if fatigue >= 3 and question.interaction == "open":
        score -= 2.0
        reasons.append("fatigue: question ouverte pénalisée")
    if fatigue >= 3 and question.interaction in {"choice", "rank", "confirm"}:
        score += 0.75
        reasons.append("fatigue: réponse rapide favorisée")

    if question.interaction in {"choice", "rank"}:
        score += 0.4
        reasons.append("réponse rapide possible")

    return ScoredQuestion(question=question, score=score, reasons=tuple(reasons))


def candidate_questions(session: dict[str, Any], step: str | None = None, *, sector_id: str | None = None, pack: SectorPack | None = None) -> list[AuditQuestion]:
    target_step = normalize_step(step or session.get("current_step"))
    resolved_sector = sector_id or str(session.get("sector_id") or "bakery")
    try:
        pack = pack or load_sector_pack(resolved_sector)
    except Exception:
        pack = load_sector_pack("bakery")
    questions = pack.questions_for_step(target_step)
    if not questions and target_step == "identity_context":
        questions = pack.questions_for_step("business_model")
    return questions


def choose_next_question(session: dict[str, Any], step: str | None = None, *, sector_id: str | None = None, limit: int = 5) -> dict[str, Any]:
    target_step = normalize_step(step or session.get("current_step"))
    resolved_sector = sector_id or str(session.get("sector_id") or "bakery")
    pack = load_sector_pack(resolved_sector if resolved_sector == "bakery" else "bakery")
    candidates = candidate_questions(session, target_step, sector_id=pack.sector_id, pack=pack)
    scored = sorted((score_question(q, session, target_step=target_step) for q in candidates), key=lambda item: item.score, reverse=True)
    if not scored:
        raise ValueError(f"no questions for step {target_step}")
    best = scored[0]
    payload = best.to_dict()
    payload.update(
        {
            "schema": "auditbizia_next_question.v1",
            "sector_id": pack.sector_id,
            "sector_label": pack.label,
            "step": target_step,
            "legacy_step": AUDITBIZ_TO_LEGACY_STEP.get(target_step, target_step),
            "why_available": bool(best.question.why),
            "skip_allowed": best.question.skip_allowed,
            "save_resume_allowed": best.question.save_resume_allowed,
            "feedback_prompt": "Cette question était-elle utile, trop loin, mal posée, ou à approfondir ?",
            "alternatives": [item.to_dict() for item in scored[1:limit]],
        }
    )
    return payload
