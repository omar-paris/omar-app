from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "data" / "audit_knowledge"
SECTORS_ROOT = KNOWLEDGE_ROOT / "sectors"


class AuditBizValidationError(ValueError):
    """Raised when an AuditBizIA contract is incomplete or malformed."""


@dataclass(frozen=True)
class AuditQuestion:
    id: str
    step: str
    facet: str
    question: str
    why: str
    interaction: str = "open"
    options: tuple[str, ...] = ()
    sensitivity: str = "normal"
    report_impact: str = "medium"
    expected_signal: tuple[str, ...] = ()
    follow_up: str = ""
    skip_allowed: bool = True
    save_resume_allowed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "step": self.step,
            "facet": self.facet,
            "question": self.question,
            "why": self.why,
            "interaction": self.interaction,
            "options": list(self.options),
            "sensitivity": self.sensitivity,
            "report_impact": self.report_impact,
            "expected_signal": list(self.expected_signal),
            "follow_up": self.follow_up,
            "skip_allowed": self.skip_allowed,
            "save_resume_allowed": self.save_resume_allowed,
        }


@dataclass(frozen=True)
class SectorPack:
    sector_id: str
    label: str
    version: str
    steps: tuple[str, ...]
    facets: tuple[dict[str, Any], ...]
    questions: tuple[AuditQuestion, ...]
    risks: tuple[dict[str, Any], ...]
    sources_md: str

    def questions_for_step(self, step: str) -> list[AuditQuestion]:
        return [q for q in self.questions if q.step == step]


def load_structured_file(path: Path) -> Any:
    """Load a structured knowledge file.

    V1 deliberately uses JSON-compatible YAML files so we do not introduce a
    PyYAML dependency in the static AppOmar runtime. If a future dependency is
    accepted, this function is the only place to extend.
    """
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AuditBizValidationError(
            f"{path} must be JSON-compatible YAML for AuditBizIA V1: {exc}"
        ) from exc


def _require_mapping(data: Any, path: Path) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise AuditBizValidationError(f"{path} must contain an object")
    return data


def _require_list(data: Any, path: Path) -> list[Any]:
    if not isinstance(data, list):
        raise AuditBizValidationError(f"{path} must contain a list")
    return data


def _as_non_empty_str(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AuditBizValidationError(f"missing required field: {field}")
    return text


def validate_question(raw: dict[str, Any]) -> AuditQuestion:
    interaction = str(raw.get("interaction") or "open").strip()
    if interaction not in {"open", "choice", "rank", "confirm"}:
        raise AuditBizValidationError(f"invalid interaction for {raw.get('id')}: {interaction}")
    options = tuple(str(x).strip() for x in raw.get("options", []) if str(x).strip())
    if interaction in {"choice", "rank"} and not options:
        raise AuditBizValidationError(f"{raw.get('id')} requires options for {interaction}")
    sensitivity = str(raw.get("sensitivity") or "normal").strip()
    if sensitivity not in {"low", "normal", "sensitive"}:
        raise AuditBizValidationError(f"invalid sensitivity for {raw.get('id')}: {sensitivity}")
    report_impact = str(raw.get("report_impact") or "medium").strip()
    if report_impact not in {"low", "medium", "high"}:
        raise AuditBizValidationError(f"invalid report_impact for {raw.get('id')}: {report_impact}")
    return AuditQuestion(
        id=_as_non_empty_str(raw.get("id"), "question.id"),
        step=_as_non_empty_str(raw.get("step"), "question.step"),
        facet=_as_non_empty_str(raw.get("facet"), "question.facet"),
        question=_as_non_empty_str(raw.get("question"), "question.question"),
        why=_as_non_empty_str(raw.get("why"), "question.why"),
        interaction=interaction,
        options=options,
        sensitivity=sensitivity,
        report_impact=report_impact,
        expected_signal=tuple(str(x).strip() for x in raw.get("expected_signal", []) if str(x).strip()),
        follow_up=str(raw.get("follow_up") or "").strip(),
        skip_allowed=bool(raw.get("skip_allowed", True)),
        save_resume_allowed=bool(raw.get("save_resume_allowed", True)),
    )


def load_sector_pack(sector_id: str, sectors_root: Path = SECTORS_ROOT) -> SectorPack:
    base = sectors_root / sector_id
    if not base.exists():
        raise AuditBizValidationError(f"sector pack not found: {sector_id}")
    sector = _require_mapping(load_structured_file(base / "sector.yaml"), base / "sector.yaml")
    facets = _require_list(load_structured_file(base / "facets.yaml"), base / "facets.yaml")
    questions_raw = _require_list(load_structured_file(base / "questions.yaml"), base / "questions.yaml")
    risks = _require_list(load_structured_file(base / "risks.yaml"), base / "risks.yaml")
    sources_md = (base / "sources.md").read_text(encoding="utf-8")

    pack_sector_id = _as_non_empty_str(sector.get("sector_id"), "sector.sector_id")
    if pack_sector_id != sector_id:
        raise AuditBizValidationError(f"sector_id mismatch: expected {sector_id}, got {pack_sector_id}")
    steps = tuple(str(x).strip() for x in sector.get("steps", []) if str(x).strip())
    if not steps:
        raise AuditBizValidationError("sector.steps must not be empty")
    facet_ids = {str(f.get("id") or "").strip() for f in facets if isinstance(f, dict)}
    if not facet_ids:
        raise AuditBizValidationError("facets must not be empty")
    questions = tuple(validate_question(q) for q in questions_raw if isinstance(q, dict))
    if not questions:
        raise AuditBizValidationError("questions must not be empty")
    question_ids = [q.id for q in questions]
    duplicates = sorted({qid for qid in question_ids if question_ids.count(qid) > 1})
    if duplicates:
        raise AuditBizValidationError(f"duplicate question ids: {duplicates}")
    for q in questions:
        if q.step not in steps:
            raise AuditBizValidationError(f"{q.id} references unknown step {q.step}")
        if q.facet not in facet_ids:
            raise AuditBizValidationError(f"{q.id} references unknown facet {q.facet}")
    return SectorPack(
        sector_id=pack_sector_id,
        label=_as_non_empty_str(sector.get("label"), "sector.label"),
        version=str(sector.get("version") or "0.1").strip(),
        steps=steps,
        facets=tuple(f for f in facets if isinstance(f, dict)),
        questions=questions,
        risks=tuple(r for r in risks if isinstance(r, dict)),
        sources_md=sources_md,
    )


def load_available_sector_packs(sectors_root: Path = SECTORS_ROOT) -> dict[str, SectorPack]:
    packs: dict[str, SectorPack] = {}
    if not sectors_root.exists():
        return packs
    for child in sorted(sectors_root.iterdir()):
        if child.is_dir() and (child / "sector.yaml").exists():
            packs[child.name] = load_sector_pack(child.name, sectors_root)
    return packs
