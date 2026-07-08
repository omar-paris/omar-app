import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog.json"
REQUIRED_PROOF_FIELDS = {
    "capability_status",
    "proof_tier",
    "proof_scope",
    "runtime_scope",
    "evidence_refs",
    "measurement_state",
    "connector_dependency_status",
    "human_approval_required",
    "release_gate_ref",
    "durable_gate_artifact_ref",
    "safe_claim",
    "do_not_claim",
    "last_verified_at",
}
APPOMAR_V1_MODULES = {
    "presence-google-business-avis",
    "recrutement-annonces-candidats",
    "secretaire-tri-demandes",
    "secretaire-redaction-reponses",
    "secretaire-taches-relances",
    "secretaire-documents-devis-syntheses",
    "secretaire-connexions-surveillance",
}


def load_products() -> list[dict]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))["products"]


def test_appomar_catalog_products_expose_proof_measurement_schema():
    missing = {}
    for product in load_products():
        absent = sorted(REQUIRED_PROOF_FIELDS - set(product))
        if absent:
            missing[product["id"]] = absent
    assert missing == {}


def test_appomar_v1_modules_remain_potential_with_unknown_measurements():
    by_id = {product["id"]: product for product in load_products()}
    assert APPOMAR_V1_MODULES <= set(by_id)

    for module_id in APPOMAR_V1_MODULES:
        product = by_id[module_id]
        assert product["capability_status"] == "potential"
        assert product["proof_tier"] == "potential"
        assert product["runtime_scope"] == "catalogue_only"
        assert product["runtime_status"] == "unknown"
        assert product["runtime_client_proven"] is False
        assert product["measurement_state"] == {
            "ram_mb": None,
            "disk_mb": None,
            "runtime_cost": None,
            "state": "unknown",
            "measured_at": None,
            "measurement_ref": None,
        }
        assert product["ram_mb"] == "unknown"
        assert product["disk_mb"] == "unknown"
        assert product["durable_gate_artifact_ref"] == ""


def test_no_commercial_claim_is_proven_without_evidence_and_durable_gate():
    violations = []
    for product in load_products():
        if product.get("capability_status") != "proven" and product.get("proof_tier") != "proven":
            continue
        if not product.get("evidence_refs"):
            violations.append((product["id"], "missing_evidence_refs"))
        if not (product.get("release_gate_ref") or product.get("durable_gate_artifact_ref")):
            violations.append((product["id"], "missing_durable_gate_ref"))
    assert violations == []
