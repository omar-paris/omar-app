import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REFS = {"t_3c8942df", "t_911dc1e5", "t_b7f1552c", "t_50fd4fd7"}
CONNECTOR_CLAIM_IDS = {
    "formule-starter",
    "formule-pro",
    "mod-crm",
    "mod-presence",
    "presence-google-business-avis",
    "secretaire-connexions-surveillance",
}
WATCHED_TERMS = ("google", "gmail", "business", "crm", "finance", "factur", "connexion")


def load_products() -> dict[str, dict]:
    payload = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["products"]}


def test_appomar_connector_commercial_claims_stay_potential_unknown_without_tenant_local_manifest():
    products = load_products()

    assert CONNECTOR_CLAIM_IDS.issubset(products)
    for product_id in CONNECTOR_CLAIM_IDS:
        product = products[product_id]
        assert product.get("capability_status") == "potential", product_id
        assert product.get("proof_tier") == "potential", product_id
        assert product.get("proof_status") == "potential", product_id
        assert product.get("runtime_status") == "unknown", product_id
        assert product.get("runtime_client_proven") is False, product_id
        assert product.get("connector_dependency_status") == "unknown", product_id
        assert product.get("connector_manifest_required") is True, product_id
        assert REQUIRED_REFS.issubset(set(product.get("connector_guard_refs", []))), product_id


def test_appomar_catalog_contains_no_configured_or_proven_connector_claims_without_manifest_gate():
    offenders = []
    for product in load_products().values():
        text = " ".join(str(product.get(key, "")) for key in ["id", "label", "pitch", "famille", "inclus", "catalogue_refs"]).lower()
        if not any(term in text for term in WATCHED_TERMS):
            continue
        has_manifest_gate = product.get("runtime_client_proven") is True and bool(product.get("evidence_refs")) and bool(
            product.get("release_gate_ref") or product.get("durable_gate_artifact_ref")
        )
        if has_manifest_gate:
            continue
        if product.get("capability_status") in {"configured", "proven"} or product.get("proof_tier") in {"configured", "proven"} or product.get("proof_status") in {"configured", "proven"}:
            offenders.append(product["id"])
    assert offenders == []
