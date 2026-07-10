# Audit Intelligence V1 — gap matrix AppOmar deep-search → code

Source de vérité : `docs/research/2026-07-08-audit-business-tech-appomar-deep-search-result.md`.

## Verdict

Le socle V0 existe : arbre conversationnel, politique anti-chaos, consentement sources publiques, secteurs, scores explicables et premier rapport premium déterministe.
Le gap produit restant n'est pas “plus de prompt”, mais une transformation du runtime en audit cabinet : preuves séparées, sections réellement alimentées, relances de profondeur, devis justifié et smoke live.

## Gap matrix

| Exigence deep-search | Statut avant V1 | Livraison V1 attendue | Preuve attendue |
|---|---:|---|---|
| Hybridation déclaratif / sources publiques consenties | Partiel | D/V/H/F séparés partout, jamais de source publique non validée | tests public research + traceability |
| 9 dimensions V0/V1/V2 | Présent minimal | Chaque dimension a evidence, implication, next_test, maturité | `diagnostic_dimensions` |
| Scores explicables | Présent minimal | Score + why + limits + how_to_improve, sans vérité technique inventée | `oa.audit-scores.explainable.v1` |
| Rapport final 17 sections | Outline seulement | 17 sections structurées, alimentées, avec statut, preuves, limites, next_action | `final_report_sections` |
| Agent profile | Brouillon simple | Mission, actions autorisées/interdites, gates, critères de succès | `agent_profile` |
| Devis non intrusif | Ligne simple | Chaque ligne pointe preuve/reco, prérequis, limites, gate humaine | `devis_model.line_items` |
| Profondeur des étapes | Arbre + missing inputs | Contrat de profondeur par étape : expected_evidence, validation, repair, impact rapport | `conversation_depth_contract` |
| Secteurs prioritaires | Données présentes | Rapport exploite secteur pour quick wins, risques, tests 7 jours | transcript/tests bakery puis extensible |
| Publication | Non fait | Tests/build/diff checks, PR/merge/live restart, smoke GET + API | output shell réel |

## Règles de livraison

- Déterministe : pas de génération LLM libre pour combler les trous.
- Sobriété : si une preuve manque, la section dit “à vérifier”, pas “confirmé”.
- Pas de secret, pas de provisioning, pas de paiement pendant audit.
- Publication seulement après tests, build, diff check, puis smoke live.

## DoD

- `python3 -m pytest tests/test_audit_tree_runtime.py -q`
- bloc audit ciblé vert
- build vert
- static contracts vert
- scan diff sans secrets ni chemins locaux publics
- PR mergée ou explicitement bloquée
- live `https://app.omar.paris/audit/` répond en GET
- smoke API audit/session/report/devis avec cleanup si possible
