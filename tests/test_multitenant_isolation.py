"""Isolation multi-tenant (app#13/#14) + SAV read-only (app#31).

Vérifie qu'un client connecté ne voit QUE ses propres données :
- /api/onboarding/status filtre par l'email authentifié (X-Auth-Request-Email)
- un email != ne voit pas le dossier d'un autre client
- email inconnu / absent -> données vides
- /api/sav/status renvoie l'état du VPS du client connecté, sans SSH ni mutation
"""
from __future__ import annotations

import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "x" * 40  # >=32, requis pour démarrer le serveur (app#13)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def make_clients(tmp_path: Path) -> Path:
    """Annuaire clients fixture : alice->client-a, bob->client-b, plus un _template ignoré."""
    clients = tmp_path / "clients"
    (clients / "client-a").mkdir(parents=True)
    (clients / "client-b").mkdir(parents=True)
    (clients / "_template").mkdir(parents=True)
    (clients / "client-a" / "app-emails.txt").write_text(
        "# emails client A\nalice@example.com\n", encoding="utf-8"
    )
    (clients / "client-b" / "app-emails.txt").write_text(
        "bob@example.com\n", encoding="utf-8"
    )
    (clients / "_template" / "app-emails.txt").write_text(
        "ignored@example.com\n", encoding="utf-8"
    )
    return clients


def make_hub(tmp_path: Path) -> Path:
    hub = tmp_path / "hub-api"
    hub.mkdir(parents=True)
    (hub / "maturity-omar.json").write_text(
        json.dumps({
            "maturity_fields": {
                "client_vps_client-a": "green",
                "client_vps_client-b": "indeterminate",
            }
        }),
        encoding="utf-8",
    )
    return hub


def start_server(tmp_path: Path):
    """Démarre le serveur avec un onboarding-status.json à 2 clients (client-a, client-b)."""
    # onboarding-status.json est lu depuis ROOT ; on le laisse tel quel et on injecte
    # via un data-dir/clients-dir/hub-api-dir fixtures. Mais le statut onboarding est
    # lu depuis ROOT/onboarding-status.json, donc on s'appuie sur des ids fixtures
    # absents du fichier réel : le filtrage doit alors renvoyer une liste vide pour
    # les clients fixtures inconnus du fichier. Pour tester le filtrage réel, on écrit
    # un onboarding-status.json temporaire via la variable d'env n'existant pas :
    # on copie donc le serveur dans un cwd dédié.
    work = tmp_path / "work"
    work.mkdir()
    (work / "src").mkdir()
    # lien symbolique vers le module + site_data
    for f in ("proposal_server.py", "site_data.py"):
        (work / "src" / f).symlink_to(ROOT / "src" / f)
    # catalogue minimal + packs proviennent de site_data, pas de catalog requis
    (work / "onboarding-status.json").write_text(
        json.dumps({
            "clients": [
                {"id": "client-a", "label": "Client A",
                 "steps": [{"label": "VPS", "statut": "done"},
                           {"label": "CRM", "statut": "cur"}]},
                {"id": "client-b", "label": "Client B",
                 "steps": [{"label": "VPS", "statut": "done"}]},
            ]
        }),
        encoding="utf-8",
    )
    clients = make_clients(tmp_path)
    hub = make_hub(tmp_path)
    port = free_port()
    proc = subprocess.Popen(
        ["python3", "src/proposal_server.py", "--host", "127.0.0.1", "--port", str(port),
         "--data-dir", str(tmp_path / "data"),
         "--clients-dir", str(clients), "--hub-api-dir", str(hub),
         "--onboarding-file", str(work / "onboarding-status.json")],
        cwd=work,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"OA_PROPOSALS_TOKEN": TOKEN, "PATH": __import__("os").environ.get("PATH", "")},
    )
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.2).read()
            return proc, port
        except Exception:
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=1)
                raise AssertionError(f"server exited early\nOUT={out}\nERR={err}")
            time.sleep(0.05)
    proc.terminate()
    raise AssertionError("server did not become ready")


def get(port: int, path: str, email: str | None = None):
    headers = {"accept": "application/json"}
    if email is not None:
        headers["X-Auth-Request-Email"] = email
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def test_onboarding_status_isolates_per_authenticated_email(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        # Alice ne voit QUE client-a
        st, alice = get(port, "/api/onboarding/status", "alice@example.com")
        assert st == 200
        ids_alice = {c["id"] for c in alice["clients"]}
        assert ids_alice == {"client-a"}
        assert "client-b" not in ids_alice

        # Bob ne voit QUE client-b
        st, bob = get(port, "/api/onboarding/status", "bob@example.com")
        assert st == 200
        ids_bob = {c["id"] for c in bob["clients"]}
        assert ids_bob == {"client-b"}

        # Croisé : les dossiers ne se recouvrent pas
        assert ids_alice.isdisjoint(ids_bob)
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_onboarding_status_unknown_or_missing_email_sees_nothing(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        st, unknown = get(port, "/api/onboarding/status", "intrus@example.com")
        assert st == 200
        assert unknown["clients"] == []

        # aucun en-tête d'auth -> aucune donnée (l'ancienne faille renvoyait TOUT)
        st, anon = get(port, "/api/onboarding/status", None)
        assert st == 200
        assert anon["clients"] == []
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_admin_email_sees_all_clients(tmp_path):
    import os
    proc, port = start_server_admin(tmp_path)
    try:
        st, data = get(port, "/api/onboarding/status", "boss@example.com")
        assert st == 200
        assert {c["id"] for c in data["clients"]} == {"client-a", "client-b"}
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def start_server_admin(tmp_path: Path):
    """Variante avec OA_ADMIN_EMAILS=boss@example.com."""
    import os
    work = tmp_path / "work"
    work.mkdir()
    (work / "src").mkdir()
    for f in ("proposal_server.py", "site_data.py"):
        (work / "src" / f).symlink_to(ROOT / "src" / f)
    (work / "onboarding-status.json").write_text(
        json.dumps({"clients": [
            {"id": "client-a", "label": "A", "steps": []},
            {"id": "client-b", "label": "B", "steps": []},
        ]}),
        encoding="utf-8",
    )
    clients = make_clients(tmp_path)
    hub = make_hub(tmp_path)
    port = free_port()
    proc = subprocess.Popen(
        ["python3", "src/proposal_server.py", "--host", "127.0.0.1", "--port", str(port),
         "--data-dir", str(tmp_path / "data"),
         "--clients-dir", str(clients), "--hub-api-dir", str(hub),
         "--onboarding-file", str(work / "onboarding-status.json")],
        cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env={"OA_PROPOSALS_TOKEN": TOKEN,
             "OA_ADMIN_EMAILS": "boss@example.com",
             "PATH": os.environ.get("PATH", "")},
    )
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.2).read()
            return proc, port
        except Exception:
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=1)
                raise AssertionError(f"server exited early\nOUT={out}\nERR={err}")
            time.sleep(0.05)
    proc.terminate()
    raise AssertionError("server did not become ready")


def test_sav_status_returns_connected_client_health_readonly(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        # Alice : VPS client-a, hub 'green' -> healthy
        st, alice = get(port, "/api/sav/status", "alice@example.com")
        assert st == 200
        assert alice["ok"] is True
        assert alice["read_only"] is True
        assert alice["vps"]["client_id"] == "client-a"
        assert alice["hub_measured_state"] == "green"
        assert alice["health"] == "healthy"
        # ne contient aucune donnée d'un autre client
        assert "client-b" not in json.dumps(alice)
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_sav_status_unknown_email_is_forbidden_and_empty(tmp_path):
    proc, port = start_server(tmp_path)
    try:
        st, data = get(port, "/api/sav/status", "intrus@example.com")
        assert st == 403
        assert data["ok"] is False
        assert data["steps"] == []
        assert data["vps"] is None
    finally:
        proc.terminate()
        proc.wait(timeout=3)
