# Adaptation du parcours audit après P2/P3 recherche publique

Date : 2026-06-29

## Objectif

Adapter le questionnaire pour que l’audit reste progressif : autorisations d’abord, compréhension métier ensuite, enrichissement public consenti, puis approfondissement opérationnel et recommandations.

## Parcours cible

### 1. Autorisations et cadre de confiance

Ce qu’on attend pour valider :

- consentement ou refus explicite par famille de source ;
- confirmation qu’aucune action payante/provisioning/contact tiers n’est autorisée pendant l’audit ;
- accord sur la séparation : déclaratif client / sources publiques / documents / hypothèses.

À améliorer : déplacer visuellement les consentements avant la première recherche, avec un micro-récap “ce que Omar a le droit de faire”.

### 2. Identité et activité

Ce qu’on attend pour valider :

- métier exact ;
- localisation / zone servie ;
- taille ;
- ancienneté ;
- ordre de CA ou refus explicite ;
- typologie clients.

Nouveau comportement acquis : Omar reformule ce qu’il sait déjà et liste seulement les manques.

### 3. Sources publiques et enrichissement

Ce qu’on attend pour valider :

- nom public / site / SIRET-SIREN si disponible ;
- plan de recherche généré ;
- sources autorisées/non autorisées visibles ;
- faits publics récupérés avec provenance ;
- sources spécialisées non exécutées listées avec lien officiel.

Acquis :

- site public explicite : fetch GET borné ;
- registre France : `recherche-entreprises.api.gouv.fr`, 3 résultats max ;
- ORIAS / barreau / Google : liens officiels préparés, pas d’auto-exécution.

À explorer :

- ORIAS : vérifier si une API ou endpoint stable/autorisé existe ; sinon garder mode lien manuel.
- CNB/barreau : vérifier si annuaire public expose une API officielle ; sinon garder mode lien manuel.
- Google/Maps : privilégier API officielle ou saisie client, éviter scraping large.

### 4. Irritants métier

Ce qu’on attend pour valider :

- tâches répétitives ;
- fréquence ou temps perdu ;
- exemples concrets ;
- distinction “ce qui peut être automatisé” / “ce qui doit rester humain”.

Adaptation : utiliser les faits publics pour éviter les questions inutiles, mais demander validation quand une source publique semble ambiguë.

### 5. Outils et flux

Ce qu’on attend pour valider :

- outils actuels ;
- canaux entrants ;
- doubles saisies ;
- contraintes d’intégration.

Adaptation : enrichir avec les outils probables du secteur sans les présenter comme faits.

### 6. Risques et garde-fous

Ce qu’on attend pour valider :

- données sensibles ;
- actions interdites ;
- validations humaines obligatoires ;
- contraintes réglementaires secteur.

Adaptation : chaque verticale doit injecter ses garde-fous : allergènes/prix pour boulangerie, hygiène/avis pour restaurant, devoir de conseil/ORIAS pour patrimoine, secret professionnel pour avocat.

### 7. Opportunités et solutions

Ce qu’on attend pour valider :

- 1 à 3 premières boucles utiles ;
- bénéfice attendu ;
- risques associés ;
- niveau d’autonomie acceptable.

Rappel : rester audit. Le devis vient après validation du rapport, pas pendant l’exploration.

## Backlog priorisé

1. UI : rendre l’étape autorisations plus visible avant “Préparer recherches”.
2. Rapport : intégrer un tableau `faits publics à valider` séparé du déclaratif client.
3. Connecteurs : investiguer ORIAS et CNB comme sources officielles, sans scraping sauvage.
4. Local : ajouter recherche concurrence locale uniquement via source/API validée ou saisie client.
5. Mémoire session : permettre à Omar de réutiliser les faits validés à chaque étape sans répétition.

## Critère de réussite

Un prospect doit pouvoir dire : “Je suis avocat à Lyon, cabinet X”, autoriser les sources publiques, et Omar doit répondre :

- ce qu’il a compris ;
- ce qu’il a trouvé publiquement ;
- ce qui reste à valider ;
- ce qu’il ne fera pas sans autorisation ;
- les 2 ou 3 questions suivantes vraiment utiles.
