# De l'audit à l'onboarding — le passage à l'action

Version : 0.1 — 2026-07-02 — Fable 2
Compagnons : `audit-model.md`, `audit-output-schema.json`, `agent-secretaire-profile.md`,
`local-pc-vps-checklist.md`.

## Principe

L'onboarding n'invente rien : il **exécute ce que l'audit a appris**. Le fichier
`audit-output-schema.json` est le contrat entre les deux : cailloux classés,
lignes rouges, outils existants, canaux préférés, readiness machine, mode
d'autonomie. Le client ne répète jamais une information déjà donnée.

Tunnel complet : landing (attire) → audit (intéresse) → rapport + devis (désir)
→ **onboarding (action)** → conversation quotidienne avec son agent.

## Déclencheur

L'onboarding démarre quand le devis est accepté — y compris un devis à 0 €
(offre pilote, ex. « Installation PC Windows — offre pilote » du catalogue).
L'acceptation vaut GO commercial ; elle ne vaut PAS GO technique : toute action
payante ou irréversible reste soumise au GO humain
(`human_go_required_before_paid_actions`, mécanisme existant d'AppOmar).

## Les 6 étapes (reprennent l'onboarding AppOmar existant, nourries par l'audit)

| # | Étape | Pré-rempli par l'audit | Reste à décider avec le client |
|---|---|---|---|
| 1 | Identité | nom, entreprise, métier, email | domaine éventuel |
| 2 | Objectifs | gros cailloux → premières boucles | ordre des 2-3 premières victoires |
| 3 | Outils & connexions | outils déclarés, consentements | quels comptes brancher en premier (noms seulement, jamais de secrets dans AppOmar) |
| 4 | Infrastructure | readiness.infra_preference + pc_specs | VPS managé / PC accompagné / hybride — décision finale après smoke test |
| 5 | Agent | mode d'autonomie, canaux préférés, lignes rouges | nom de l'agent, ton, périmètre d'autonomie initial |
| 6 | Récap & GO | tout | accord explicite → plan de provisioning |

## Le plan de provisioning

À l'étape 6, AppOmar génère le plan (mécanisme dry-run existant,
`omartop.provisioning-contract.v1`) :

- **VPS** : location serveur → bootstrap OmarTop (skill `omar-top-bootstrap`,
  `phases-spec.yaml`) → applis infra + applis métier → agent Hermes → canaux.
- **PC (Windows)** : voir `local-pc-vps-checklist.md` — vérification machine,
  smoke test, installation accompagnée. Le PC est un « edge client » : il ne porte
  ni Caddy, ni Vault, ni serveur Hermes (règle profil `maryse-pc.yml`).
- **Hybride** : serveur pour la fiabilité 24/7 (relances, surveillance boîte mail),
  PC pour les usages locaux (documents, dossiers du client).

Les interactions client sont réduites au strict nécessaire et regroupées :
consentements, mots de passe saisis PAR le client dans les interfaces des
services concernés (jamais transmis via chat ou AppOmar), décisions de canal.
Tout le reste est automatisé ou fait par l'équipe.

## Après l'installation : l'agent prend le relais

Le plan issu de l'audit est remis à l'agent du client (fichiers de profil +
premières boucles). C'est ensuite **la conversation entre le client et son agent**
qui fait vivre le système : l'agent connaît les cailloux, propose la première
victoire, apprend les préférences, montre qu'il travaille (bilan hebdomadaire).

Support et contrôle côté client, via AppOmar :

- **/sav/** : discuter avec un agent support qui peut diagnostiquer et corriger
  (ex. Hermes Desktop qui ne répond plus) — uniquement dans le cadre des
  autorisations accordées.
- **Autorisations activables/désactivables par le client** (à construire — même
  logique que les consentements d'audit) : accès distant au PC (RustDesk),
  accès à certains dossiers, recherche Internet, actions par service connecté.
  Par défaut : tout est fermé ; chaque ouverture est explicite, datée, révocable.

## Garde-fous non négociables

1. Aucun secret ne transite par AppOmar, l'audit ou le chat.
2. Aucune action payante sans GO humain explicite (mécanisme existant conservé).
3. Actions sensibles (envoyer, payer, publier, promettre) : l'agent prépare,
   le client valide — conformément aux lignes rouges de SON audit.
4. Le client peut tout arrêter : autorisations révocables, données exportables.
5. On installe d'abord la première victoire, pas tout le catalogue : la confiance
   se construit par preuves.
