from __future__ import annotations

import time
from typing import Any

TELEMETRY_SCHEMA = "oa.audit.telemetry_event.v1"
SESSION_METRICS_SCHEMA = "oa.audit.session_metrics.v1"
PRIVACY = {"pii": False, "contains_free_text": False, "retention": "product_analytics_90d"}
_ALLOWED_EVENTS = {
    "session_created",
    "button_displayed",
    "button_clicked",
    "step_validated",
    "public_research_started",
    "public_research_completed",
    "research_run",
    "report_created",
}
_ALLOWED_FIELDS = {
    "schema",
    "event",
    "at",
    "session_id",
    "tree_id",
    "tree_version",
    "step",
    "acte",
    "source",
    "is_tester",
    "telemetry_weight",
    "privacy",
    "entrypoint",
    "runtime_schema",
    "actions",
    "action_id",
    "intent",
    "rank",
    "stores_answer",
    "advances_step",
    "next_step",
    "completion_pct_after",
    "missing_count_before",
    "dry_run",
    "external_calls_attempted",
    "connectors",
    "consent_snapshot",
    "facts_count",
    "errors_count",
    "audit_id",
    "status_after",
    "sections_count",
    "documents_available",
    "share_available",
}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def is_tester_session(session: dict[str, Any]) -> bool:
    raw_runtime = session.get("runtime")
    runtime: dict[str, Any] = raw_runtime if isinstance(raw_runtime, dict) else {}
    if runtime.get("tester") or runtime.get("is_tester"):
        return True
    return bool(session.get("is_tester"))


def _base_event(session: dict[str, Any], event: str, *, source: str = "backend") -> dict[str, Any]:
    tester = is_tester_session(session)
    return {
        "schema": TELEMETRY_SCHEMA,
        "event": event,
        "at": _now(),
        "session_id": session.get("id"),
        "tree_id": session.get("tree_id"),
        "tree_version": session.get("tree_version"),
        "step": session.get("current_step"),
        "source": source,
        "is_tester": tester,
        "telemetry_weight": 0.0 if tester else 1.0,
        "privacy": dict(PRIVACY),
    }


def _clean_actions(actions: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    clean: list[dict[str, Any]] = []
    for index, action in enumerate(actions or [], start=1):
        if not isinstance(action, dict):
            continue
        action_id = str(action.get("id") or action.get("action_id") or action.get("intent") or "unknown").strip()
        intent = str(action.get("intent") or "").strip()
        clean.append(
            {
                "action_id": action_id[:80] or "unknown",
                "intent": intent[:80],
                "rank": int(action.get("rank") or index),
                "stores_answer": bool(action.get("stores_answer", intent in {"answer", "confirm", "continue", "deny"})),
                "advances_step": bool(action.get("advances_step", intent in {"confirm", "continue", "deny"})),
            }
        )
    return clean


def _normalize_consent_snapshot(plan: dict[str, Any] | None) -> dict[str, bool]:
    raw_consent = (plan or {}).get("consent_snapshot")
    consent = raw_consent if isinstance(raw_consent, dict) else {}
    raw_permissions = consent.get("permissions")
    permissions = raw_permissions if isinstance(raw_permissions, dict) else {}
    return {
        "public_web_search": bool(permissions.get("public_web_search")),
        "legal_registry_lookup": bool(permissions.get("legal_registry_lookup")),
        "social_media_lookup": bool(permissions.get("social_media_lookup")),
    }


def append_telemetry_event(session: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    raw_privacy = event.get("privacy")
    privacy: dict[str, Any] = raw_privacy if isinstance(raw_privacy, dict) else {}
    if privacy.get("pii") is True or privacy.get("contains_free_text") is True:
        raise ValueError("PII/free-text telemetry event rejected")
    event_name = str(event.get("event") or "").strip()
    if event_name not in _ALLOWED_EVENTS:
        raise ValueError("unsupported telemetry event")
    merged = {**_base_event(session, event_name, source=str(event.get("source") or "backend")), **event}
    merged["schema"] = TELEMETRY_SCHEMA
    merged["session_id"] = session.get("id")
    merged["privacy"] = dict(PRIVACY)
    merged["is_tester"] = is_tester_session(session) or bool(event.get("is_tester"))
    merged["telemetry_weight"] = 0.0 if merged["is_tester"] else float(event.get("telemetry_weight", 1.0) or 0.0)
    clean = {key: merged[key] for key in _ALLOWED_FIELDS if key in merged and merged[key] is not None}
    session.setdefault("metrics", {})["schema"] = SESSION_METRICS_SCHEMA
    session["metrics"].setdefault("telemetry_events", []).append(clean)
    return session


def make_session_created(session: dict[str, Any], *, entrypoint: str = "audit_page") -> dict[str, Any]:
    event = _base_event(session, "session_created")
    event.update({"entrypoint": entrypoint, "runtime_schema": session.get("schema")})
    return event


def make_button_displayed(session: dict[str, Any], actions: list[dict[str, Any]] | None) -> dict[str, Any]:
    event = _base_event(session, "button_displayed")
    event["actions"] = _clean_actions(actions)
    return event


def make_button_clicked(session: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    event = _base_event(session, "button_clicked", source="frontend")
    rank = payload.get("rank")
    event.update(
        {
            "step": str(payload.get("step") or session.get("current_step") or ""),
            "action_id": str(payload.get("action_id") or payload.get("intent") or "legacy_intent:unknown")[:80],
            "intent": str(payload.get("intent") or "")[:80],
            "rank": int(str(rank)) if str(rank or "").isdigit() else None,
            "stores_answer": bool(payload.get("stores_answer", False)),
            "advances_step": bool(payload.get("advances_step", False)),
        }
    )
    return event


def make_step_validated(session: dict[str, Any], *, step: str, next_step: str | None, completion: dict[str, Any]) -> dict[str, Any]:
    event = _base_event(session, "step_validated")
    event.update(
        {
            "step": step,
            "next_step": next_step,
            "completion_pct_after": ((session.get("completion") or {}).get("completion_pct") or 0),
            "missing_count_before": len(completion.get("missing_inputs") or completion.get("missing_fields") or []),
        }
    )
    return event


def make_public_research_started(session: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    event = _base_event(session, "public_research_started")
    event["dry_run"] = bool(dry_run)
    return event


def make_research_run(session: dict[str, Any], *, plan: dict[str, Any], result: dict[str, Any], dry_run: bool, external_calls_attempted: bool) -> dict[str, Any]:
    sources = plan.get("sources") if isinstance(plan.get("sources"), list) else []
    event = _base_event(session, "research_run")
    event.update(
        {
            "dry_run": bool(dry_run),
            "external_calls_attempted": bool(external_calls_attempted),
            "connectors": [
                {
                    "id": str(source.get("connector") or source.get("consent_key") or "unknown")[:80],
                    "attempted": bool(external_calls_attempted and source.get("status") == "authorized"),
                    "status": "ok" if source.get("status") == "authorized" and external_calls_attempted else str(source.get("status") or "skipped")[:40],
                }
                for source in sources[:8]
                if isinstance(source, dict)
            ],
            "consent_snapshot": _normalize_consent_snapshot(plan),
            "facts_count": len(result.get("facts") or []),
            "errors_count": len(result.get("fetch_errors") or []),
        }
    )
    return event


def make_public_research_completed(session: dict[str, Any], *, result: dict[str, Any], dry_run: bool, external_calls_attempted: bool) -> dict[str, Any]:
    event = _base_event(session, "public_research_completed")
    event.update(
        {
            "dry_run": bool(dry_run),
            "external_calls_attempted": bool(external_calls_attempted),
            "facts_count": len(result.get("facts") or []),
            "errors_count": len(result.get("fetch_errors") or []),
        }
    )
    return event


def make_report_created(session: dict[str, Any], *, audit: dict[str, Any], share: dict[str, Any] | None = None) -> dict[str, Any]:
    raw_report = audit.get("report")
    report: dict[str, Any] = raw_report if isinstance(raw_report, dict) else {}
    event = _base_event(session, "report_created")
    event.update(
        {
            "audit_id": audit.get("id"),
            "status_after": audit.get("status"),
            "sections_count": sum(1 for value in report.values() if value),
            "documents_available": True,
            "share_available": bool(share),
        }
    )
    return event
