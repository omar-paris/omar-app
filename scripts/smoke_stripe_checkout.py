#!/usr/bin/env python3
"""Smoke AppOmar checkout without exposing secrets.

Creates a non-zero devis via the running proposal server, calls /api/checkout,
and prints a redacted result:
- OK when a configured payment provider returns a checkout URL
- BLOCKED payment_provider_unconfigured while payment provider is not wired/configured
- FAIL for unexpected API/runtime errors

No payment secret, checkout URL, or sensitive payload is printed.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def post_json(base_url: str, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {"ok": False, "error": f"HTTP {exc.code}"}
        return exc.code, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8096")
    parser.add_argument("--client-email", default="payment-smoke@example.test")
    args = parser.parse_args()

    devis_status, devis_payload = post_json(args.base_url, "/api/devis", {
        "client": {"email": args.client_email, "name": "Payment Smoke"},
        "items": ["formule-starter", "presta-onboarding"],
    })
    if devis_status != 201 or not devis_payload.get("ok"):
        print(json.dumps({"status": "FAIL", "step": "devis", "http": devis_status, "error": devis_payload.get("error")}, ensure_ascii=False))
        return 2

    devis = devis_payload["devis"]
    checkout_status, checkout_payload = post_json(args.base_url, "/api/checkout", {"devis_id": devis["id"]})
    if checkout_status == 409 and checkout_payload.get("error") == "devis_not_validated":
        validate_status, validate_payload = post_json(args.base_url, f"/api/devis/{devis['id']}/validate", {
            "accepted": True,
            "email": args.client_email,
            "understood": "Smoke test: devis validé explicitement avant checkout paiement sécurisé.",
        })
        if validate_status != 200 or not validate_payload.get("ok"):
            print(json.dumps({"status": "FAIL", "step": "validate_devis", "http": validate_status, "error": validate_payload.get("error")}, ensure_ascii=False))
            return 2
        checkout_status, checkout_payload = post_json(args.base_url, "/api/checkout", {"devis_id": devis["id"]})
    result: dict[str, Any] = {
        "devis_id": devis["id"],
        "total_mensuel_eur": devis["total_mensuel_eur"],
        "total_unique_eur": devis["total_unique_eur"],
        "checkout_http": checkout_status,
    }
    if checkout_status == 200 and checkout_payload.get("ok") and checkout_payload.get("checkout_url"):
        result.update({
            "status": "OK",
            "mode": checkout_payload.get("mode"),
            "checkout_url_present": True,
            "checkout_url_host": checkout_payload["checkout_url"].split("/", 3)[:3],
        })
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if checkout_status == 503 and checkout_payload.get("error") == "payment_provider_unconfigured":
        result.update({
            "status": "BLOCKED",
            "blocker": "payment_provider_unconfigured",
            "message": checkout_payload.get("message"),
        })
        print(json.dumps(result, ensure_ascii=False))
        return 3
    result.update({"status": "FAIL", "error": checkout_payload.get("error"), "message": checkout_payload.get("message")})
    print(json.dumps(result, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    sys.exit(main())
