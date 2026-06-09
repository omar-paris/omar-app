# Omar App — Build Report V0.2.0

Date: 2026-06-09
Domain: `app.omar.paris`

## Scope

V0.2.0 turns `/config/` from a static description into a first usable configuration wizard.

## Delivered

- `V0.2.0` version marker across generated pages.
- `/config/` wizard with:
  - company/activity/contact/domain fields;
  - need/urgency/budget/existing-tools fields;
  - Hetzner pack selector `starter/pro/max`;
  - location selector `fsn1/nbg1/hel1`;
  - backups flag.
- Client-side `configuration_proposal` JSON generation.
- Dry-run `hetzner_payload.create_server_payload`.
- `pending_human_go` status before any paid resource.
- Apps L1 expected list aligned to OmarTop → Hub chain.
- Public JSON contracts:
  - `/api/oa-start-packs.json`
  - `/api/apps-l1.json`

## Safety

No Hetzner API call is executed by the browser.
No paid action is automated.
Generated proposals explicitly mark:

```txt
status: pending_human_go
paid_actions: none
```

## Verification

```txt
python3 -m pytest -q
9 passed

python3 scripts/build.py
built 8 routes into /home/omar/23-Offre/actifs/omar-app/public

node --check public/assets/app.js
OK

git diff --check
OK
```

## Live probes

```txt
https://app.omar.paris/config/                 200
https://app.omar.paris/api/oa-start-packs.json 200
https://app.omar.paris/api/apps-l1.json        200
```

Browser JS proof:

```json
{
  "ok": true,
  "status": "pending_human_go",
  "server": "cax21",
  "apps": 10,
  "paid": "none",
  "download": "oa-client-client-demo-01-configuration-proposal.json"
}
```

## Remaining work

1. Add backend `POST /api/proposals` to store proposal JSON server-side.
2. Replace static monthly estimates with live Hetzner pricing API read-only values.
3. Feed selected Apps L1 into Hub client context.
4. Add operator screen to transform `pending_human_go` into actual provision after explicit GO.
