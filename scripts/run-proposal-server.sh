#!/usr/bin/env bash
set -euo pipefail
cd /home/omar/23-Offre/actifs/omar-app
export VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8202}"
if [[ -z "${HCLOUD_TOKEN:-}" && -f /home/omar/.vault-token ]] && command -v vault >/dev/null 2>&1; then
  export VAULT_TOKEN="$(cat /home/omar/.vault-token)"
  HCLOUD_TOKEN="$(vault kv get -format=json secret/oadmin/integrations/hetzner | python3 -c 'import sys,json; print(json.load(sys.stdin)["data"]["data"].get("HCLOUD_TOKEN", ""))')"
  export HCLOUD_TOKEN
  unset VAULT_TOKEN
fi
exec python3 src/proposal_server.py --host 127.0.0.1 --port 8096 --data-dir /home/omar/23-Offre/actifs/omar-app/var
