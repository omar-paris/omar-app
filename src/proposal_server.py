#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from site_data import OA_START_PACKS  # noqa: E402

DEFAULT_DATA_DIR = ROOT / "var"
# UUID hex (V0.3.1, app#14 non-enumerable) + ancien format timestamp (lecture des
# propositions déjà stockées uniquement)
PROPOSAL_ID_RE = re.compile(r"^proposal-(?:[0-9a-f]{32}|[0-9]{8}T[0-9]{6}Z)-[a-z0-9-]+$")
SECRET_PATTERNS = ["HCLOUD_TOKEN", "Authorization", "Bearer ", "sk-"]


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "client-demo"


def proposal_id(payload: dict[str, Any]) -> str:
    company = payload.get("client_profile", {}).get("company_name", "client-demo")
    return f"proposal-{uuid.uuid4().hex}-{slugify(str(company))}"


def validate_proposal(payload: dict[str, Any]) -> str | None:
    if payload.get("type") != "configuration_proposal":
        return "type must be configuration_proposal"
    if payload.get("status") != "pending_human_go":
        return "status must remain pending_human_go"
    safety = payload.get("safety") or {}
    if safety.get("paid_actions") != "none":
        return "paid actions are forbidden in V0.3 proposal storage"
    hetzner = payload.get("hetzner_payload") or {}
    if hetzner.get("mode") != "dry_run_no_paid_resource":
        return "hetzner_payload.mode must be dry_run_no_paid_resource"
    raw = json.dumps(payload, ensure_ascii=False)
    for pattern in SECRET_PATTERNS:
        if pattern in raw:
            return f"secret-like literal forbidden: {pattern}"
    return None


def safe_write_proposal(data_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    error = validate_proposal(payload)
    if error:
        raise ValueError(error)
    out = dict(payload)
    out["id"] = proposal_id(payload)
    out["stored_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out["storage"] = {"mode": "local_json", "path": f"var/proposals/{out['id']}.json"}
    proposals_dir = data_dir / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    target = proposals_dir / f"{out['id']}.json"
    target.write_bytes(json_bytes(out))
    return out


import urllib.parse  # noqa: E402

STRIPE_API = "https://api.stripe.com/v1"


def _stripe_secret(mode: str, field: str) -> str:
    """Lit un champ de secret/stripe/<mode> dans le Vault."""
    try:
        raw = subprocess.check_output(
            ["/usr/bin/vault", "kv", "get", "-format=json", f"secret/stripe/{mode}"],
            text=True, stderr=subprocess.DEVNULL,
            env={**os.environ, "VAULT_ADDR": "http://127.0.0.1:8202"},
        )
        return json.loads(raw).get("data", {}).get("data", {}).get(field, "")
    except Exception:
        return ""


def _stripe_key(mode: str) -> str:
    """Clé secrète Stripe. 'test' par défaut ; 'live' uniquement sur OA_STRIPE_MODE=live."""
    return _stripe_secret(mode, "STRIPE_SECRET_KEY")


def _verify_stripe_sig(payload: bytes, sig_header: str, secret: str) -> bool:
    """Vérifie la signature Stripe (schéma t=…,v1=…) — HMAC-SHA256, tolérance 5 min."""
    import hashlib
    try:
        parts = dict(p.split("=", 1) for p in sig_header.split(","))
        ts, v1 = parts.get("t", ""), parts.get("v1", "")
        signed = f"{ts}.".encode() + payload
        expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, v1):
            return False
        return abs(time.time() - int(ts)) < 300
    except Exception:
        return False


def _stripe_flatten(prefix: str, value: Any, out: list) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            _stripe_flatten(f"{prefix}[{k}]" if prefix else k, v, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _stripe_flatten(f"{prefix}[{i}]", v, out)
    else:
        out.append((prefix, str(value)))


def stripe_post(endpoint: str, params: dict, key: str) -> dict:
    flat: list = []
    for k, v in params.items():
        _stripe_flatten(k, v, flat)
    body = urllib.parse.urlencode(flat).encode()
    req = urllib.request.Request(f"{STRIPE_API}/{endpoint}", data=body,
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read()).get("error", {"message": str(e)})}


_CATALOG_CACHE: dict[str, Any] = {}


def load_catalog() -> dict[str, Any]:
    """Catalogue de vente. catalog.json (éditable via admin) prioritaire,
    sinon catalog.yaml (référence lisible, parseur minimal)."""
    jpath = ROOT / "catalog.json"
    if jpath.exists():
        try:
            return json.loads(jpath.read_text(encoding="utf-8"))
        except Exception:
            pass
    path = ROOT / "catalog.yaml"
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {"products": [], "error": "catalog_missing"}
    if _CATALOG_CACHE.get("mtime") == mtime:
        return _CATALOG_CACHE["data"]
    products, cur = [], None
    list_key = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip().startswith("#") or not raw.strip():
            continue
        if raw.startswith("  - id:"):
            cur = {"id": raw.split("id:", 1)[1].strip()}
            products.append(cur)
            list_key = None
        elif raw.startswith("    ") and cur is not None and ":" in raw:
            k, _, v = raw.strip().partition(":")
            v = v.strip()
            if v in ("", "[]"):
                if v == "":
                    list_key = k
                    cur[k] = []
                else:
                    cur[k] = []
                continue
            list_key = None
            if v.startswith("[") and v.endswith("]"):
                cur[k] = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
            elif v in ("null", "~"):
                cur[k] = None
            elif v.lstrip("-").isdigit():
                cur[k] = int(v)
            else:
                cur[k] = v.strip('"')
        elif raw.startswith("      - ") and list_key and cur is not None:
            cur[list_key].append(raw.strip()[2:].strip().strip('"'))
    data = {"version": "0.1", "currency": "EUR", "products": products}
    _CATALOG_CACHE.update(mtime=mtime, data=data)
    return data


def read_devis(data_dir: Path, did: str) -> dict[str, Any] | None:
    if not re.match(r"^devis-[0-9A-Za-z-]+$", did):
        return None
    path = data_dir / "devis" / f"{did}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_proposal(data_dir: Path, pid: str) -> dict[str, Any] | None:
    if not PROPOSAL_ID_RE.match(pid):
        return None
    path = data_dir / "proposals" / f"{pid}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def pricing_payload() -> dict[str, Any]:
    # V0.3 is intentionally read-only. If HCLOUD_TOKEN is present, we only call pricing.
    token = os.environ.get("HCLOUD_TOKEN")
    mode = "static_fallback"
    source = "src/site_data.py"
    hcloud_error = None
    if token:
        try:
            req = urllib.request.Request(
                "https://api.hetzner.cloud/v1/pricing",
                headers={"Authorization": f"Bearer {token}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                json.loads(response.read().decode("utf-8"))
            mode = "live_readonly"
            source = "https://api.hetzner.cloud/v1/pricing"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            hcloud_error = str(exc)
    return {
        "ok": True,
        "provider": "hetzner",
        "mode": mode,
        "source": source,
        "paid_actions": "none",
        "hcloud_error": hcloud_error,
        "packs": OA_START_PACKS,
    }


class ProposalHandler(BaseHTTPRequestHandler):
    server_version = "OmarAppProposalServer/0.3"

    @property
    def data_dir(self) -> Path:
        return self.server.data_dir  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("proposal_server " + fmt % args + "\n")

    def authorized(self) -> bool:
        expected = self.server.api_token  # type: ignore[attr-defined]
        header = self.headers.get("authorization", "")
        if header.startswith("Bearer "):
            provided = header[len("Bearer "):].strip()
        else:
            provided = self.headers.get("x-oa-token", "").strip()
        return bool(provided) and hmac.compare_digest(provided, expected)

    def reject_unauthorized(self) -> None:
        self.send_json(401, {"ok": False, "error": "unauthorized"})

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self.send_json(200, {"ok": True, "service": "omar-app-proposals", "version": "V0.4.0"})
            return
        if self.path == "/api/catalog":
            self.send_json(200, load_catalog())
            return
        if self.path.startswith("/api/devis/"):
            did = self.path[len("/api/devis/"):].split("?", 1)[0]
            dv = read_devis(self.data_dir, did)
            if not dv:
                self.send_json(404, {"ok": False, "error": "devis_not_found"})
                return
            self.send_json(200, {"ok": True, "devis": dv})
            return
        if self.path == "/api/hetzner/pricing":
            self.send_json(200, pricing_payload())
            return
        prefix = "/api/proposals/"
        if self.path.startswith(prefix):
            if not self.authorized():
                self.reject_unauthorized()
                return
            pid = self.path[len(prefix):].split("?", 1)[0]
            proposal = read_proposal(self.data_dir, pid)
            if not proposal:
                self.send_json(404, {"ok": False, "error": "proposal_not_found"})
                return
            self.send_json(200, {"ok": True, "proposal": proposal})
            return
        self.send_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        if self.path == "/api/onboarding":
            self.handle_onboarding()
            return
        if self.path == "/api/admin/catalog":
            self.handle_admin_catalog()
            return
        if self.path == "/api/devis":
            self.handle_devis()
            return
        if self.path == "/api/checkout":
            self.handle_checkout()
            return
        if self.path == "/api/stripe-webhook":
            self.handle_stripe_webhook()
            return
        if self.path != "/api/proposals":
            self.send_json(404, {"ok": False, "error": "not_found"})
            return
        if not self.authorized():
            self.reject_unauthorized()
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 200_000:
                raise ValueError("invalid content-length")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("payload must be object")
            proposal = safe_write_proposal(self.data_dir, payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self.send_json(422, {"ok": False, "error": str(exc)})
            return
        self.send_json(201, {"ok": True, "proposal": proposal})


    def handle_admin_catalog(self) -> None:
        """Sauvegarde du catalogue (prix, produits, packs). Protégé par OAuth :
        le vhost n'atteint cet endpoint qu'après forward_auth, et injecte
        X-Auth-Request-Email — on vérifie qu'il est dans la liste admin."""
        email = self.headers.get("X-Auth-Request-Email", "").strip().lower()
        admins = {e.strip().lower() for e in
                  os.environ.get("OA_ADMIN_EMAILS", "alexwillemetz@gmail.com").split(",")}
        if email not in admins:
            self.send_json(403, {"ok": False, "error": "not_admin", "vu": email or "(aucun email)"})
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 200_000:
                raise ValueError("payload invalide")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            products = payload.get("products")
            if not isinstance(products, list) or not products:
                raise ValueError("products vide")
            for p in products:
                if not p.get("id") or not p.get("label"):
                    raise ValueError("chaque produit exige id + label")
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self.send_json(422, {"ok": False, "error": str(exc)})
            return
        out = {"version": payload.get("version", "0.1"), "currency": "EUR", "products": products}
        (ROOT / "catalog.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        _CATALOG_CACHE.clear()
        self.send_json(200, {"ok": True, "count": len(products), "par": email})

    def handle_devis(self) -> None:
        """Crée un devis depuis une sélection de produits du catalogue (app#24/qg#28).
        Public (un prospect n'a pas de compte) — pas de Bearer."""
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 50_000:
                raise ValueError("invalid content-length")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            item_ids = payload.get("items") or []
            if not isinstance(item_ids, list) or not item_ids:
                raise ValueError("items vide")
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self.send_json(422, {"ok": False, "error": str(exc)})
            return
        catalog = {p["id"]: p for p in load_catalog().get("products", [])}
        lignes, mensuel, unique = [], 0, 0
        for iid in item_ids:
            p = catalog.get(iid)
            if not p:
                continue
            lignes.append({"id": p["id"], "label": p["label"],
                           "prix_mensuel": p.get("prix_mensuel"), "prix_unique": p.get("prix_unique")})
            mensuel += p.get("prix_mensuel") or 0
            unique += p.get("prix_unique") or 0
        did = f"devis-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
        devis = {
            "id": did, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "client": payload.get("client", {}), "lignes": lignes,
            "total_mensuel_eur": mensuel, "total_unique_eur": unique,
            "devise": "EUR", "statut": "brouillon",
        }
        d = self.data_dir / "devis"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{did}.json").write_bytes(json_bytes(devis))
        self.send_json(201, {"ok": True, "devis": devis})

    def handle_checkout(self) -> None:
        """Lance le paiement Stripe d'un devis. Stub tant que la clef Stripe n'est
        pas fournie (app#32) — renvoie 503 explicite, jamais de faux paiement."""
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            did = str(payload.get("devis_id", ""))
        except Exception as exc:
            self.send_json(422, {"ok": False, "error": str(exc)})
            return
        devis = read_devis(self.data_dir, did)
        if not devis:
            self.send_json(404, {"ok": False, "error": "devis_not_found"})
            return
        mode = "live" if os.environ.get("OA_STRIPE_MODE") == "live" else "test"
        key = _stripe_key(mode)
        if not key:
            self.send_json(503, {"ok": False, "error": "stripe_non_configure",
                                 "message": f"Paiement bientôt disponible — clef Stripe {mode} en attente.",
                                 "devis_id": did, "total_mensuel_eur": devis["total_mensuel_eur"]})
            return
        base = "https://app.omar.paris"
        params: dict = {
            "success_url": f"{base}/devis/?paid={did}",
            "cancel_url": f"{base}/devis/?cancel={did}",
            "client_reference_id": did,
            "metadata": {"devis_id": did},
        }
        mensuel = [l for l in devis["lignes"] if l.get("prix_mensuel")]
        unique = [l for l in devis["lignes"] if l.get("prix_unique")]
        line_items = []
        if mensuel:
            params["mode"] = "subscription"
            for l in mensuel:
                line_items.append({"price_data": {"currency": "eur",
                    "product_data": {"name": l["label"]},
                    "unit_amount": int(l["prix_mensuel"]) * 100,
                    "recurring": {"interval": "month"}}, "quantity": 1})
            # prestations one-shot ajoutées sur la 1re facture de l'abonnement
            if unique:
                params["subscription_data"] = {"metadata": {"devis_id": did}}
        else:
            params["mode"] = "payment"
        for l in unique:
            li = {"price_data": {"currency": "eur",
                  "product_data": {"name": l["label"]},
                  "unit_amount": int(l["prix_unique"]) * 100}, "quantity": 1}
            if mensuel:
                # en mode subscription, les one-shot passent en add_invoice_items
                params.setdefault("subscription_data", {})
                params["line_items"] = line_items  # set below anyway
            line_items.append(li)
        params["line_items"] = line_items
        session = stripe_post("checkout/sessions", params, key)
        if session.get("error"):
            self.send_json(502, {"ok": False, "error": "stripe_error",
                                 "message": session["error"].get("message", "?")})
            return
        # marque le devis 'en_paiement'
        devis["statut"] = "en_paiement"
        devis["stripe_session"] = session.get("id")
        devis["stripe_mode"] = mode
        (self.data_dir / "devis" / f"{did}.json").write_bytes(json_bytes(devis))
        self.send_json(200, {"ok": True, "checkout_url": session.get("url"), "mode": mode})

    def handle_stripe_webhook(self) -> None:
        """Reçoit les events Stripe. Marque le devis 'acheté' à la complétion du
        paiement → débloque la configuration. Signature OBLIGATOIRE (anti-falsification)."""
        try:
            length = int(self.headers.get("content-length", "0"))
            raw = self.rfile.read(length)
        except Exception:
            self.send_json(400, {"ok": False})
            return
        mode = "live" if os.environ.get("OA_STRIPE_MODE") == "live" else "test"
        whsec = _stripe_secret(mode, "STRIPE_WEBHOOK_SECRET")
        if not whsec or not _verify_stripe_sig(raw, self.headers.get("Stripe-Signature", ""), whsec):
            self.send_json(400, {"ok": False, "error": "bad_signature"})
            return
        try:
            event = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_json(400, {"ok": False})
            return
        if event.get("type") == "checkout.session.completed":
            obj = event.get("data", {}).get("object", {})
            did = obj.get("client_reference_id") or (obj.get("metadata") or {}).get("devis_id")
            dv = read_devis(self.data_dir, did) if did else None
            if dv:
                dv["statut"] = "achete"
                dv["paye_le"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                (self.data_dir / "devis" / f"{did}.json").write_bytes(json_bytes(dv))
        self.send_json(200, {"received": True})

    def handle_onboarding(self) -> None:
        """Dossier d'onboarding v1 (app#22). Pas de Bearer : la couche d'accès est
        le vhost tailnet_only (puis OAuth au rollout qg#23) — un humain remplit ce
        formulaire, il n'a pas de token."""
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 100_000:
                raise ValueError("invalid content-length")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            record = payload.get("record")
            if not isinstance(record, dict) or not record:
                raise ValueError("record vide")
            raw = json.dumps(payload, ensure_ascii=False)
            for pattern in SECRET_PATTERNS:
                if pattern in raw:
                    raise ValueError(f"secret-like literal forbidden: {pattern}")
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self.send_json(422, {"ok": False, "error": str(exc)})
            return
        slug = slugify(str(record.get("identite", "client"))[:40])
        oid = f"onboarding-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{slug}"
        out_dir = self.data_dir / "clients"
        out_dir.mkdir(parents=True, exist_ok=True)
        payload["id"] = oid
        payload["received_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (out_dir / f"{oid}.json").write_bytes(json_bytes(payload))
        self.send_json(201, {"ok": True, "id": oid})


class ReusableServer(ThreadingHTTPServer):
    allow_reuse_address = True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8096)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    api_token = os.environ.get("OA_PROPOSALS_TOKEN", "").strip()
    if len(api_token) < 32:
        sys.exit("OA_PROPOSALS_TOKEN manquant ou trop court (>=32 chars requis) — refus de démarrer sans auth (app#13)")
    server = ReusableServer((args.host, args.port), ProposalHandler)
    server.data_dir = args.data_dir  # type: ignore[attr-defined]
    server.api_token = api_token  # type: ignore[attr-defined]
    args.data_dir.mkdir(parents=True, exist_ok=True)
    print(f"serving omar-app proposals on http://{args.host}:{args.port} data={args.data_dir}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
