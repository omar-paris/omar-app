#!/usr/bin/env bash
set -euo pipefail
cd /home/omar/23-Offre/actifs/omar-app

# Secrets boundary (app#38): this runner must not read the operator/root Vault token
# from /home/omar/.vault-token. Inject either direct runtime secrets (for example
# HCLOUD_TOKEN) or a least-privilege omar-app Vault token via OA_APP_VAULT_TOKEN or
# OA_APP_VAULT_TOKEN_FILE. See docs/security/vault-policies.md.
export OA_APP_VAULT_ADDR="${OA_APP_VAULT_ADDR:-${VAULT_ADDR:-http://127.0.0.1:8202}}"
export OA_APP_VAULT_TOKEN_FILE="${OA_APP_VAULT_TOKEN_FILE:-/home/omar/.config/omar-app/vault-token}"

exec python3 src/proposal_server.py --host 127.0.0.1 --port 8096 --data-dir /home/omar/23-Offre/actifs/omar-app/var
