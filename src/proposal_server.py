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
DEFAULT_VAULT_ADDR = os.environ.get("OA_APP_VAULT_ADDR", os.environ.get("VAULT_ADDR", "http://127.0.0.1:8202"))
DEFAULT_VAULT_TOKEN_FILE = Path(
    os.environ.get("OA_APP_VAULT_TOKEN_FILE", "/home/omar/.config/omar-app/vault-token")
)
# UUID hex (V0.3.1, app#14 non-enumerable) + ancien format timestamp (lecture des
# propositions déjà stockées uniquement)
PROPOSAL_ID_RE = re.compile(r"^proposal-(?:[0-9a-f]{32}|[0-9]{8}T[0-9]{6}Z)-[a-z0-9-]+$")
SECRET_PATTERNS = ["HCLOUD_TOKEN", "Authorization", "Bearer ", "sk-"]
ALLOWED_VAULT_FIELDS = {
    "secret/stripe/test": {"STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"},
    "secret/stripe/live": {"STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"},
    "secret/integrations/hetzner/test": {"HCLOUD_TOKEN"},
}

# Annuaire des clients (app-emails.txt par client) — racine surchargeable pour les
# tests. Sert au mapping email authentifié -> client (isolation multi-tenant app#13/#14).
DEFAULT_CLIENTS_DIR = Path(os.environ.get("OA_CLIENTS_DIR", "/home/omar/clients"))
# Artefacts Hub en lecture seule pour l'état de santé SAV (jamais de SSH/mutation).
DEFAULT_HUB_API_DIR = Path(
    os.environ.get("OA_HUB_API_DIR", str(ROOT.parent / "omar-hub" / "public" / "api"))
)
_CLIENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def admin_emails() -> set[str]:
    return {
        e.strip().lower()
        for e in os.environ.get("OA_ADMIN_EMAILS", "alexwillemetz@gmail.com").split(",")
        if e.strip()
    }


def load_email_to_client(clients_dir: Path) -> dict[str, str]:
    """Construit le mapping email -> client_id en lisant clients/<id>/app-emails.txt.
    Les lignes vides et commentaires (#) sont ignorés. Casse normalisée en minuscules."""
    mapping: dict[str, str] = {}
    try:
        entries = sorted(clients_dir.iterdir())
    except OSError:
        return mapping
    for child in entries:
        if not child.is_dir():
            continue
        cid = child.name
        if cid.startswith("_") or not _CLIENT_ID_RE.match(cid):
            continue
        emails_file = child / "app-emails.txt"
        if not emails_file.exists():
            continue
        try:
            lines = emails_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw in lines:
            line = raw.strip().lower()
            if not line or line.startswith("#"):
                continue
            mapping.setdefault(line, cid)
    return mapping


def resolve_client_id(clients_dir: Path, email: str) -> str | None:
    """Retourne le client_id propriétaire de l'email authentifié, ou None si inconnu."""
    email = (email or "").strip().lower()
    if not email:
        return None
    return load_email_to_client(clients_dir).get(email)


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _pdf_escape(value: Any) -> str:
    text = str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


def devis_pdf_bytes(devis: dict[str, Any]) -> bytes:
    """Produit un PDF minimal sans dépendance externe pour l'export DIY.

    Ce n'est pas une facture ni une mise en page finale : c'est un devis lisible,
    téléchargeable, et vérifiable en smoke-test navigateur/API.
    """
    client = devis.get("client") or {}
    lines = [
        "Omar & Alex - Devis",
        f"Reference: {devis.get('id', '')}",
        f"Client: {client.get('nom') or client.get('name') or client.get('company_name') or ''}",
        f"Statut: {devis.get('statut', '')}",
        "",
        "Lignes:",
    ]
    for item in devis.get("lignes", []):
        label = item.get("label", item.get("id", "ligne"))
        mensuel = item.get("prix_mensuel")
        unique = item.get("prix_unique")
        price = []
        if mensuel is not None:
            price.append(f"{mensuel} EUR/mois")
        if unique is not None:
            price.append(f"{unique} EUR setup")
        lines.append(f"- {label}: {', '.join(price) if price else 'sur devis'}")
    lines.extend([
        "",
        f"Total mensuel HT: {devis.get('total_mensuel_eur', 0)} EUR",
        f"Total initial HT: {devis.get('total_unique_eur', 0)} EUR",
        "",
        "DIY: export pour validation humaine. Aucune action payante n'est declenchee par ce PDF.",
    ])
    text_ops = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for line in lines:
        text_ops.append(f"({_pdf_escape(line)}) Tj")
        text_ops.append("T*")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    return bytes(out)


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


def _app_vault_token() -> str:
    """Token Vault dédié omar-app. N'utilise jamais le token root utilisateur implicite."""
    token = os.environ.get("OA_APP_VAULT_TOKEN", "").strip()
    if token:
        return token
    try:
        return DEFAULT_VAULT_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _app_vault_env() -> dict[str, str] | None:
    token = _app_vault_token()
    if not token:
        return None
    env = os.environ.copy()
    env["VAULT_ADDR"] = DEFAULT_VAULT_ADDR
    env["VAULT_TOKEN"] = token
    return env


def _vault_secret(path: str, field: str) -> str:
    """Lit uniquement les chemins/champs autorisés avec le token service omar-app."""
    if field not in ALLOWED_VAULT_FIELDS.get(path, set()):
        return ""
    env = _app_vault_env()
    if env is None:
        return ""
    try:
        raw = subprocess.check_output(
            ["/usr/bin/vault", "kv", "get", "-format=json", path],
            text=True, stderr=subprocess.DEVNULL, env=env,
        )
        return json.loads(raw).get("data", {}).get("data", {}).get(field, "")
    except Exception:
        return ""


def _stripe_secret(mode: str, field: str) -> str:
    """Lit un champ Stripe via le token Vault service-scopé omar-app."""
    return _vault_secret(f"secret/stripe/{mode}", field)


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


def read_provisioning(data_dir: Path, did: str) -> dict[str, Any] | None:
    if not re.match(r"^devis-[0-9A-Za-z-]+$", did):
        return None
    path = data_dir / "provisioning" / f"{did}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def build_provisioning_contract(devis: dict[str, Any], target: str) -> dict[str, Any]:
    if target not in {"vps", "pc", "hybride"}:
        raise ValueError("target invalide")
    checks = [
        {"key": "devis_present", "label": "Devis AppOmar présent", "result": "pass", "detail": devis.get("id", "")},
        {"key": "paid_actions_none", "label": "Aucune action payante déclenchée", "result": "pass", "detail": "dry-run"},
        {"key": "go_humain_required", "label": "GO humain requis avant réel", "result": "manual", "detail": "pending_go avant provisioning réel"},
    ]
    return {
        "schema": "omartop.provisioning-contract.v1",
        "source": "appomar.api.provisioning.dry_run",
        "source_devis_id": devis["id"],
        "vps_id": target,
        "target": target,
        "mode": "dry-run",
        "paid_actions": "none",
        "go_humain": {"required": True, "provided": False, "token_present": False},
        "status": "pending_go",
        "score": 67,
        "checks": {"pass_count": 2, "fail_count": 0, "manual_count": 1, "items": checks},
        "pc_smoke": {"present": True} if target in {"pc", "hybride"} else None,
        "vps_smoke": {"present": True} if target in {"vps", "hybride"} else None,
        "errors": [],
        "warnings": ["dry-run AppOmar: aucune installation réelle sans GO H-Omar/Alex"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generated_by": "appomar-proposal-server",
        "commit_ref": None,
        "dry_run": True,
    }


def read_proposal(data_dir: Path, pid: str) -> dict[str, Any] | None:
    if not PROPOSAL_ID_RE.match(pid):
        return None
    path = data_dir / "proposals" / f"{pid}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def pricing_payload() -> dict[str, Any]:
    # V0.3 is intentionally read-only. HCLOUD_TOKEN may be injected directly; otherwise
    # read it with the omar-app Vault service token only (never /home/omar/.vault-token).
    token = os.environ.get("HCLOUD_TOKEN") or _vault_secret("secret/integrations/hetzner/test", "HCLOUD_TOKEN")
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


DEFAULT_ONBOARDING_FILE = ROOT / "onboarding-status.json"


def load_onboarding_status(onboarding_file: Path | None = None) -> dict[str, Any]:
    """Lit onboarding-status.json (tous clients). Jamais exposé tel quel : toujours
    filtré par client authentifié avant envoi."""
    path = onboarding_file or DEFAULT_ONBOARDING_FILE
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"clients": []}


def filter_onboarding_for_client(client_id: str | None, *, all_clients: bool,
                                 onboarding_file: Path | None = None) -> dict[str, Any]:
    """Isolation multi-tenant (app#13/#14) : ne renvoie QUE le dossier du client
    authentifié. Admin (all_clients) voit tout. Email inconnu -> liste vide."""
    data = load_onboarding_status(onboarding_file)
    clients = data.get("clients") or []
    if all_clients:
        return {"clients": clients}
    if not client_id:
        return {"clients": []}
    return {"clients": [c for c in clients if c.get("id") == client_id]}


def _hub_client_vps_state(hub_api_dir: Path, client_id: str) -> str | None:
    """État du VPS client tel que mesuré par le Hub (lecture seule de
    maturity-omar.json). Renvoie ex 'green'/'indeterminate' ou None si absent."""
    path = hub_api_dir / "maturity-omar.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    fields = data.get("maturity_fields") or {}
    val = fields.get(f"client_vps_{client_id}")
    return str(val) if val is not None else None


def sav_status_payload(clients_dir: Path, hub_api_dir: Path, email: str,
                       onboarding_file: Path | None = None) -> dict[str, Any]:
    """État de santé SAV du VPS du client CONNECTÉ — read-only, sans SSH ni mutation.
    Agrège : avancement onboarding (onboarding-status.json) + état mesuré par le Hub
    (maturity-omar.json client_vps_<id>). Email inconnu -> ok:False, data vides."""
    client_id = resolve_client_id(clients_dir, email)
    if not client_id:
        return {"ok": False, "error": "unknown_client", "vps": None,
                "steps": [], "summary": "Aucun VPS associé à votre compte."}
    filtered = filter_onboarding_for_client(client_id, all_clients=False,
                                            onboarding_file=onboarding_file)
    dossier = (filtered["clients"] or [{}])[0]
    steps = dossier.get("steps") or []
    done = sum(1 for s in steps if s.get("statut") == "done")
    total = len(steps)
    pct = round(100 * done / total) if total else 0
    hub_state = _hub_client_vps_state(hub_api_dir, client_id)
    # statut global lisible client, dérivé d'artefacts existants uniquement
    if hub_state in {"green", "healthy", "ok"}:
        health = "healthy"
    elif hub_state in {"red", "blocked"}:
        health = "attention"
    elif total and done == total:
        health = "healthy"
    elif done:
        health = "en_cours"
    else:
        health = "indetermine"
    return {
        "ok": True,
        "vps": {"client_id": client_id, "label": dossier.get("label", client_id)},
        "health": health,
        "hub_measured_state": hub_state,  # peut être None si le Hub n'a pas mesuré
        "onboarding": {"done": done, "total": total, "pct": pct},
        "steps": steps,
        "source": "onboarding-status.json + Hub maturity-omar.json (read-only)",
        "read_only": True,
    }


class ProposalHandler(BaseHTTPRequestHandler):
    server_version = "OmarAppProposalServer/0.5"

    @property
    def data_dir(self) -> Path:
        return self.server.data_dir  # type: ignore[attr-defined]

    @property
    def clients_dir(self) -> Path:
        return self.server.clients_dir  # type: ignore[attr-defined]

    @property
    def hub_api_dir(self) -> Path:
        return self.server.hub_api_dir  # type: ignore[attr-defined]

    @property
    def onboarding_file(self) -> Path:
        return self.server.onboarding_file  # type: ignore[attr-defined]

    def auth_email(self) -> str:
        """Email authentifié injecté par le forward_auth OAuth en amont (vhost).
        En dehors de ce chemin, l'en-tête est absent -> chaîne vide."""
        return self.headers.get("X-Auth-Request-Email", "").strip().lower()

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("proposal_server " + fmt % args + "\n")

    def _serve_file(self, fp: Path, ctype: str) -> None:
        body = fp.read_bytes()
        self.send_response(200)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def operator_authorized(self) -> bool:
        expected = self.server.api_token  # type: ignore[attr-defined]
        header = self.headers.get("authorization", "")
        if header.startswith("Bearer "):
            provided = header[len("Bearer "):].strip()
        else:
            provided = self.headers.get("x-oa-token", "").strip()
        return bool(provided) and hmac.compare_digest(provided, expected)

    def proposal_auth_context(self) -> dict[str, Any] | None:
        """Auth proposals app#13.

        Deux chemins sont acceptés :
        - token opérateur (Bearer/X-OA-Token) pour automatisations internes ;
        - email OAuth injecté par Caddy forward_auth, mappé vers clients/<id>/app-emails.txt.
        """
        email = self.auth_email()
        client_id = resolve_client_id(self.clients_dir, email)
        is_admin = bool(email) and email in admin_emails()
        if self.operator_authorized():
            return {"mode": "operator", "email": email, "client_id": client_id, "is_admin": True}
        if is_admin:
            return {"mode": "admin", "email": email, "client_id": client_id, "is_admin": True}
        if client_id:
            return {"mode": "client", "email": email, "client_id": client_id, "is_admin": False}
        return None

    def can_read_proposal(self, proposal: dict[str, Any], ctx: dict[str, Any]) -> bool:
        if ctx.get("is_admin") or ctx.get("mode") == "operator":
            return True
        owner_client_id = proposal.get("owner_client_id")
        return bool(owner_client_id) and owner_client_id == ctx.get("client_id")

    def reject_unauthorized(self) -> None:
        self.send_json(401, {"ok": False, "error": "unauthorized"})

    def reject_forbidden(self) -> None:
        self.send_json(403, {"ok": False, "error": "forbidden"})

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        # Portail unifié — pages servies par le serveur (hors build.py → survivent au rebuild)
        APP_PAGES = {
            "/": "home.html",
            "/devis/": "devis.html", "/devis": "devis.html",
            "/onboarding/": "onboarding.html", "/onboarding": "onboarding.html",
            "/sav/": "sav.html", "/sav": "sav.html",
            "/compte/": "compte.html", "/compte": "compte.html",
            "/aide/": "aide.html", "/aide": "aide.html",
            "/changelog/": "changelog.html", "/changelog": "changelog.html",
            "/admin/catalog/": "admin-catalog.html", "/admin/catalog": "admin-catalog.html",
        }
        # Canonical redirects: old routes → new canonical routes
        REDIRECTS = {
            "/config/": "/onboarding/", "/config": "/onboarding/",
            "/buy/": "/devis/", "/buy": "/devis/",
            "/factures/": "/compte/", "/factures": "/compte/",
            "/jab/": "/", "/jab": "/",
        }
        redirect_target = REDIRECTS.get(path)
        if redirect_target:
            self.send_response(301)
            self.send_header("location", redirect_target)
            self.send_header("content-length", "0")
            self.end_headers()
            return
        page_file = APP_PAGES.get(path)
        if page_file:
            fp = ROOT / "pages-app" / page_file
            if fp.exists():
                self._serve_file(fp, "text/html; charset=utf-8")
                return
        # assets du portail (_portal.js)
        if path.startswith("/pages-app/") and path.endswith(".js"):
            fp = ROOT / "pages-app" / Path(path).name
            if fp.exists():
                self._serve_file(fp, "application/javascript; charset=utf-8")
                return
        if path == "/api/onboarding/status":
            # Isolation multi-tenant (app#13/#14) : un client connecté ne voit QUE
            # son propre dossier. L'email vient du forward_auth OAuth amont.
            # Sans email authentifié, renvoie une liste vide (prospects en tunnel).
            # V0.5.0: ajout champ auth_required pour traçabilité.
            email = self.auth_email()
            is_admin = bool(email) and email in admin_emails()
            client_id = resolve_client_id(self.clients_dir, email)
            payload = filter_onboarding_for_client(
                client_id, all_clients=is_admin, onboarding_file=self.onboarding_file)
            if not email:
                payload["auth_required"] = True
            self.send_json(200, payload)
            return
        if path == "/api/sav/status":
            # SAV read-only : santé du VPS du client connecté, lue d'artefacts
            # existants (onboarding-status.json + Hub maturity-omar.json). Pas de SSH.
            email = self.auth_email()
            payload = sav_status_payload(self.clients_dir, self.hub_api_dir, email,
                                         onboarding_file=self.onboarding_file)
            self.send_json(200 if payload.get("ok") else 403, payload)
            return
        if self.path == "/api/health":
            self.send_json(200, {"ok": True, "service": "omar-app-proposals", "version": "V0.5.0"})
            return
        if self.path == "/api/catalog":
            self.send_json(200, load_catalog())
            return
        if self.path.startswith("/api/devis/"):
            did = self.path[len("/api/devis/"):].split("?", 1)[0]
            wants_pdf = did.endswith(".pdf")
            if wants_pdf:
                did = did[:-4]
            dv = read_devis(self.data_dir, did)
            if not dv:
                self.send_json(404, {"ok": False, "error": "devis_not_found"})
                return
            if wants_pdf:
                body = devis_pdf_bytes(dv)
                self.send_response(200)
                self.send_header("content-type", "application/pdf")
                self.send_header("content-disposition", f'attachment; filename="{did}.pdf"')
                self.send_header("content-length", str(len(body)))
                self.send_header("cache-control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_json(200, {"ok": True, "devis": dv})
            return
        if self.path.startswith("/api/provisioning/"):
            did = self.path[len("/api/provisioning/"):].split("?", 1)[0]
            contract = read_provisioning(self.data_dir, did)
            if not contract:
                self.send_json(404, {"ok": False, "error": "provisioning_not_found"})
                return
            self.send_json(200, {"ok": True, "provisioning": contract})
            return
        if self.path == "/api/hetzner/pricing":
            self.send_json(200, pricing_payload())
            return
        prefix = "/api/proposals/"
        if self.path.startswith(prefix):
            ctx = self.proposal_auth_context()
            if ctx is None:
                self.reject_unauthorized()
                return
            pid = self.path[len(prefix):].split("?", 1)[0]
            proposal = read_proposal(self.data_dir, pid)
            if not proposal:
                self.send_json(404, {"ok": False, "error": "proposal_not_found"})
                return
            if not self.can_read_proposal(proposal, ctx):
                self.reject_forbidden()
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
        if self.path == "/api/provisioning/dry-run":
            self.handle_provisioning_dry_run()
            return
        if self.path == "/api/stripe-webhook":
            self.handle_stripe_webhook()
            return
        if self.path != "/api/proposals":
            self.send_json(404, {"ok": False, "error": "not_found"})
            return
        ctx = self.proposal_auth_context()
        if ctx is None:
            self.reject_unauthorized()
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 200_000:
                raise ValueError("invalid content-length")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("payload must be object")
            if ctx.get("mode") == "client":
                contact_email = str(payload.get("client_profile", {}).get("contact_email", "")).strip().lower()
                if contact_email and contact_email != ctx.get("email"):
                    self.reject_forbidden()
                    return
                payload = dict(payload)
                payload["owner_client_id"] = ctx["client_id"]
                payload["owner_email"] = ctx["email"]
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
        for raw_item in item_ids:
            if isinstance(raw_item, str):
                iid = raw_item
                qty = 1
            elif isinstance(raw_item, dict):
                iid = str(raw_item.get("id", ""))
                try:
                    qty = max(1, int(raw_item.get("qty", 1)))
                except (TypeError, ValueError):
                    qty = 1
            else:
                continue
            p = catalog.get(iid)
            if not p:
                continue
            line_mensuel = p.get("prix_mensuel")
            line_unique = p.get("prix_unique")
            lignes.append({"id": p["id"], "label": p["label"], "qty": qty,
                           "prix_mensuel": line_mensuel, "prix_unique": line_unique})
            mensuel += (line_mensuel or 0) * qty
            unique += (line_unique or 0) * qty
        if not lignes:
            self.send_json(422, {"ok": False, "error": "aucun item catalogue valide"})
            return
        # reprise : si devis_id fourni et existe (et pas encore payé), on met à jour le même
        existing = read_devis(self.data_dir, str(payload.get("devis_id", "")))
        if existing and existing.get("statut") != "achete":
            did = existing["id"]
            devis = {**existing, "lignes": lignes, "total_mensuel_eur": mensuel,
                     "total_unique_eur": unique,
                     "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        else:
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

    def handle_provisioning_dry_run(self) -> None:
        """Pont AppOmar → OmarTop : produit un contrat provisioning dry-run.

        Aucun provisioning réel, aucun call provider, aucune dépense. Le contrat est
        stocké pour Hub/QG et reste en pending_go jusqu'à arbitrage humain.
        """
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            did = str(payload.get("devis_id", ""))
            target = str(payload.get("target", "pc"))
        except Exception as exc:
            self.send_json(422, {"ok": False, "error": str(exc)})
            return
        devis = read_devis(self.data_dir, did)
        if not devis:
            self.send_json(404, {"ok": False, "error": "devis_not_found"})
            return
        try:
            contract = build_provisioning_contract(devis, target)
        except ValueError as exc:
            self.send_json(422, {"ok": False, "error": str(exc)})
            return
        out_dir = self.data_dir / "provisioning"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{did}.json").write_bytes(json_bytes(contract))
        self.send_json(201, {"ok": True, "provisioning": contract})

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
    parser.add_argument("--clients-dir", type=Path, default=DEFAULT_CLIENTS_DIR)
    parser.add_argument("--hub-api-dir", type=Path, default=DEFAULT_HUB_API_DIR)
    parser.add_argument("--onboarding-file", type=Path, default=DEFAULT_ONBOARDING_FILE)
    args = parser.parse_args()
    api_token = os.environ.get("OA_PROPOSALS_TOKEN", "").strip()
    if len(api_token) < 32:
        sys.exit("OA_PROPOSALS_TOKEN manquant ou trop court (>=32 chars requis) — refus de démarrer sans auth (app#13)")
    server = ReusableServer((args.host, args.port), ProposalHandler)
    server.data_dir = args.data_dir  # type: ignore[attr-defined]
    server.clients_dir = args.clients_dir  # type: ignore[attr-defined]
    server.hub_api_dir = args.hub_api_dir  # type: ignore[attr-defined]
    server.onboarding_file = args.onboarding_file  # type: ignore[attr-defined]
    server.api_token = api_token  # type: ignore[attr-defined]
    args.data_dir.mkdir(parents=True, exist_ok=True)
    print(f"serving omar-app proposals on http://{args.host}:{args.port} data={args.data_dir}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
