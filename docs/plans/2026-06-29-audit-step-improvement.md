# AppOmar — amélioration audit étape par étape

Date: 2026-06-29
Statut: cadrage opérationnel + correctif V0 appliqué

## Correction de périmètre

On parle ici de l'audit, pas du devis.

Le devis est une sortie aval possible, après rapport et validation humaine. Pendant l'audit, les informations collectées servent d'abord à comprendre la personne/l'entreprise, compléter le diagnostic et produire des propositions de solutions concrètes, justifiées et limitées.

## Problème identifié

La première étape demandait l'activité, mais ne forçait pas assez Omar à proposer lui-même la collecte d'informations complémentaires.

Risque UX:
- l'utilisateur doit tout saisir manuellement ;
- Omar pose une suite de questions internes sans enrichissement ;
- le tunnel glisse trop vite vers le devis ;
- les propositions sont moins solides parce que les sources publiques, le site, la fiche Google, le SIRET ou les réseaux publics ne sont pas cadrés.

## Correctif V0 appliqué

Ajout d'une étape explicite après `Activité` : `Sources`.

Objectif de l'étape:
- demander le nom public de l'entreprise ;
- demander site, fiche Google, SIRET, réseaux publics si disponibles ;
- demander l'autorisation ou le refus explicite d'utiliser des sources publiques ;
- permettre à l'utilisateur de rester uniquement sur ses réponses s'il refuse.

Le wording visible de l'audit a aussi été corrigé pour parler de `rapport et propositions`, pas de `rapport, devis et onboarding`.

## Nouveau déroulé cible

1. Activité
   - métier exact ;
   - secteur ;
   - localisation ;
   - taille ;
   - ancienneté ;
   - ordre de CA si accepté ;
   - types de clients ;
   - demandes fréquentes.

2. Sources
   - nom public / enseigne ;
   - site web ;
   - fiche Google ;
   - SIRET/SIRENE ;
   - réseaux publics ;
   - documents fournis ;
   - consentement ou refus explicite.

3. Irritants
   - tâches répétitives ;
   - temps perdu ;
   - erreurs coûteuses ;
   - moments de friction.

4. Outils
   - email, agenda, WhatsApp, téléphone ;
   - Excel/Drive/OneDrive ;
   - CRM/facturation ;
   - flux réels entre outils.

5. Risques
   - données sensibles ;
   - actions interdites ;
   - décisions nécessitant validation humaine ;
   - publication externe ;
   - image de marque.

6. Opportunités
   - premières boucles utiles ;
   - gains réalistes ;
   - niveau d'automatisation admissible ;
   - ce qu'il ne faut pas automatiser.

7. Autonomie
   - faire soi-même ;
   - déléguer ;
   - hybride ;
   - rythme réaliste d'apprentissage.

8. Validation
   - reformulation finale ;
   - faits vs hypothèses ;
   - limites ;
   - rapport audit ;
   - propositions de solutions justifiées.

## Améliorations suivantes recommandées

### P1 — Backend de recherche contrôlée

Créer un endpoint `POST /api/audit-sessions/<id>/research-plan` qui ne fait pas encore de web scraping automatique, mais produit un plan de recherche structuré :

- sources autorisées ;
- sources refusées ;
- champs à vérifier ;
- hypothèses interdites ;
- preuves attendues.

### P2 — Recherche publique réelle mais bornée

Si consentement actif, brancher une recherche web publique limitée :

- site officiel ;
- fiche Google / avis publics ;
- registre légal public ;
- pages sociales publiques ;
- aucun login ;
- aucun contournement ;
- jamais de données privées.

Chaque fait injecté dans l'audit doit porter une provenance.

### P3 — Rapport avec séparation stricte

Dans le rapport final, séparer :

- déclarations utilisateur ;
- sources publiques vérifiées ;
- documents fournis ;
- hypothèses Omar ;
- recommandations ;
- limites et incertitudes.

### P4 — Propositions de solutions avant devis

Renommer l'artefact UX visible : `recommandations_source.json` ou `propositions_source.json`.

Le terme `devis_source` peut rester temporairement côté API pour compatibilité, mais il ne doit pas dominer l'expérience audit.

## Fichiers modifiés

- `pages-app/audit.html`
- `src/audit_intelligence.py`
- `tests/test_audit_intelligence.py`
- `tests/test_static_contract.py`

## Vérification

Commande exécutée :

```bash
python3 -m pytest -q tests/test_audit_intelligence.py tests/test_static_contract.py
```

Résultat : `17 passed`.
