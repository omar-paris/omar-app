# Checklist installation — PC Windows accompagné (et repères VPS/hybride)

Version : 0.1 — 2026-07-02 — Fable 2
Cas visé : Maryse (PC Windows, profil `omar-top/profiles/maryse-pc.yml`), mais la
checklist est générique pour tout client en option « PC accompagné ».
Exécution : Alex + H-Omar. Fable 2 ne provisionne pas et ne manipule pas de secrets.

## État déclaré (Alex, 2026-07-02 — à vérifier, rien n'est pris pour acquis)

- Une connexion VPS ↔ PC de Maryse existerait déjà.
- RustDesk serait installé (contrôle à distance).
- Un dossier « maintenance PC » (nom approximatif) existerait sur sa machine.

Aucune trace vérifiable de cet état sur le VPS : le smoke test ci-dessous doit
tout reconfirmer avant d'installer quoi que ce soit.

## Phase 0 — Consentement (5 min, avec la cliente)

- [ ] Expliquer en une phrase ce qu'on installe et pourquoi (la première victoire
      de son audit, pas « un système »).
- [ ] Accord explicite pour la prise en main à distance (RustDesk), à chaque
      session — pas d'accès permanent silencieux.
- [ ] Accord sur ce que l'agent pourra lire/écrire (dossiers précis, pas « tout
      le disque ») — refléter les lignes rouges de l'audit.
- [ ] Dire clairement ce qu'on ne fait PAS : pas d'accès à sa banque, pas d'envoi
      sans validation, désinstallation possible à tout moment.

## Phase 1 — Smoke test machine (champs requis du profil OmarTop)

- [ ] `os.id` / `os.version` : édition et version Windows exactes (Windows 10/11,
      Famille/Pro) — Pro requis pour certaines options ; noter la version.
- [ ] `arch`, `ram_mb`, `disk_gb` : architecture, RAM, espace disque libre
      (minimum confortable : 8 Go RAM, 20 Go libres).
- [ ] Droits administrateur : la cliente peut-elle installer un logiciel ?
- [ ] Antivirus/EDR présent : lequel, pour anticiper les faux positifs.
- [ ] Machine partagée ? comptes Windows séparés ? verrouillage par mot de passe ?
- [ ] Portable ou fixe, allumé quand ? (détermine ce qui peut tourner en local)
- [ ] Réseau : débit, wifi/filaire, box opérateur.
- [ ] `python_ok`, `curl_ok`, `git_ok`, `hermes_ok` : présence des prérequis
      (sinon, installés en phase 3).
- [ ] RustDesk : version, mode de connexion (ID + validation manuelle recommandé),
      PAS de mot de passe permanent non su par la cliente.
- [ ] Inventorier le dossier « maintenance PC » existant : contenu, âge, qui l'a
      créé — décider de le reprendre ou de repartir propre.

Consigner les résultats dans `attestations.pc_smoke` du profil
`maryse-pc.yml` (aujourd'hui `null`).

## Phase 2 — Décision d'architecture (honnête, pas idéologique)

- [ ] Les boucles visées tournent-elles quand le PC est éteint ? Si oui
      (surveillance email, relances programmées) → proposer hybride : la partie
      24/7 sur VPS, la partie documents en local.
- [ ] PC pur : acceptable si les boucles sont « à la demande » et si la machine
      passe le smoke test.
- [ ] Trancher AVEC la cliente, en langage simple : « ça marche quand votre
      ordinateur est éteint » vs « tout reste chez vous ».

## Phase 3 — Installation PC (edge client — jamais serveur)

Règles du profil : le PC ne porte ni Caddy, ni Vault, ni serveur Hermes.
Secrets locaux : backend `age_local` (chiffrés sur sa machine), rien en clair.

- [ ] Créer le dossier de travail OA propre (ex. `C:\OA\` ou reprise du dossier
      maintenance existant si sain) : `agent/`, `logs/`, `docs/`.
- [ ] Installer les prérequis manquants (Python 3.11 — version alignée sur la
      flotte —, git, curl) ; Docker/WSL2 seulement si un module l'exige vraiment :
      chaque dépendance doit être justifiée par une boucle installée.
- [ ] Installer le client Hermes (agent h-maryse) connecté au rail OA via
      tailnet — Machine Identity dédiée par agent client (règle phases-spec
      P3.5), jamais les credentials d'un autre agent.
- [ ] Connecteurs (Google Workspace, Stripe si confirmés par l'audit) : OAuth
      réalisé PAR la cliente dans son navigateur ; aucun mot de passe transmis.
- [ ] Canal client : installer/configurer le canal choisi (Telegram, WhatsApp,
      email, Hermes Desktop) — un seul au départ.
- [ ] Injecter le profil agent (`agent-secretaire-profile.md` instancié avec les
      données d'audit) + les lignes rouges.
- [ ] Démarrage automatique borné : l'agent démarre avec la session Windows,
      s'arrête proprement, ne réinstalle rien tout seul.

## Phase 4 — Recette avec la cliente (le vrai critère de fin)

- [ ] La cliente envoie un message à son agent depuis SON canal et reçoit une
      réponse utile.
- [ ] La première victoire de l'audit est exécutée une fois en conditions réelles
      (ex. un brouillon de proposition généré à partir de ses notes).
- [ ] Elle sait faire trois gestes seule : parler à l'agent, valider/refuser une
      proposition, demander de l'aide (page /sav/).
- [ ] Elle sait comment tout couper (et on lui montre que ça marche).
- [ ] `attestations.agent_activated` renseigné dans le profil ; compte rendu
      d'installation déposé dans `clients/maryse/`.

## Phase 5 — Suivi J+7

- [ ] Premier bilan hebdo envoyé par l'agent (preuve qu'il travaille).
- [ ] Mesure honnête : temps gagné, corrections nécessaires, agacements.
- [ ] Décision suivante (élargir un module, ajuster, ou pause) prise sur ces
      mesures — pas sur l'enthousiasme du jour de l'installation.

## Rollback

À tout moment : arrêt de l'agent (service Windows), révocation Machine Identity
côté rail, désinstallation des composants, remise du dossier OA à la cliente.
Ses données restent chez elle ; rien ne dépend de nous pour les lire.
