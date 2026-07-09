# AppOmar — contrat de frontière activation / audit / devis / onboarding / SAV

Date: 2026-07-08
Statut: contrat documentaire v0.1 — non publié, non release, sans décision commerciale nouvelle
Carte Kanban: t_fe045e53
Source audit adoptée: `src/audit_tree.business_tech.v1.yaml` (`schema: oa.audit-tree/1`, `tree_id: business_tech`, `version: 1`)

## 1. Décision de frontière

AppOmar n'est pas une simple page d'onboarding et l'onboarding n'est pas une application séparée.

AppOmar porte le parcours d'activation complet Omar & Alex:

```txt
promesse publique
→ audit conversationnel Omar
→ rapport / propositions justifiées
→ devis ou validation commerciale
→ onboarding agent prérempli depuis l'audit validé
→ préférences / intégrations / apps nécessaires
→ mise en place Hub client
→ SAV / maintenance / évolutions
```

Cette séquence est une **frontière produit et technique**. Elle ne fige pas à elle seule le moment commercial exact du paiement dans la communication publique.

## 2. Décision commerciale non figée par ce contrat

Le moment où le client paie est une décision business Alex/H-Omar, pas une décision d'un reviewer ni d'un worker.

Règle v0:

```txt
- Le contrat technique peut prévoir les points de sortie `devis`, `checkout`, `validation`, `onboarding`.
- Le wording public et l'ordre payant exact ne sont pas modifiés sans GO business explicite.
- L'ancien Stripe reste legacy; PayPal / coupons / bons / paiement 1er mois avant activation réelle restent des options commerciales à valider dans le tunnel public.
```

Donc la carte 3 débloque les cartes tunnel en écrivant les limites et contrats, pas en publiant un nouveau parcours payant.

## 3. Arbre audit canonique adopté

La frontière AppOmar adopte l'arbre existant:

```txt
/home/omar/23-Offre/actifs/omar-app/src/audit_tree.business_tech.v1.yaml
```

Champs clefs à respecter par les implémentations tunnel:

| Zone | Source dans YAML | Règle frontière |
|---|---|---|
| Audit conversationnel | `steps`, `actes`, `v0_scope` | Le runtime suit les steps structurés, pas un LLM libre. |
| Consentement sources | `consent_contract` + step `public_sources_consent` | Aucune recherche/source externe sans consentement explicite. |
| Preuves | `evidence_contract` | Déclaré client ≠ vérifié public ≠ hypothèse Omar ≠ document fourni. |
| Rapport | `report_contract.sections` | Rapport généré depuis champs structurés, jamais depuis transcript brut. |
| Onboarding | `onboarding_contract` + `outputs.onboarding` | Agent profile dérivé de la synthèse validée, pas d'un wizard vierge. |
| Devis | `devis_contract` + `outputs.devis` | Chaque ligne est justifiée par recommandation/preuve d'audit; optionnelle sinon. |
| Sécurité | `principles.aucune_action_sensible` | Jamais paiement/provisioning/contact externe/publication sans GO humain. |

## 4. Contrats de sortie AppOmar

### 4.1 `oa.audit-session.business_tech/v1`

Premier consommateur: runtime AppOmar audit (`src/audit_intelligence.py` / API audit).

Obligatoire: `session_id`, `tree_id=business_tech`, `current_step`, `completed_steps`, `structured_answers`, `consents`, `validation_cards`, `status`.

Interdit: transcript brut comme source de vérité, mot de passe, clé, RIB, recherche publique sans consentement.

### 4.2 `oa.audit-report.business_tech/v1`

Premier consommateur: page rapport AppOmar + génération propositions.

Doit inclure les 17 sections du `report_contract` YAML et séparer `D=declaré client`, `V=vérifié public consenti`, `H=hypothèse Omar`, `F=document fourni`.

### 4.3 `oa.onboarding-pack.business_tech/v1`

Premier consommateur: onboarding AppOmar prérempli + création future Hub client.

Source unique: `client_validated_summary` et `outputs.onboarding` validés.

Champs minimum: `role`, `mission`, `tone`, `channels`, `allowed_connectors`, `forbidden_data`, `human_gates`, `initial_routines`, `test_scenarios`, `success_criteria`.

### 4.4 `oa.devis.business_tech/v1`

Premier consommateur: devis/proposition AppOmar.

Règle: chaque ligne porte une justification issue d'une recommandation validée.

Champs minimum: `catalog_id`, `recommendation_ref`, `evidence`, `required`, `confidence`, `price_policy_ref|null`, `checkout_state`.

Le champ `checkout_state` existe pour la technique; il ne décide pas seul du moment commercial du paiement.

### 4.5 `oa.hub-client-bootstrap/v1`

Premier consommateur: OmarHub client / Hub local.

Contient uniquement les paramètres safe nécessaires pour amorcer le Hub client: `tenant_id`, `company_context_summary`, `agent_profile_ref`, `apps_needed`, `connectors_needed`, `human_gates`, `redaction_level`, `source_audit_id`.

Pas de secrets. Les secrets passent par le circuit secret validé, jamais dans le payload AppOmar.

### 4.6 `oa.sav-request/v1`

Premier consommateur: AppOmar SAV + Hub local.

Champs minimum: `tenant`, `vps_or_hub`, `app_or_agent`, `status`, `symptom`, `safe_context`, `requested_action`, `proof_refs`.

Le SAV ne doit pas exposer logs bruts, transcripts ou secrets.

## 5. Interfaces avec Hub et QG

### Hub client

Le Hub reçoit les éléments utiles pour opérer le client après activation: agent profile validé, apps/intégrations nécessaires, human gates, routines initiales, SAV / maintenance requests.

Le Hub reste owner de la vérité locale. AppOmar ne devient pas le cockpit runtime.

### QG

Le QG reçoit seulement des états agrégés: `audit_started`, `report_ready`, `devis_draft`, `onboarding_ready`, `hub_pending`, `sav_open`, fraîcheur, owner, blocked_reason si besoin décision.

Le QG ne reçoit ni transcript brut, ni données client détaillées, ni secret.

## 6. Pré-requis pour les cartes [TUNNEL]

Les cartes suivantes doivent considérer ce contrat comme prérequis de cohérence:

```txt
t_89ec59b1 [TUNNEL][P3] Runtime arbre
t_3af3c7f4 [TUNNEL][P4] Rapport business_tech.v1
t_b3236aec [TUNNEL][P5] Onboarding prérempli + devis public justifié
```

Conséquence pratique:

```txt
- elles descendent du même arbre `audit_tree.business_tech.v1.yaml`;
- elles ne doivent pas inventer un contrat concurrent;
- toute divergence doit être traitée comme finding de review, pas comme détail d'implémentation.
```

## 7. DoD carte 3

```txt
[x] AppOmar défini comme parcours activation complet + SAV.
[x] Arbre `audit_tree.business_tech.v1.yaml` adopté comme source canonique.
[x] Contrats de sortie nommés avec premier consommateur.
[x] Interface Hub/QG clarifiée.
[x] Moment commercial du paiement explicitement non figé par cette carte.
[x] Cartes [TUNNEL] listées comme dépendantes/prérequis de cohérence.
```
