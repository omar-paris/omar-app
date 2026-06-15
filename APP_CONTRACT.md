# OA App Contract — app.omar.paris

> Date : 2026-06-08. Statut : V0 draft. Source : `/home/omar/11-Pilotage/doctrine/oa-operating-manifest/APP-V0-PRD.md`.

## Identity

- App ID: `app`
- Internal name/codename: `AppOmar`
- Filesystem path for now: `/home/omar/23-Offre/actifs/omar-app`
- Product name: `Omar App`
- Public domain: `app.omar.paris`
- Naming rule: `AppOmar` is the internal codename; the customer-facing surface remains `app.omar.paris` / `Omar App`.
- QG remains distinct: internal CORE OA registry/backoffice, not the customer portal.
- Do not introduce `AAPP` unless Alex/H-Omar later define a distinct acronym; it is too ambiguous for now.
- Code namespace recommendation: `app_omar` or `oa_app` at build time, but choose one before backend implementation.
- Stack: CORE OA
- Tenant/client: multi-tenant, à définir
- Public/private/tailnet-only: public avec authentification obligatoire pour le portail client et `/api/proposals*` (OAuth Google via Caddy `forward_auth` côté vhost public ; token opérateur >=32 chars uniquement pour accès interne direct au serveur).
- Repo/path: `/home/omar/23-Offre/actifs/omar-app`

## Objective

Primary job-to-be-done:

> Transformer un prospect/client en configuration OA exploitable : compte, onboarding conversationnel, besoins, outils existants, proposition de configuration, support et suivi.

## Audience

- Prospect OA
- Client OA
- Alex/OA operator
- Agents OA via données structurées

## Routes/pages V0

```txt
/
  Accueil portail client/prospect.

/onboarding
  Formulaire + conversation chatbot pour définir besoin, objectifs, livrables, outils, entreprise, domaine, préférences.

/config
  Wizard actionnable qui produit une configuration OA Start.

/buy
  Démarrage commande/demande de devis/paiement placeholder.

/sav
  Support, bugs, incidents, demandes, feedback.

/factures
  Factures/abonnement placeholder V0.

/compte
  Entreprise, membres, rôles, domaines, connexions, préférences.
```

## Core concepts

### Onboarding

Onboarding = formulaire + conversation.

Collecte :

- entreprise ;
- objectifs ;
- livrables attendus ;
- outils existants ;
- domaine actuel ou achat ;
- préférences ;
- ressources ;
- contraintes.

### Config

Config = wizard actionnable.

V0 propose une option principale :

```txt
Pack OA Start
- VPS Hetzner
- domaine/email Infomaniak si nécessaire
- compte Omar client
- Hub local
- agent Hermes OA
- support/SAV via App
- configuration initiale accompagnée
```

### Connexions

- Nango = L2 pour le moment.
- Le modèle App doit prévoir `connection_intent` compatible OAuth/Nango plus tard.
- Infisical = secrets machine/client cible.
- Hermes Agent Vault reste distinct pour runtime agents.

## Data boundaries

- Chaque client ne voit que ses données (`/api/onboarding/status`, `/api/sav/status`, `/api/proposals/{id}` filtrés par email OAuth → `clients/<id>/app-emails.txt`).
- `/api/proposals` refuse tout POST/GET sans credential valide : OAuth client connu/admin ou token opérateur interne.
- Pas de secrets en clair.
- Pas de données inter-tenant visibles.
- Les tokens/API keys ne sont jamais stockés dans le repo.
- Les secrets runtime `omar-app` doivent venir soit d'une injection directe du superviseur, soit d'un token Vault service-scopé (`OA_APP_VAULT_TOKEN` ou `OA_APP_VAULT_TOKEN_FILE`) ; le token root/opérateur `/home/omar/.vault-token` est interdit côté runner applicatif.
- Les chemins Vault applicatifs autorisés sont documentés dans `docs/security/vault-policies.md` et limités à Stripe test/live + Hetzner pricing read-only.

## Data model draft

```yaml
client_profile:
  company_name:
  activity:
  contacts:
  domain:
  existing_tools:
  goals:
  expected_deliverables:
  preferences:

onboarding_session:
  status: draft | submitted | needs_clarification | ready_for_config
  conversation_summary:
  missing_information:

configuration_proposal:
  pack: oa-start
  providers:
    hetzner:
    infomaniak:
    phone_operator:
  apps:
  integrations:
  estimated_costs:
  next_actions:

support_request:
  type: bug | request | incident | question
  priority:
  status:
```

## Non-goals V0

- Pas de paiement complet complexe.
- Pas de marketplace multi-options.
- Pas de CRM complet.
- Pas de provider automation risquée sans validation.
- Pas de Nango obligatoire.
- Pas de promesse opérateur mobile géré OA tant que modèle légal/facturation non tranché.

## Success criteria V0

- Un prospect peut exprimer son besoin.
- OA reçoit une synthèse exploitable.
- Une configuration recommandée est produite.
- Le client comprend inclus/non inclus.
- Une prochaine action interne est créée.
- QG/Lab peuvent suivre l'état.

## Build gates

- Version visible.
- Changelog visible.
- Routes fonctionnelles.
- No secrets.
- Test/smoke minimal.
- Contract mis à jour avant build.
