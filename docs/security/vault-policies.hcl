# Vault policy for omar-app service token (app#38).
# KV v2 paths use secret/data/... for policy definitions.

path "secret/data/stripe/test" {
  capabilities = ["read"]
}

path "secret/data/stripe/live" {
  capabilities = ["read"]
}

path "secret/data/integrations/hetzner/test" {
  capabilities = ["read"]
}
