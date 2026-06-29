# AppOmar — fiches métier prioritaires pour audit utile

Date: 2026-06-29
Statut: V0 appliquée et testée

## Intention produit

Omar ne doit pas seulement demander au client de raconter son activité. Il doit disposer de fiches métier pour savoir quelles informations sont importantes, quelles recherches publiques proposer, quels concurrents regarder et quelles questions poser pour aboutir à des propositions concrètes.

Les quatre métiers prioritaires sont :

1. Boulangers
2. Restaurants
3. Gestion de fortune / patrimoine
4. Avocats

## Socle commun à collecter

Pour chaque audit métier, Omar doit récupérer ou demander explicitement :

- métier exact ;
- localisation et zone servie ;
- âge de l’entreprise / cabinet ;
- chiffre d’affaires ou ordre de grandeur accepté ;
- nombre d’employés / associés / prestataires ;
- typologie clients ;
- canaux entrants ;
- concurrents directs ;
- concurrents indirects ;
- outils actuels ;
- tâches répétitives ;
- données sensibles ;
- limites IA ;
- sources publiques autorisées ou refusées.

## Structure ajoutée dans chaque fiche métier prioritaire

Chaque référentiel prioritaire contient maintenant :

- `important_dimensions` : dimensions métier à surveiller ;
- `core_parameters` : paramètres critiques et pourquoi ils comptent ;
- `localized_research` : sources publiques à proposer, faits à collecter, consentement requis ;
- `competitor_mapping` : concurrence directe, concurrence indirecte, questions de différenciation ;
- `question_blocks` enrichis sur toutes les étapes : activité, sources, irritants, outils, risques, opportunités, autonomie, validation ;
- `risk_flags` ;
- `benchmarks` avec candidats d’automatisation et tests de première semaine.

## Spécificités par métier

### Boulangers

À maîtriser : flux boutique, commandes spéciales, saisonnalité, marges produit, horaires, avis Google, allergènes, hygiène, concurrence locale.

Concurrence directe : autres boulangeries, pâtisseries, terminaux de cuisson.
Concurrence indirecte : supermarchés, sandwicheries, livraison petit-déjeuner, traiteurs.

Premiers tests utiles : réponses commandes, rappels retrait, résumé avis Google, posts locaux, formulaire commande spéciale.

### Restaurants

À maîtriser : couverts par service, réservations/no-show, menus, allergènes, avis publics, livraison, privatisation, saisonnalité, stocks/pertes.

Concurrence directe : restaurants même cuisine/quartier/prix, brasseries, traiteurs proches.
Concurrence indirecte : livraison plateformes, snacking midi, supermarché repas prêts, cuisine d’entreprise.

Premiers tests utiles : réponses réservation, FAQ menu/allergènes, résumé avis, posts réseaux, relances no-show.

### Gestion de fortune / patrimoine

À maîtriser : réglementation AMF/MIF II, statuts CIF/IAS/IOBSP, profil investisseur, encours/CA, typologie clients, KYC/LCB-FT, devoir de conseil, traçabilité.

Concurrence directe : CGP indépendants, banques privées, family offices.
Concurrence indirecte : robo-advisors, courtiers en ligne, plateformes ETF, contenus finance gratuits.

Premiers tests utiles : préparation RDV, compte rendu, checklist conformité, relances documents, synthèse pédagogique, veille non prescriptive.

Garde-fou absolu : jamais de recommandation d’investissement automatique ; vocabulaire informatif + validation humaine.

### Avocats

À maîtriser : domaine du droit, secret professionnel, localisation/barreau, volume dossiers, typologie clients, production documentaire, délais, recherche juridique, validation.

Concurrence directe : cabinets du même domaine/barreau, boutiques spécialisées, cabinets d’affaires locaux.
Concurrence indirecte : legaltech, modèles de documents, plateformes consultation, contenus gratuits.

Premiers tests utiles : questionnaire préqualification, checklist pièces, synthèse anonymisée, brouillon de relance non juridique, recherche publique non confidentielle.

Garde-fou absolu : aucun conseil juridique non validé ; les sorties restent brouillons internes si elles touchent un dossier.

## Lien avec qgfinance.omar.paris

Le site QG Finance existant est une preuve utile : il contient déjà une logique de proposition concrète pour gestion de fortune, avec architecture, canaux, conformité et déploiement. Ce contenu doit nourrir la fiche `wealth_manager`, mais le nouveau moteur d’audit doit être plus général, plus structuré, et surtout capable de collecter d’abord les paramètres métier avant de proposer.

## Vérification

### Ajout P1/P2 appliqué

Deux endpoints structurent maintenant la recherche publique :

```txt
POST /api/audit-sessions/<id>/research-plan
POST /api/audit-sessions/<id>/public-research
```

`research-plan` renvoie :

- `schema: oa_audit_research_plan.v1` ;
- les champs de contexte présents/manquants ;
- les sources publiques proposées et leur statut selon consentement ;
- les faits à collecter ;
- la concurrence directe et indirecte ;
- les garde-fous métier ;
- `execute_external_calls: false` pour éviter tout scraping implicite.

`public-research` exécute seulement une première recherche publique bornée quand le consentement existe. Pour l’instant :

- fetch GET du site public explicitement fourni ;
- recherche légale France via `recherche-entreprises.api.gouv.fr` si SIRET/SIREN/nom public + consentement registre ;
- résultats limités à 3 établissements ;
- blocage des URL locales ;
- pas de login, POST, paiement, provisioning ou contact tiers ;
- faits extraits avec provenance `public_web_authorized` ou `legal_registry_authorized` ;
- statut des sources non exécutées conservé ;
- séparation stricte entre faits publics, réponses client et hypothèses.

Connecteurs spécialisés préparés mais pas encore exécutés automatiquement :

- ORIAS pour gestion de patrimoine/fortune ;
- annuaire/barreau pour avocats ;
- fiche Google / réseaux publics selon consentement.

L’interface `/audit/` expose aussi l’action **Préparer recherches**, qui affiche le plan puis la recherche publique initiale dans la conversation et dans le fichier `sources_audit.md`.

Chaque étape expose désormais :

- un objectif clair ;
- des critères de validation ;
- les champs manquants ;
- une reformulation de ce qu’Omar a déjà compris pour ne pas faire répéter le client.

Tests exécutés :

```bash
python3 -m pytest -q tests
```

Résultat : `40 passed`.

Smoke réel connecteur registre :

```bash
python3 - <<'PY'
import sys
sys.path.insert(0,'src')
from proposal_server import fetch_recherche_entreprises
print(fetch_recherche_entreprises('boulangerie lille', timeout=10)[:2])
PY
```

Résultat : 3 enregistrements reçus depuis `recherche-entreprises.api.gouv.fr`, dont `BOULANGERIE DU PAVE DE LILLE` avec SIREN/SIRET et code activité.
