#!/usr/bin/env python3
"""Validate AppOmar audit conversation tree/path contracts.

This is a static + lightweight runtime guard. It does not prove UX quality, but it
catches the dangerous class of bugs Alex hit: buttons or branches that look
available yet lead to no handler, no state transition, or skipped mandatory gates.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "src" / "audit_tree.business_tech.v1.yaml"
FRONT = ROOT / "pages-app" / "audit.html"
SRC = ROOT / "src" / "audit_intelligence.py"

REQUIRED_FRONT_INTENTS = {
    "save",
    "confirm",
    "explain",
    "help",
    "value",
    "challenge",
    "focus",
    "unknown",
    "run_public_research",
    "confirm_public_research",
    "deny",
    "modify",
}

CRITICAL_STEPS = [
    "pacte",
    "identity_public_context",
    "public_sources_consent",
    "activity_business_model",
    "person_and_goals",
    "operations_week",
    "admin_finance_purchasing",
    "digital_tools_data",
    "risks_limits",
    "diagnosis",
    "recommendations",
    "validation",
]


def load_tree() -> dict[str, Any]:
    return yaml.safe_load(TREE.read_text(encoding="utf-8"))


def fail(report: dict[str, Any], code: str, message: str, **extra: Any) -> None:
    report.setdefault("failures", []).append({"code": code, "message": message, **extra})


def handled_intents(front: str) -> set[str]:
    found = set(re.findall(r"intent\s*===\s*['\"]([^'\"]+)['\"]", front))
    found |= set(re.findall(r"\['([^'\"]+)'\s*,\s*'([^'\"]+)'\]", front)[0]) if False else set()
    for m in re.finditer(r"\[([^\]]+)\]\.includes\(intent\)", front):
        found |= set(re.findall(r"['\"]([^'\"]+)['\"]", m.group(1)))
    return found


def main() -> int:
    tree = load_tree()
    front = FRONT.read_text(encoding="utf-8")
    src = SRC.read_text(encoding="utf-8")
    report: dict[str, Any] = {
        "schema": "appomar.audit_tree_validator.v1",
        "tree": str(TREE.relative_to(ROOT)),
        "front": str(FRONT.relative_to(ROOT)),
        "checked": [],
        "failures": [],
    }

    steps = tree.get("steps") or []
    step_ids = [str(s.get("step_id")) for s in steps]
    report["checked"].append({"id": "step_count", "value": len(step_ids)})
    if len(step_ids) != len(set(step_ids)):
        fail(report, "duplicate_step_id", "Step IDs must be unique", duplicates=sorted({x for x in step_ids if step_ids.count(x) > 1}))
    cursor = -1
    for required in CRITICAL_STEPS:
        if required not in step_ids:
            fail(report, "missing_critical_step", "Critical audit step missing", step=required)
            continue
        idx = step_ids.index(required)
        if idx <= cursor:
            fail(report, "critical_order_changed", "Critical V0 scope order changed unexpectedly", step=required, found=step_ids)
        cursor = idx

    for step in steps:
        sid = str(step.get("step_id"))
        inputs = step.get("inputs") or []
        required = [i.get("id") for i in inputs if isinstance(i, dict) and i.get("required")]
        if not required and sid in CRITICAL_STEPS:
            fail(report, "critical_step_without_required_input", "Critical step should have at least one required input", step=sid)
        for branch in step.get("branches") or []:
            target = str(branch.get("then") or "")
            if target.startswith("skip_step("):
                skipped = target.removeprefix("skip_step(").removesuffix(")")
                if skipped not in step_ids:
                    fail(report, "branch_skips_unknown_step", "Branch skip target does not exist", step=sid, target=skipped)

    handled = handled_intents(front)
    missing_handlers = sorted(REQUIRED_FRONT_INTENTS - handled - {"save", "explain"})
    # save/explain are text-specific in pacte, not always generic intent branches.
    for intent in missing_handlers:
        fail(report, "front_intent_not_handled", "Required quick-reply intent has no explicit front handler", intent=intent)
    report["checked"].append({"id": "handled_intents", "value": sorted(handled)})

    required_markers = [
        "public_research_required",
        "public_research_validation_required",
        "_tree_public_research_block",
        "runPublicResearch",
        "confirm_public_research",
        "confirm_omar_story",
        "buildOmarMiniStory",
        "/public-research",
    ]
    for marker in required_markers:
        haystack = src + "\n" + front
        if marker not in haystack:
            fail(report, "missing_public_research_gate_marker", "Public research gate marker missing", marker=marker)

    status = "pass" if not report["failures"] else "fail"
    report["status"] = status
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
