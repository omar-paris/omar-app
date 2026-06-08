# Issue 001 — Packager l’offre OA autour du coût réel + options payantes activables

**Statut** : open  
**Type** : product / pricing / provisioning  
**Priorité** : P0  
**Source** : échange Alex ↔ H-Omar, 2026-06-08  
**Repo cible demandé** : `App.omar.paris`  
**Note** : aucun repo GitHub `omar-paris/omar-app`, `alexwill87/omar-app` ou `App.omar.paris` trouvé au moment de la capture. Issue durable créée localement sous `23-Offre/actifs/omar-app/.ops/issues/` en attendant repo GitHub.

---

## Contexte

Alex veut cadrer l’offre potentielle OA “solution tout-en-un” en distinguant :

1. le **coût réel** que OA porte dans son forfait ;
2. les **options payantes** que le client peut activer ;
3. ce qui est **self-hosted / gratuit côté licence** et ne doit pas être compté comme abonnement externe ;
4. ce qu’on peut **acheter/louer/configurer automatiquement via API** ;
5. la promesse commerciale correcte : provisioning automatisé, mais validation humaine dès qu’il y a dépense ou engagement.

Correction importante d’Alex :

- En PO/offre, parler d’**OpenRouter avec budget minimal**.
- Proposer en priorité le raccord à un **plan Codex Plus / Pro / Max** quand pertinent.
- **Infisical est self-hosted**, donc gratuit côté licence SaaS dans notre stack de base.
- **Monitoring self-hosted** : gratuit côté licence SaaS dans le socle.
- **Nango self-hosted** : gratuit côté licence SaaS.
- **Connecteurs OA** : gratuits côté licence ; coût = temps d’intégration/maintenance, pas abonnement.
- Focus principal : **coût réel de notre offre**, pas liste marketing gonflée.

---

## Problème à résoudre

Aujourd’hui, l’offre risque de mélanger :

- vrais coûts récurrents OA ;
- coûts client externes ;
- briques self-hosted gratuites ;
- options configurables mais non achetables automatiquement ;
- connecteurs qui ont une valeur produit mais pas de coût fournisseur.

Cela peut fausser la marge, rendre l’offre floue, ou promettre “tout inclus” alors que certaines licences restent côté client.

---

## Décision produit proposée

Créer un modèle d’offre avec quatre catégories :

### 1. Inclus OA — coût réel porté par OA

Ces coûts doivent entrer dans notre prix mensuel et notre marge.

- VPS client dédié : Hetzner / OVH / équivalent européen.
- Backups VPS / snapshots / stockage minimum.
- Domaine ou sous-domaine selon pack.
- DNS managé.
- Email transactionnel minimal si nécessaire.
- Budget OpenRouter minimal.
- Option prioritaire : raccord à Codex Plus / Pro / Max selon besoin réel.
- Maintenance opérationnelle OA : monitoring, mises à jour, supervision, backups, support.

### 2. Inclus technique — self-hosted / pas de coût licence SaaS

Ces briques ont un coût serveur/ops mais pas d’abonnement fournisseur à refacturer comme SaaS séparé :

- Infisical self-hosted.
- Vault si maintenu côté OA.
- Monitoring self-hosted : Grafana/Prometheus/Uptime stack interne ou équivalent.
- Nango self-hosted.
- Connecteurs OA / fiches catalogue / manifest capacités.
- Caddy.
- Postgres / Redis / Docker.
- Hermes Agent / Hub / runtime OA.
- OpenWebUI si utilisé côté client.
- Scripts de provisioning / smoke-checks.

### 3. À connecter — licence payée par le client

OA configure et agentise, mais ne paie pas par défaut :

- Google Workspace.
- Microsoft 365.
- PennyLane.
- HubSpot / Pipedrive / Brevo / Notion / Airtable.
- Sage / QuickBooks / Ciel / autres outils compta.
- Stripe / PayPal : compte client + frais transactionnels.
- Réseaux sociaux : Meta, Instagram Business, LinkedIn, Google Business Profile.
- Publicité : Google Ads / Meta Ads, budget toujours séparé.
- Signature électronique : Yousign / DocuSign / Universign.

### 4. À acheter via OA — option activable avec validation

OA peut orchestrer achat/location/provisioning, mais seulement après validation explicite :

- Domaine.
- Boîte mail pro souveraine.
- Stockage additionnel.
- Crédit SMS.
- WhatsApp Business / numéro téléphone, sous réserve KYC/validation fournisseur.
- Quota IA supérieur.
- Backup premium.
- IA souveraine externe type Infomaniak AI si retenue.
- GPU/serveur plus puissant.

---

## Options à inclure dans le catalogue produit

Chaque option doit avoir cette fiche :

```yaml
id: openrouter-budget-minimal
name: Budget OpenRouter minimal
category: ia
billing_owner: oa
purchase_automation: partial
config_automation: full
license_cost: variable_usage
included_in_pack: starter
requires_human_validation: true
requires_kyc: false
secrets:
  - OPENROUTER_API_KEY
smoke_checks:
  - list_models
  - run_minimal_chat_completion
cost_model:
  type: monthly_cap
  default_cap_eur: TBD
```

Champs obligatoires pour toutes les options :

```yaml
id:
name:
category:
billing_owner: oa | client | either
purchase_automation: full | partial | manual
config_automation: full | partial | manual
license_cost: none | fixed_monthly | usage_based | external_client_plan
included_in_pack: none | starter | pro | max
requires_human_validation: true | false
requires_kyc: true | false
secrets: []
smoke_checks: []
rollback:
notes:
```

---

## Catalogue initial recommandé

### P0 — socle à chiffrer tout de suite

| Option | Billing owner | Coût licence | Automatisation achat | Automatisation config | Statut offre |
|---|---|---:|---|---|---|
| VPS Hetzner client | OA | Oui | Full | Full | Inclus |
| Backup/snapshot VPS | OA | Oui | Full | Full | Inclus |
| Domaine/sous-domaine | OA/client selon pack | Oui | Partial/Full | Full DNS | Inclus/option |
| DNS managé | OA | Inclus/variable | Full | Full | Inclus |
| OpenRouter budget minimal | OA | Usage | Partial | Full | Inclus avec cap |
| Codex Plus/Pro/Max raccord | Client ou OA selon stratégie | Oui | Manual/Partial | Partial/Full | Prioritaire |
| Email transactionnel minimal | OA | Usage/freemium | Partial | Full | Inclus si besoin app |
| Infisical self-hosted | OA | 0 licence | N/A | Full | Inclus technique |
| Monitoring self-hosted | OA | 0 licence | N/A | Full | Inclus technique |
| Nango self-hosted | OA | 0 licence | N/A | Full | Inclus technique |
| Connecteurs OA | OA | 0 licence | N/A | Full/Partial | Inclus technique |
| Tailscale accès privé | OA/client | Free/paid selon seuil | Partial | Full | Inclus/à surveiller |

### P1 — options commerciales fortes

| Option | Billing owner | Coût licence | Automatisation achat | Automatisation config | Statut offre |
|---|---|---:|---|---|---|
| Email pro Infomaniak/OVH | OA/client | Oui | Partial | Partial/Full | Option |
| kDrive / stockage souverain | Client/OA | Oui | Partial | Full API possible | Option |
| Google Workspace | Client | Oui | Manual sauf reseller | Full OAuth/API | À connecter |
| Microsoft 365 | Client | Oui | Manual sauf partner | Full Graph API | À connecter |
| Stripe | Client | Frais transactions | Partial | Full API | Option |
| PennyLane | Client | Oui | Manual | API config/connecteur | À connecter |
| CRM HubSpot/Pipedrive/Brevo | Client | Oui/freemium | Manual/Partial | Full API | Option |
| SMS | OA/client | Usage | Full/Partial | Full API | Option |
| WhatsApp Business | Client/OA | Usage + KYC | Partial | Full après validation | Option |
| Infomaniak AI souveraine | OA/client | Usage | Partial | Full API | Option |
| Swiss Backup/Object Storage | OA/client | Oui | Partial/Full | Full | Option |

### P2 — plus tard

| Option | Billing owner | Coût licence | Automatisation achat | Automatisation config | Statut offre |
|---|---|---:|---|---|---|
| Téléphonie agent vocal | OA/client | Usage | Partial | Partial/Full | Spike |
| Signature électronique | Client | Oui | Manual/Partial | API selon provider | Spike |
| SSO avancé | Client/OA | Oui/variable | Manual/Partial | Full | Plus tard |
| GPU/local LLM dédié | OA/client | Élevé | Full si cloud | Full | Plus tard |
| Google/Meta Ads | Client | Budget externe | Manual | API possible | Hors forfait |
| EDR/antivirus poste client | Client | Oui | Manual | Partial | Hors coeur |

---

## Focus coût réel à produire

Créer une matrice de coût par pack :

```text
Coût réel OA mensuel =
  VPS
+ backup/snapshot
+ stockage additionnel moyen
+ domaine amorti / mois si inclus
+ email transactionnel moyen
+ budget OpenRouter capé
+ éventuel plan Codex si porté par OA
+ monitoring externe éventuel (normalement 0 si self-hosted)
+ marge risque support/ops
+ marge commerciale
```

À produire pour :

1. **Starter** : coût minimal viable.
2. **Pro** : coût confortable avec plus d’IA/connecteurs.
3. **Max** : coût premium avec budgets IA plus élevés + options communication.

Variables à trancher :

- Est-ce que le plan Codex Plus/Pro/Max est payé par OA ou raccordé au compte client ?
- Quel budget OpenRouter minimal inclus ?
- Domaine inclus ou facturé one-shot ?
- Email pro inclus ou option ?
- SMS/WhatsApp inclus avec quota ou 100% option ?
- Quel seuil de surconsommation IA déclenche blocage/refacturation ?

---

## Automatisation attendue

### Provisioning automatisé

- Créer VPS.
- Configurer DNS.
- Déployer stack OA.
- Déployer Infisical self-hosted.
- Déployer monitoring self-hosted.
- Déployer Nango self-hosted.
- Créer secrets initiaux.
- Configurer OpenRouter budget minimal.
- Raccorder Codex Plus/Pro/Max si credentials/plan disponibles.
- Activer connecteurs choisis.
- Lancer smoke-checks.
- Écrire résultat dans fiche client.

### Garde-fous

- Toute dépense récurrente ou achat définitif requiert validation explicite.
- Tout abonnement annuel requiert validation explicite.
- Tout budget usage-based doit avoir cap mensuel.
- Aucun secret en clair dans issue, logs, repo.
- Les connecteurs gratuits doivent être valorisés comme capacité produit, pas comme coût fournisseur.

---

## Acceptance criteria

- [ ] Une page/offre liste clairement : inclus OA, inclus technique self-hosted, à connecter, à acheter via OA.
- [ ] Une matrice coût réel mensuel existe pour Starter / Pro / Max.
- [ ] OpenRouter apparaît comme budget minimal capé.
- [ ] Codex Plus/Pro/Max apparaît comme option prioritaire de raccordement.
- [ ] Infisical, monitoring, Nango et connecteurs sont notés self-hosted/gratuits côté licence.
- [ ] Chaque option a `billing_owner`, `purchase_automation`, `config_automation`, `license_cost`, `requires_human_validation`.
- [ ] Les options avec KYC/validation fournisseur sont marquées partial/manual.
- [ ] Le wizard/provisioner refuse tout achat sans validation explicite.
- [ ] Smoke-checks définis pour chaque option P0.
- [ ] Issue migrée vers GitHub dès que le repo `App.omar.paris` existe.

---

## Prochaine action recommandée

1. Confirmer ou créer le repo GitHub cible `App.omar.paris` / `omar-app`.
2. Migrer cette issue locale vers GitHub.
3. Construire le premier fichier `offer-options.yaml` avec les champs ci-dessus.
4. Produire la matrice coût réel Starter/Pro/Max.
5. Faire un spike provisioning P0 : VPS + DNS + OpenRouter cap + Infisical self-host + Nango self-host + monitoring self-host.
