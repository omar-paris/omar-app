# AppOmar Audit Business & Tech — intégration du résultat Deep Search

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task after Alex GO.

**Goal:** Transformer le résultat Deep Search reçu (`docs/research/2026-07-08-audit-business-tech-appomar-deep-search-result.md`) en améliorations concrètes de l'arbre audit, du runtime, du rapport, de l'onboarding et du devis.

**Architecture:** Garder `src/audit_tree.business_tech.v1.yaml` comme source canonique court terme. Ne pas créer une V2 parallèle tant que le runtime V1 n'est pas stabilisé. Ajouter des enrichissements ciblés: traçabilité D/V/H/F, cyber baseline TPE, facturation électronique 2027, scoring explicable, consent gates granulaires, génération d'artefacts structurés.

**Décision produit Alex — 2026-07-08:**
- Audit public possible sans compte.
- Inscription proposée au début pour suivre/sauvegarder, mais non obligatoire pour auditer.
- À la fin, proposer sauvegarde + envoi email si la personne n’est pas encore enregistrée.
- Devis réservé aux personnes enregistrées/authentifiées.
- Paiement sécurisé cible PayPal ; Stripe est legacy technique à remplacer, pas la promesse produit.
- Fable/Deep Search sont des matériaux à digérer en améliorations, pas des artefacts à supprimer ni à publier bruts.

**Tech Stack:** Python backend `src/proposal_server.py` / audit intelligence, YAML audit tree, pytest, docs markdown.

---

## 1. Ce qu'on intègre maintenant

### A. Source de recherche

- Create: `docs/research/2026-07-08-audit-business-tech-appomar-deep-search-result.md`
- Rôle: archive nettoyée du résultat Deep Search, non exécutée par le runtime.
- Statut: source documentaire, à citer dans les plans/PR, pas à copier aveuglément.

### B. Arbre audit V1 — enrichissements prioritaires

Modifier `src/audit_tree.business_tech.v1.yaml` sans casser le schéma existant:

1. **Traçabilité D/V/H/F**
   - D = déclaré client.
   - V = vérifié source publique.
   - H = hypothèse Omar.
   - F = fichier/document fourni.
   - Chaque output rapport important doit pouvoir porter `origin`, `confidence`, `source_ref`.

2. **Consentements granulaires**
   - Séparer `sirene_detail`, `site_web`, `fiche_google`, `reseaux`, `documents`.
   - Garder refus non bloquant.
   - Ajouter gestion homonymie / établissement multiple / non-diffusibilité.

3. **Cyber baseline TPE**
   Ajouter dans `digital_tools_data` ou une sous-section dédiée:
   - sauvegarde fiable / test restauration / support déconnecté ;
   - MFA sur mail et comptes critiques ;
   - coffre-fort mots de passe ou mots de passe uniques ;
   - mises à jour automatiques ;
   - anti-phishing / vigilance équipe.

4. **Facturation électronique 2027**
   Ajouter dans `admin_finance_purchasing`:
   - outil actuel: logiciel conforme / Excel-Word / comptable / papier ;
   - niveau de préparation à la réforme ;
   - opportunité pédagogique, pas anxiogène.

5. **Scores explicables, pas pseudo-scientifiques**
   Ajouter une section `scoring_contract`:
   - hygiène cyber ;
   - friction opérationnelle ;
   - maturité numérique/data/IA ;
   - valeur automatisation ;
   - risque automatisation ;
   - chaque score doit exposer `why`, `limits`, `how_to_improve`.

6. **Sorties structurées verrouillées**
   Renforcer `report_contract`, `devis_contract` et ajouter `onboarding_contract`.

---

## 2. Ce qu'on ne copie PAS tel quel

1. Le style du résultat Deep Search est trop consultant/institutionnel par endroits.
   - À transformer en langage Omar: court, humain, concret.

2. Les formules mathématiques exportées sont cassées par le rendu markdown.
   - À remplacer par des scores simples à barèmes explicites.

3. Les exemples de tarifs du devis sont placeholders.
   - À mapper au catalogue réel AppOmar, jamais inventer des prix.

4. Le YAML proposé comme `v2` n'est pas compatible direct avec notre schéma actuel.
   - À utiliser comme inspiration, pas comme remplacement.

5. Certaines sources sont secondaires/commerciales.
   - À hiérarchiser: sources publiques/institutionnelles > cabinets privés > blogs outils.

---

## 3. Implémentation recommandée

### Task 1: Ajouter la traceabilité des informations d'audit

**Objective:** permettre au rapport de distinguer déclaré / vérifié / hypothèse / document.

**Files:**
- Modify: `src/audit_tree.business_tech.v1.yaml`
- Modify/Test: `tests/test_audit_tree_runtime.py`

**Steps:**
1. Ajouter un bloc `evidence_contract` au YAML.
2. Déclarer les types `declared`, `verified_public`, `omar_hypothesis`, `provided_document`.
3. Ajouter un test qui parse le YAML et vérifie la présence du contrat.
4. Vérifier que `report_contract.regle` impose cette séparation.

### Task 2: Renforcer les consent gates

**Objective:** rendre le consentement source-par-source exploitable en UI/runtime.

**Files:**
- Modify: `src/audit_tree.business_tech.v1.yaml`
- Modify: `src/proposal_server.py` si endpoints research-plan/public-research doivent suivre le contrat.
- Test: `tests/test_proposal_server.py`

**Steps:**
1. Formaliser les sources autorisées.
2. Ajouter `error_handling`: homonymie, non-diffusible, source obsolète, refus.
3. Tester que le refus ne bloque pas l'audit.

### Task 3: Ajouter cyber baseline TPE

**Objective:** intégrer un diagnostic cyber minimal ANSSI-compatible sans audit anxiogène.

**Files:**
- Modify: `src/audit_tree.business_tech.v1.yaml`
- Test: `tests/test_audit_tree_runtime.py`

**Questions à ajouter:**
- “Si votre téléphone ou ordinateur principal disparaît demain, qu'est-ce qui reste accessible ?”
- “Votre boîte mail principale a-t-elle une double validation ?”
- “Vos mots de passe sont-ils uniques ou réutilisés ?”
- “Avez-vous déjà testé une restauration de sauvegarde ?”

### Task 4: Ajouter facturation électronique 2027

**Objective:** transformer une contrainte réglementaire française en opportunité utile.

**Files:**
- Modify: `src/audit_tree.business_tech.v1.yaml`

**Questions à ajouter:**
- “Vos devis/factures sortent d'un logiciel, d'Excel/Word, du comptable, ou encore du papier ?”
- “Vous voulez que je vérifie plus tard si votre organisation est prête pour la facturation électronique ?”

### Task 5: Ajouter scoring_contract

**Objective:** rendre les scores explicables et non pseudo-scientifiques.

**Files:**
- Modify: `src/audit_tree.business_tech.v1.yaml`
- Test: `tests/test_audit_tree_runtime.py`

**Scores:**
- `cyber_hygiene_score`
- `operational_friction_score`
- `digital_data_ai_maturity_score`
- `automation_value_score`
- `automation_risk_score`

Chaque score doit avoir:
- `signals`
- `explanation`
- `limits`
- `improvement_hint`

### Task 6: Renforcer onboarding_contract

**Objective:** faire du rapport la source canonique de l'agent_profile.

**Files:**
- Modify: `src/audit_tree.business_tech.v1.yaml`
- Modify: `src/proposal_server.py` si génération déjà présente.

**Champs:**
- role, mission, tone, channels, allowed_connectors, forbidden_data, human_gates, initial_routines, test_scenarios, success_criteria.

### Task 7: Renforcer devis_contract

**Objective:** aucune ligne de devis sans justification audit.

**Files:**
- Modify: `src/proposal_server.py`
- Test: `tests/test_proposal_server.py`

**Règle:**
- item catalogue réel seulement ;
- recommendation_source obligatoire ;
- evidence/verbatim obligatoire ou statut `optionnel` ;
- pas de prix inventé.

---

## 4. Gates de vérification

Avant PR:

```bash
python3 - <<'PY'
import yaml
from pathlib import Path
p = Path('src/audit_tree.business_tech.v1.yaml')
yaml.safe_load(p.read_text())
print('YAML OK')
PY
python3 -m pytest -q tests/test_audit_tree_runtime.py tests/test_proposal_server.py
```

Smoke fonctionnel attendu:

```txt
/audit/ -> session -> research-plan -> public-research dry-run/consent -> report -> onboarding_pack -> devis_source -> devis justified
```

---

## 5. Décision CTO

Ne pas continuer à explorer globalement sans implémenter. La recherche a donné assez de matière pour un incrément V1 utile.

Explorer encore seulement sur 3 axes ciblés:

1. **Sources françaises officielles**: CNIL, ANSSI, France Num, Bpifrance, facturation électronique.
2. **Verticales prioritaires**: boulangerie/restauration, artisan BTP, avocat, CGP.
3. **Microcopy audit premium**: rendre les questions moins “rapport consultant” et plus Omar.
