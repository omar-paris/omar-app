from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auditbiz_schema import AuditBizValidationError, load_sector_pack, load_structured_file, validate_question  # noqa: E402


def test_validate_question_requires_explanation_and_options_for_choice():
    q = validate_question(
        {
            "id": "bakery_losses_1",
            "step": "operations",
            "facet": "production_offre",
            "question": "Les pertes viennent surtout d’où ?",
            "why": "Les invendus touchent marge, production et image.",
            "interaction": "choice",
            "options": ["Pain", "Viennoiseries"],
            "expected_signal": ["marge", "production"],
            "report_impact": "high",
        }
    )
    assert q.id == "bakery_losses_1"
    assert q.interaction == "choice"
    assert q.options == ("Pain", "Viennoiseries")
    assert q.to_dict()["skip_allowed"] is True

    with pytest.raises(AuditBizValidationError, match="requires options"):
        validate_question(
            {
                "id": "bad_choice",
                "step": "operations",
                "facet": "production_offre",
                "question": "Choisissez.",
                "why": "Pour comprendre.",
                "interaction": "choice",
            }
        )


def test_load_structured_file_uses_json_compatible_yaml(tmp_path: Path):
    path = tmp_path / "sector.yaml"
    path.write_text(json.dumps({"sector_id": "bakery"}), encoding="utf-8")
    assert load_structured_file(path) == {"sector_id": "bakery"}

    bad = tmp_path / "bad.yaml"
    bad.write_text("sector_id: bakery\n", encoding="utf-8")
    with pytest.raises(AuditBizValidationError, match="JSON-compatible"):
        load_structured_file(bad)


def test_bakery_sector_pack_loads_and_validates_core_contract():
    pack = load_sector_pack("bakery")
    assert pack.sector_id == "bakery"
    assert pack.label.lower().startswith("boulangerie")
    assert "business_model" in pack.steps
    assert len(pack.facets) >= 8
    assert len(pack.questions) >= 10
    qids = {q.id for q in pack.questions}
    assert "bakery_offer_rank" in qids
    assert "bakery_losses_1" in qids
    assert any(q.interaction == "rank" for q in pack.questions)
    assert any(q.sensitivity == "sensitive" for q in pack.questions)
    assert pack.sources_md.startswith("# Sources")
