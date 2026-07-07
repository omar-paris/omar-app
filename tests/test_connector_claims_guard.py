import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REFS = {"t_3c8942df", "t_911dc1e5", "t_b7f1552c", "t_50fd4fd7"}
WATCHED_IDS = {
    "formule-pro",
    "mod-crm",
    "mod-presence",
    "presence-google-business-avis",
}


def test_appomar_connector_commercial_claims_stay_potential_unknown_without_tenant_local_manifest():
    payload = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    products = {item["id"]: item for item in payload["products"]}

    assert WATCHED_IDS.issubset(products)
    for product_id in WATCHED_IDS:
        product = products[product_id]
        assert product.get("capability_status") == "potential", product_id
        assert product.get("runtime_status") == "unknown", product_id
        assert product.get("runtime_client_proven") is False, product_id
        assert product.get("connector_manifest_required") is True, product_id
        assert REQUIRED_REFS.issubset(set(product.get("connector_guard_refs", []))), product_id


def test_appomar_catalog_contains_no_client_configured_or_proven_connector_claims():
    payload = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    watched_terms = ("google", "gmail", "business", "crm", "finance", "factur", "connexion")
    offenders = []
    for product in payload["products"]:
        text = " ".join(str(product.get(key, "")) for key in ["id", "label", "pitch", "famille", "inclus"]).lower()
        if not any(term in text for term in watched_terms):
            continue
        if product.get("capability_status") in {"configured", "proven"} or product.get("runtime_client_proven") is True:
            offenders.append(product["id"])
    assert offenders == []
