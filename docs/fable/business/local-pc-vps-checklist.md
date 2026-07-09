# Checklist installation — poste local accompagné (et repères VPS/hybride)

Version : 0.2 — 2026-07-10 — Fable 2
Cas visé : tout client qui choisit une option « poste local accompagné ». Cette
checklist est générique et ne doit pas contenir de nom de client, profil machine,
canal privé, outil de prise en main imposé ou état opérationnel réel.
Exécution : équipe OA habilitée. Fable 2 ne provisionne pas et ne manipule pas de
secrets.

## État initial à reconfirmer

Aucun état déclaré n'est pris pour acquis dans ce dépôt public. Avant toute
installation, l'équipe reconfirme avec le client : machine concernée, OS, droits,
réseau, consentement, outil d'assistance éventuel et périmètre de données.

## Phase 0 — Consentement (5 min, avec le client)

- [ ] Expliquer en une phrase ce qu'on installe et pourquoi (la première victoire
      de son audit, pas « un système »).
- [ ] Accord explicite pour toute prise en main à distance, à chaque session — pas
      d'accès permanent silencieux.
- [ ] Accord sur ce que l'agent pourra lire/écrire (dossiers précis, pas « tout
      le disque ») — refléter les lignes rouges de l'audit.
- [ ] Dire clairement ce qu'on ne fait PAS : pas d'accès à sa banque, pas d'envoi
      sans validation, désinstallation possible à tout moment.

## Phase 1 — Smoke test machine

- [ ] `os.id` / `os.version` : système exact et contraintes connues.
- [ ] `arch`, `ram_mb`, `disk_gb` : architecture, RAM, espace disque libre
      (minimum confortable : 8 Go RAM, 20 Go libres).
- [ ] Droits administrateur : le client peut-il installer un logiciel ?
- [ ] Antivirus/EDR présent : lequel, pour anticiper les faux positifs.
- [ ] Machine partagée ? comptes séparés ? verrouillage par mot de passe ?
- [ ] Portable ou fixe, allumé quand ? (détermine ce qui peut tourner en local)
- [ ] Réseau : débit, wifi/filaire, box opérateur.
- [ ] `python_ok`, `curl_ok`, `git_ok`, `hermes_ok` : présence des prérequis
      (sinon, installés uniquement si justifiés par le module retenu).
- [ ] Outil d'assistance à distance : version, mode de connexion avec validation
      manuelle recommandé, PAS de mot de passe permanent non su par le client.
- [ ] Inventorier l'éventuel dossier de travail existant : contenu, âge, qui l'a
      créé — décider de le reprendre ou de repartir propre.

Consigner les résultats dans l'attestation de smoke test du dossier client privé,
pas dans le dépôt public.

## Phase 2 — Décision d'architecture (honnête, pas idéologique)

- [ ] Les boucles visées tournent-elles quand le poste est éteint ? Si oui
      (surveillance email, relances programmées) → proposer hybride : la partie
      24/7 sur VPS, la partie documents en local.
- [ ] Local pur : acceptable si les boucles sont « à la demande » et si la machine
      passe le smoke test.
- [ ] Trancher AVEC le client, en langage simple : « ça marche quand votre
      ordinateur est éteint » vs « tout reste chez vous ».

## Phase 3 — Installation locale (edge client — jamais serveur)

Règles du profil : le poste local ne porte ni Caddy, ni Vault, ni serveur Hermes.
Secrets locaux : backend chiffré sur la machine, rien en clair.

- [ ] Créer le dossier de travail OA propre (ex. dossier OA dédié) ou reprendre le
      dossier existant si sain : `agent/`, `logs/`, `docs/`.
- [ ] Installer les prérequis manquants (Python aligné sur la flotte, git, curl) ;
      Docker/WSL2 seulement si un module l'exige vraiment : chaque dépendance doit
      être justifiée par une boucle installée.
- [ ] Installer le client Hermes connecté au rail OA via une Machine Identity
      dédiée par agent client, jamais les credentials d'un autre agent.
- [ ] Connecteurs : OAuth réalisé PAR le client dans son navigateur ; aucun mot de
      passe transmis.
- [ ] Canal client : installer/configurer le canal choisi — un seul au départ.
- [ ] Injecter le profil agent (`agent-secretaire-profile.md` instancié avec les
      données d'audit) + les lignes rouges.
- [ ] Démarrage automatique borné : l'agent démarre avec la session utilisateur,
      s'arrête proprement, ne réinstalle rien tout seul.

## Phase 4 — Recette avec le client (le vrai critère de fin)

- [ ] Le client envoie un message à son agent depuis SON canal et reçoit une
      réponse utile.
- [ ] La première victoire de l'audit est exécutée une fois en conditions réelles
      (ex. un brouillon généré à partir de ses notes).
- [ ] Le client sait faire trois gestes seul : parler à l'agent, valider/refuser
      une proposition, demander de l'aide (page /sav/).
- [ ] Le client sait comment tout couper (et on lui montre que ça marche).
- [ ] Attestation d'activation renseignée dans le dossier client privé.

## Phase 5 — Suivi J+7

- [ ] Premier bilan hebdo envoyé par l'agent (preuve qu'il travaille).
- [ ] Mesure honnête : temps gagné, corrections nécessaires, agacements.
- [ ] Décision suivante (élargir un module, ajuster, ou pause) prise sur ces
      mesures — pas sur l'enthousiasme du jour de l'installation.

## Rollback

À tout moment : arrêt de l'agent, révocation Machine Identity côté rail,
désinstallation des composants, remise du dossier OA au client. Ses données
restent chez lui ; rien ne dépend de nous pour les lire.
