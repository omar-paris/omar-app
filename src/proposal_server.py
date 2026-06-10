#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hmac
import json
import os
import re
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
            self.send_json(200, {"ok": True, "service": "omar-app-proposals", "version": "V0.3.0"})
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
