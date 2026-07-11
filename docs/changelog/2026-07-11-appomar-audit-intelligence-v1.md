# Changelog AppOmar — Audit Intelligence V1

Date : 2026-07-11 03:18 CEST

Périmètre : audit conversationnel Business & Tech AppOmar (`tree_id=business_tech`)

Source de référence : `docs/research/2026-07-08-audit-business-tech-appomar-deep-search-result.md`

## Résumé exécutif

Aujourd'hui, l'audit AppOmar a été transformé d'un parcours conversationnel fonctionnel en socle d'audit consultant traçable, déterministe et exposé par l'API live.

L'objectif produit reste : à partir d'une conversation audit, produire une restitution exploitable et plusieurs documents finaux pour cadrer le client, son agent IA, ses limites, son devis et ses prochaines décisions.

## Ce qui est maintenant en place

### 1. Cadre audit Business & Tech

- Arbre source : `src/audit_tree.business_tech.v1.yaml`.
- Session runtime : `oa_audit_session.business_tech.v1`.
- Parcours structuré en 3 actes :
  - `rencontre` : pacte, identité, sources publiques, activité, dirigeant/objectifs ;
  - `plongee` : semaine réelle, ventes/marketing, admin/finance, équipe, outils/data/sécurité, lignes rouges ;
  - `livraison` : diagnostic, recommandations, validation finale.
- Politique active : vouvoiement, messages courts, 70/30, contrôle client, aucune action sensible sans GO humain.

### 2. Questions, objectifs et quick replies

- Chaque étape porte désormais un objectif métier explicite.
- Les questions clés visent la réalité opérationnelle : métier exact, clients, zone, équipe, semaine réelle, irritants, outils, ruptures de flux, lignes rouges, validation humaine.
- Les quick replies servent à confirmer/accélérer, pas à remplacer l'écoute.
- Les réponses faibles/confuses/hostiles ne valident plus automatiquement une étape.
- Les critiques produit de l'utilisateur sont détectées comme feedback et bloquent la validation jusqu'à réparation.

### 3. Profondeur consultant et secteurs

- Le rapport premium est aligné sur le deep-search AppOmar.
- 9 dimensions de diagnostic sont codées et testées :
  1. identité et contexte officiel ;
  2. modèle économique et proposition de valeur ;
  3. semaine réelle et charge mentale ;
  4. hygiène cyber minimale ;
  5. maturité numérique/IA subjective ;
  6. parcours client et acquisition ;
  7. admin/finance/facturation électronique ;
  8. équipe et organisation ;
  9. maturité Data/IA objective.
- Les sector packs prioritaires restent utilisés pour enrichir le contexte, notamment `bakery`, `restaurant`, `lawyer`, `plumber`, `florist`, `wealth_manager`, `marketing_freelance`, `secretary_independent`, `generic_tpe`.
- La profondeur sectorielle est surtout prouvée aujourd'hui sur le transcript boulangerie ; les autres secteurs restent à renforcer demain.

### 4. Traçabilité D/V/H/F

Le rapport sépare les natures de preuve :

- `declared_client` : déclarations client ;
- `verified_public` : sources publiques vérifiées/validées ;
- `hypotheses_omar` : hypothèses Omar ;
- `unknowns_or_future_checks` : inconnues ou vérifications futures.

Règle produit : une hypothèse ne doit pas devenir une vérité dans le rapport.

### 5. Scores explicables

Le rapport expose `oa.audit-scores.explainable.v1` avec :

- `cyber_hygiene` ;
- `operational_friction` ;
- `digital_ai_maturity`.

Chaque score contient :

- `score` ;
- `why` ;
- `limits` ;
- `how_to_improve`.

Ces scores restent indicatifs : ils ne prétendent pas remplacer une vérification technique terrain.

### 6. Documents finaux produits ou préparés

Le runtime sait désormais produire plusieurs artefacts déterministes depuis la session d'audit :

1. `structured_audit` — audit structuré J1-ter (`oa.structured_audit.j1ter.v1`).
2. `premium_consulting_report` — rapport premium structuré (`oa.premium-consulting-report.v1`).
3. `premium_consulting_markdown` — version markdown du rapport premium.
4. `manifest_business` — manifeste business client.
5. `owner_identity` — identité/objectif dirigeant.
6. `agent_profile` — profil d'agent proposé, gates humains et interdits.
7. `local_constitution` — pré-constitution locale.
8. `open_questions` — inconnues restantes à traiter.

Objectif initial rappelé : aboutir à 5 ou 6 documents finaux type manifeste business, constitution locale, profil agent, rapport d'audit, plan/devis et questions ouvertes. Le socle en produit aujourd'hui davantage, mais certains restent courts et devront être enrichis demain pour être vraiment présentables.

### 7. Rapport premium 17 sections

Le `premium_consulting_report` expose maintenant :

- `final_report_outline` avec 17 titres ;
- `final_report_sections` avec 17 sections structurées ;
- pour chaque section : `id`, `title`, `status`, `source_buckets`, `content`, `evidence`, `limits`, `next_action`.

Sections couvertes : résumé exécutif, déclarations client, sources vérifiées, hypothèses Omar, diagnostic business, diagnostic tech/data, SWOT, risques/lignes rouges, matrice d'automatisation, quick wins 7 jours, plan 30 jours, recommandations OA, limites d'automatisation, prompts/procédures, données onboarding agent, devis justifié, prochaines décisions.

### 8. Devis non intrusif

Le modèle de devis est maintenant rattaché à l'audit :

- `non_intrusive: true` ;
- lignes de devis justifiées par preuves/recommandations ;
- prérequis, limites et gate humaine ;
- pas de promesse d'autonomie sans validation.

### 9. API live corrigée

Après le merge du socle V1, un smoke live a montré que `/api/audit-sessions/{sid}/report` ne renvoyait pas encore les artefacts premium.

Hotfix appliqué :

- `premium_consulting_report` est maintenant exposé dans la réponse API ;
- `premium_consulting_markdown` est exposé aussi ;
- les deux artefacts sont persistés dans `audits/<id>.json` ;
- la garde limite ce comportement aux sessions `oa_audit_session.business_tech.v1` complètes.

Smoke final observé :

```json
{
  "has_premium": true,
  "premium_schema": "oa.premium-consulting-report.v1",
  "sections": 17,
  "has_markdown": true
}
```

## Commits et PRs associés

- `c767a21` — `fix: block weak audit inputs from auto-validating`
- `22838ad` — `feat(appomar): deepen audit intelligence report contract`
- `edb1d43` — `fix(appomar): expose premium report artifacts via API`

PRs :

- PR #76 — Audit Intelligence V1 : rapport premium, 9 dimensions, scores, D/V/H/F, 17 sections, depth contract, agent profile, devis.
- PR #77 — hotfix API : exposition/persistance du rapport premium via `/report`.

## Gates et preuves connues

### Revue froide Athena

- PR #76 : `pass_with_nits`.
- PR #77 : `pass`.
- Aucun blocker final.

### Tests rapportés pendant le cycle

- `python3 -m pytest tests/test_audit_tree_runtime.py -q` — couvert par PR #76.
- `python3 -m pytest tests/test_proposal_server.py -q` — couvert par PR #77.
- `python3 -m pytest -q` — revue PR #77 : `128 passed in 62.02s`.
- `python3 scripts/build.py` — build OK pendant la revue PR #76.
- `git diff --check` — OK sur les PRs revues.

### Smoke live

- `https://app.omar.paris/audit/` répond en GET/OAuth selon contexte.
- Endpoint `/api/audit-sessions/{sid}/report` corrigé : artefacts premium présents et persistés.

## Ce qui reste à reprendre demain

1. Enrichir les documents finaux courts (`manifest_business`, `local_constitution`, `owner_identity`, `open_questions`) pour les rendre présentables client, pas seulement structurés.
2. Étendre les transcripts/tests sectoriels au-delà de `bakery` : restaurant, avocat, plombier, secrétaire indépendante, gestionnaire de patrimoine.
3. Clarifier l'UX de téléchargement/présentation des 5-6 documents finaux dans AppOmar.
4. Vérifier dans le navigateur que les quick replies et validations donnent bien l'impression d'un consultant, pas d'un formulaire.
5. Décider quels artefacts sont livrés gratuitement après audit et lesquels deviennent onboarding/devis/activation.
6. Ajouter un test négatif explicite : une session non-`business_tech` ne doit jamais exposer `premium_consulting_report`.

## Lecture rapide pour reprise

État mental à conserver : le moteur n'est plus seulement un questionnaire. C'est maintenant un noyau d'audit déterministe qui collecte des faits, refuse les réponses non exploitables, sépare les preuves, produit un rapport premium 17 sections, prépare un agent et justifie un devis. Demain, le travail n'est pas de tout refaire : il faut surtout enrichir la qualité éditoriale des documents finaux et valider l'expérience utilisateur complète.
