# Omar App — Build Report V0.3.0

Date: 2026-06-09
Domain: `app.omar.paris`

## Scope

V0.3.0 adds the first server-side layer behind AppOmar:

- proposal storage via `POST /api/proposals`;
- operator reread via `GET /api/proposals/<id>`;
- Hetzner pricing read-only endpoint via `GET /api/hetzner/pricing`;
- browser button "Enregistrer la proposition" from `/config/`.

## Delivered

- `src/proposal_server.py` — minimal stdlib HTTP server.
- `scripts/run-proposal-server.sh` — runner with optional Vault read for Hetzner read-only token.
- `deploy/app.omar.paris.caddy` — persistent Caddy snippet for API reverse proxy.
- `.gitignore` excludes runtime `var/proposals/`.
- `/config/` now calls:
  - `/api/hetzner/pricing` on load;
  - `/api/proposals` when operator/user clicks save.

## Runtime state

Server:

```txt
127.0.0.1:8096
```

Live API:

```txt
https://app.omar.paris/api/health          200
https://app.omar.paris/api/hetzner/pricing 200 live_readonly
POST /api/proposals                        201
GET /api/proposals/<id>                    200
```

## Safety

- No paid Hetzner action exists in the server.
- Pricing endpoint is read-only only.
- Proposal storage rejects payloads unless:
  - `type = configuration_proposal`;
  - `status = pending_human_go`;
  - `safety.paid_actions = none`;
  - `hetzner_payload.mode = dry_run_no_paid_resource`.
- Runtime proposal JSON is stored locally under `var/proposals/` and excluded from git.

## Verification

```txt
python3 -m pytest -q
12 passed

python3 scripts/build.py
built 8 routes into /home/omar/23-Offre/actifs/omar-app/public

node --check public/assets/app.js
OK

git diff --check
OK
```

Browser proof:

```txt
V0.3.0 visible
Pricing Hetzner : live_readonly, 3 packs, paid_actions=none
Click Enregistrer la proposition → Proposition enregistrée: proposal-...
Console JS: 0 errors
```

## Persistence caveat

Caddy runtime was patched through the Caddy Admin API. The persistent snippet exists at:

```txt
deploy/app.omar.paris.caddy
```

The proposal server is currently running as a Hermes-managed background process. For durable reboot survival, install it as a user service or supervised process next.

## Next step

V0.4 should connect the stored proposal to a real operator screen:

1. list latest proposals;
2. inspect proposal;
3. generate exact Hetzner create payload;
4. show GO/NO-GO checklist;
5. only then allow H-Omar/Alex to run provisioning.
