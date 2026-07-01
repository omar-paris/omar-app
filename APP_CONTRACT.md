# OA App Contract — app.omar.paris

> Date : 2026-06-26. Statut : V0.5.0. Source : A2Z tunnel build (issue omar-app#46).

## Identity

- App ID: `app`
- Internal name/codename: `AppOmar`
- Filesystem path for now: `/home/omar/23-Offre/actifs/omar-app`
- Product name: `Omar App`
- Public domain: `app.omar.paris`
- Naming rule: `AppOmar` is the internal codename; the customer-facing surface remains `app.omar.paris` / `Omar App`.
- QG remains distinct: internal CORE OA registry/backoffice, not the customer portal.
- Stack: CORE OA
- Tenant/client: multi-tenant
- Public/private/tailnet-only: public avec authentification obligatoire pour le portail client et `/api/proposals*` (OAuth Google via Caddy `forward_auth` côté vhost public ; token opérateur >=32 chars uniquement pour accès interne direct au serveur).
- Repo/path: `/home/omar/23-Offre/actifs/omar-app`

## Objective

Primary job-to-be-done:

> Transformer un prospect/client en configuration OA exploitable via le tunnel A→Z : onboarding conversationnel → devis → Stripe test/simulation → provisioning timeline → agent_spec.

## Audience

- Prospect OA
- Client OA
- Alex/OA operator
- Agents OA via données structurées

## Routes/pages V0.5.0

```txt
/
  Accueil portail client/prospect. CTA principal vers /onboarding/.

/onboarding/
  Tunnel conversationnel multi-étapes mobile-first :
  1. Identité (qui êtes-vous ?)
  2. Objectifs (que veut votre assistant ?)
  3. Outils (comment travaillez-vous aujourd'hui ?)
  4. Infra (VPS/PC/hybride — ou "je ne sais pas")
  5. Préférences agent (nom, ton, autonomie)
  6. Récap → POST /api/onboarding → lien de reprise `record_id` → simulation configuration → /devis/

  Reprise : `GET /api/onboarding/<record_id>` recharge les sections validées,
  `completed_sections`, `current_step`, `record` et `agent_profile`.
  Simulation vendable : `POST /api/onboarding/<record_id>/simulate` prévisualise
  `agent_spec` + `provisioning_preview` en dry-run, `paid_actions=none`.

/devis/
  Composez votre solution : formule + modules + prestations.
  Autosave continu, lien repreneur, checkout Stripe test.

/sav/
  Support, bugs, incidents, demandes, feedback. Diagnostic VPS read-only.

/compte/
  Entreprise, membres, rôles, domaines, connexions, préférences.

/aide/
  Aide contextuelle : quoi faire selon l'état du client.

/changelog/
  Historique des versions Omar App.

/admin/catalog/
  Édition catalogue (admin only).

# Routes historiques redirigées (compat) :
/config/  → 301 /onboarding/
/buy/     → 301 /devis/
/factures/ → 301 /compte/
/jab/     → supprimé (spécifique pilote, pas canonique)
```

## Core concepts

### Onboarding conversationnel (V0.5.0)

Onboarding = tunnel multi-étapes avec chat simulé + collecte structurée.

Collecte progressive :
- identité client et activité ;
- objectifs pro et personnels autorisés ;
- nom de l'agent, personnalité (ton, tutoiement/vouvoiement, autonomie, seuil de validation) ;
- canaux : AppOmar, Telegram, email, Google/Microsoft, autres plus tard ;
- notifications : urgences, résumé quotidien, relances, documents à valider ;
- périmètre d'accès : pro, perso limité, sujets interdits, validation obligatoire ;
- infrastructure préférée : VPS managé, PC, hybride, "je ne sais pas" ;
- appareils : PC/Mac/mobile, OS, accès admin, Tailscale possible ;
- connecteurs : Google Workspace, Microsoft 365, Infomaniak, OVH, Drive/OneDrive, agenda ;
- modules/fonctions sélectionnés ;
- devis et consentements.

Chat : assistant simulé avec `agent_spec` exploitable — le backend renvoie des messages
pré-programmés contextuels. Quand un vrai agent sera connecté, le même endpoint
sera utilisé sans changement UI.

Persistance/reprise (issue #35) :
- `POST /api/onboarding` crée ou met à jour un record local JSON sous `var/clients/`.
- La réponse contient `id`, `resume_url=/onboarding/?record_id=<id>`,
  `completed_sections`, `current_step` et `safety.paid_actions=none`.
- Le frontend autosauvegarde et peut recharger un onboarding via `record_id`.
- `POST /api/onboarding/<id>/simulate` produit une console de simulation :
  `appomar.onboarding_simulation.v1`, `agent_spec`, `provisioning_preview.mode=dry-run`,
  `provisioning_preview.paid_actions=none`, et prochains pas vers devis / dry-run / GO humain.

### Devis (V0.6.0)

Devis = sélection catalogue → devis JSON/PDF → checkout Stripe test/simulation.

- Produits du `catalog.json` : formules (Starter 49€, Pro 99€, Sur-mesure), modules, prestations.
- API accepte les items simples (`"formule-starter"`) et quantifiés (`{"id":"formule-starter","qty":2}`).
- Export DIY minimal : `GET /api/devis/<id>.pdf` renvoie un PDF téléchargeable sans dépendance externe.
- Aucun coût réel : `paid_actions=none`, Stripe test uniquement tant que la clef n'est pas configurée.
- Statut `paid_test` pour simulation de paiement réussi.

### Provisioning dry-run (V0.6.0)

Après devis, AppOmar peut produire un contrat de provisioning dry-run consommable par OmarTop/Hub/QG :
- `POST /api/provisioning/dry-run` avec `devis_id` + `target` (`vps|pc|hybride`).
- `GET /api/provisioning/<devis_id>` relit le contrat stocké.
- Contrat `omartop.provisioning-contract.v1`, `status=pending_go`, `paid_actions=none`.
- Aucune action automatique sans GO humain.

### Provisioning timeline (V0.5.0)

Après devis (payé ou simulé), le client voit une timeline de provisioning :
- Étapes visibles simulées (VPS, Caddy, Hub, agent, connexions).
- Aucune action automatique sans GO humain.
- Utilise `onboarding-status.json` existant.

### Agent spec (V0.5.0)

L'onboarding produit un `agent_profile` JSON structuré :
```json
{
  "agent_name": "...",
  "personality": { "ton": "...", "tutoiement": true, "autonomie": "moderee" },
  "canaux": [...],
  "perimetre": { "pro": true, "perso_limite": false, "sujets_interdits": [...] },
  "modules": [...],
  "infra_preference": "vps_managé|pc|hybride|inconnu"
}
```
Ce spec est exploitable par Hermes pour bootstrapper l'agent client.

## Simulation sans coût

| Étape | Simulation | Preuve |
|---|---|---|
| Onboarding | profil client + agent_profile JSON | `POST /api/onboarding` |
| Reprise onboarding | record_id + resume_url + sections validées | `GET /api/onboarding/<id>` |
| Simulation configuration | agent_spec + provisioning_preview dry-run | `POST /api/onboarding/<id>/simulate` |
| Devis | lignes catalogue non vides | `POST /api/devis` |
| Paiement | Stripe test statut `paid_test` | `POST /api/checkout` (503 attendu) |
| Infra | Hetzner dry-run / `paid_actions=none` | `GET /api/hetzner/pricing` |
| Provisioning | timeline visible status steps | `GET /api/onboarding/status` |
| Agent | `agent_profile` dans onboarding record | onboarding JSON |
| SAV | diagnostic read-only | `GET /api/sav/status` |

## Data boundaries

- Chaque client ne voit que ses données (`/api/onboarding/status`, `/api/sav/status`, `/api/proposals/{id}` filtrés par email OAuth → `clients/<id>/app-emails.txt`).
- `/api/onboarding/status` et `/api/sav/status` refusent l'accès sans email authentifié (403 unknown, [] vide données).
- `/api/proposals` refuse tout POST/GET sans credential valide : OAuth client connu/admin ou token opérateur interne.
- Pas de secrets en clair.
- Pas de données inter-tenant visibles.
- Les tokens/API keys ne sont jamais stockés dans le repo.
- Les secrets runtime `omar-app` doivent venir soit d'une injection directe du superviseur, soit d'un token Vault service-scopé.
- Les chemins Vault applicatifs autorisés sont documentés dans `docs/security/vault-policies.md`.

## Data model V0.5.0

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
  infra_preference: vps_managé | pc | hybride | inconnu
  appareils:
  connecteurs_intention:

agent_profile:
  agent_name:
  personality:
    ton: professionnel | amical | neutre
    tutoiement: bool
    autonomie: moderee | elevee | conservative
    seuil_validation: toujours | risqué | jamais
  canaux: [appomar, telegram, email]
  perimetre:
    pro: bool
    perso_limite: bool
    sujets_interdits: []
  modules: []
  notifications: []

onboarding_session:
  id:
  schema: appomar.onboarding_record.v1
  record: { client_profile, agent_profile }
  status: draft | submitted | ready_for_config
  resume_url:
  completed_sections: []
  current_step:
  safety: { paid_actions: none, provisioning: none }
  received_at:

onboarding_simulation:
  schema: appomar.onboarding_simulation.v1
  source_onboarding_id:
  agent_spec:
  provisioning_preview:
    mode: dry-run
    paid_actions: none
    status: pending_devis_then_human_go

devis:
  id:
  client:
  lignes: [{ id, label, prix_mensuel, prix_unique }]
  total_mensuel_eur:
  total_unique_eur:
  statut: brouillon | en_paiement | achete | paid_test
  stripe_session:
  stripe_mode: test | live

configuration_proposal:
  pack: oa-start
  providers: { hetzner, infomaniak }
  apps: []
  integrations: []
  estimated_costs:
  safety: { paid_actions: none }

support_request:
  type: bug | request | incident | question
  priority:
  status:
```

## Non-goals V0.5.0

- Pas de paiement réel live (Stripe test uniquement).
- Pas de marketplace multi-options complète.
- Pas de CRM complet.
- Pas de provider automation risquée sans validation.
- Pas de Nango obligatoire.
- Pas de true agent backend (chat simulé avec agent_spec exploitable).
- Pas de provisioning PC réel sans smoke test préalable et validation humaine.

## Option PC — promesse prépublique et smoke test V0.5.x

L'option PC est promise publiquement comme **installation accompagnée**. Elle ne doit pas déclencher d'action payante ni de modification machine sans validation.

Smoke test attendu avant installation réelle :

1. Collecter `infra=pc` ou `infra=hybride` dans l'onboarding.
2. Collecter OS/appareils et contraintes d'accès admin.
3. Produire un `agent_profile` indiquant clairement la cible PC.
4. Afficher que le PC sera vérifié avant activation : OS, droits admin, Tailscale/Docker ou alternative, connectivité.
5. Garder `paid_actions=none` en mode test.
6. Remonter un statut lisible : `pc_smoke=pending|pass|fail|not_applicable`.

## Success criteria V0.5.0

- Un prospect peut parcourir le tunnel A→Z sur mobile.
- Un prospect peut revenir via `record_id`/`resume_url` et retrouver ses sections validées.
- Un prospect peut cliquer "Simuler la configuration" pour prévisualiser agent_spec/provisioning sans coût.
- Onboarding collecte identité, objectifs, outils, infra, agent_spec.
- Devis non vide avec produits catalogue cohérents.
- Stripe test simulé lisible (503 attendu, pas faux paiement).
- Provisioning timeline visible (simulée).
- Option PC promise comme installation accompagnée avec smoke test préalable (`pc_smoke`) et aucune action payante.
- `/api/onboarding/status` ne fuit pas les données d'autres clients.
- Routes canoniques : `/onboarding/` + `/devis/` + `/sav/` + `/compte/`.
- Routes historiques `/config/`, `/buy/`, `/factures/` redirigées.
- Tests passent ; smokes API OK.

## Build gates

- Version visible (V0.5.0 header + changelog).
- Changelog visible.
- Routes fonctionnelles.
- No secrets.
- Test/smoke minimal.
- Contract mis à jour avant build.
- Review-gate H-Athena avant merge.
