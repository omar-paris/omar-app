# Omar App V0.1.0 — Build Report

Date : 2026-06-08
App : `app.omar.paris`
Path : `/home/omar/23-Offre/actifs/omar-app`

## Livrable

Skeleton statique local-first créé.

Routes générées :

```txt
/
/onboarding/
/config/
/buy/
/sav/
/factures/
/compte/
/changelog/
```

## Tests

RED initial confirmé :

```txt
6 failed
python3: can't open file 'scripts/build.py'
```

GREEN après implémentation :

```txt
python3 -m pytest -q tests/test_static_contract.py
...... [100%]
6 passed in 0.21s
```

## Smokes HTTP locaux

Serveur local :

```txt
python3 scripts/build.py && python3 -m http.server 8123 --directory public
```

Résultat :

```txt
/ HTTP 200 bytes 3196
/onboarding/ HTTP 200 bytes 3537
/config/ HTTP 200 bytes 3475
/buy/ HTTP 200 bytes 2896
/sav/ HTTP 200 bytes 3017
/factures/ HTTP 200 bytes 2906
/compte/ HTTP 200 bytes 3192
/changelog/ HTTP 200 bytes 2792
/assets/styles.css HTTP 200 bytes 2891
```

## Browser QA

URL testée :

```txt
http://127.0.0.1:8123/
http://127.0.0.1:8123/config/
```

Résultat :

- navigation visible ;
- route `/config/` chargée ;
- console sans erreur JS ;
- visuel lisible ;
- contraste fort ;
- pas de blocage visible.

Console :

```txt
console_messages: []
js_errors: []
total_errors: 0
```

## Fichiers principaux

```txt
APP_CONTRACT.md
README.md
src/site_data.py
scripts/build.py
tests/test_static_contract.py
public/**
```

## Limites V0

- Pas encore déployé sur `app.omar.paris` : DNS public ne résout pas actuellement.
- Pas d'auth réelle.
- Pas de chatbot réel.
- Pas de stockage client.
- Pas de paiement.
- Pas d'OAuth/Nango réel.

## Prochaine étape recommandée

1. Décider déploiement preview : Tailnet ou public DNS.
2. Ajouter formulaire onboarding interactif local-first.
3. Ajouter modèle JSON `client_profile`, `onboarding_session`, `configuration_proposal`.
4. Brancher sortie vers Plane/QG plus tard.
