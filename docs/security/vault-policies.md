# Omar App — Vault least-privilege policy (app#38)

## Objectif

Remplacer l'usage implicite du token root/opérateur par un token de service dédié `omar-app`, limité aux secrets réellement lus par l'application.

## Boundary runtime

Le runner `scripts/run-proposal-server.sh` ne lit plus `/home/omar/.vault-token`.

Secrets acceptés par le process :

- injection directe d'environnement par le superviseur : `HCLOUD_TOKEN` si nécessaire ;
- token Vault service-scopé via `OA_APP_VAULT_TOKEN` ;
- ou fichier service-scopé `OA_APP_VAULT_TOKEN_FILE`, défaut `/home/omar/.config/omar-app/vault-token`.

Le code ignore volontairement `VAULT_TOKEN` seul pour éviter qu'un token root shell/opérateur soit consommé par l'app.

## Chemins Vault autorisés dans le code

Allowlist applicative :

- `secret/stripe/test` : `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `secret/stripe/live` : `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `secret/integrations/hetzner/test` : `HCLOUD_TOKEN`

Tout autre chemin/champ est refusé avant appel au CLI Vault.

## Policy Vault cible

À appliquer par un opérateur Vault autorisé, hors déploiement applicatif :

```hcl
path "secret/data/stripe/test" {
  capabilities = ["read"]
}

path "secret/data/stripe/live" {
  capabilities = ["read"]
}

path "secret/data/integrations/hetzner/test" {
  capabilities = ["read"]
}
```

Nom suggéré : `omar-app-readonly`.

## Bootstrap token service

Exemple opérateur (ne pas committer les sorties) :

```bash
vault policy write omar-app-readonly docs/security/vault-policies.hcl
vault token create -policy=omar-app-readonly -period=24h -renewable=true
install -d -m 700 /home/omar/.config/omar-app
# Coller uniquement le token de service dans ce fichier, jamais le root token.
install -m 600 /dev/stdin /home/omar/.config/omar-app/vault-token
```

Si le mode AppRole/Machine Identity est disponible, préférer AppRole/Infisical et injecter un token court-vivant au démarrage plutôt qu'un token statique.

## Rotation minimale avant premier client payant

1. Révoquer tout token root utilisé par un service applicatif.
2. Créer `omar-app-readonly` et un token/service identity dédié.
3. Redémarrer `omar-app` avec `OA_APP_VAULT_TOKEN` ou `OA_APP_VAULT_TOKEN_FILE`.
4. Vérifier que `/api/hetzner/pricing`, checkout Stripe et webhook Stripe fonctionnent sans `VAULT_TOKEN` hérité.
5. Rotater les secrets historiquement exposés : AgentMail, tokens Vault applicatifs, tokens provider lus par omar-app.
6. Migrer vers Infisical machine identities quand le modèle multi-tenant est prêt.

## Non fait par cette PR

- Pas de mutation Vault réelle.
- Pas de rotation effective de secrets.
- Pas de migration Infisical.

Ces actions restent des opérations humaines/infra séparées avant production client.
