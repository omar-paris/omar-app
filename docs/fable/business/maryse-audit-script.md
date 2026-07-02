# Audit Maryse — déroulé pour la session de demain

Version : 0.1 — 2026-07-02 — Fable 2
Compagnons : `maryse-cailloux-hypotheses.md` (à confirmer/infirmer pendant la session),
`maryse-readiness-questions.md` (infos pratiques à capter avant la fin).

## Qui est Maryse (ce qu'on sait)

- **Consultante auprès de boulangeries** (profil pilote `omar-top/profiles/maryse-pc.yml`).
- Cas pilote **PC local** (pas VPS a priori) — le PC n'a pas encore été qualifié
  (OS, RAM, disque : champs vides dans le profil).
- Modules pressentis : secrétaire, compta, devis, relances.
- Connecteurs pressentis : Google Workspace, Stripe.
- Tout cela reste **hypothèse** tant que l'audit ne l'a pas confirmé : c'est
  précisément le but de demain.

## Dispositif de la session

- Maryse **seule devant l'écran** (son PC ou celui d'Alex), sur
  `app.omar.paris/audit/`.
- Alex à côté : il observe, ne pilote pas. Il n'intervient que si Maryse bloque.
- **Enregistrement d'écran activé** (souris, hésitations, relectures) — c'est notre
  premier test utilisateur réel du produit audit, autant que l'audit de Maryse.
- Durée : pas de chrono. Prévoir 45-60 min de tranquillité. Maryse peut s'arrêter
  quand elle veut ; la session doit être reprenable.

## À savoir avant de commencer (honnêteté interne)

La version d'audit actuellement en ligne est la V0.5.0 **déterministe** : 9 étapes
séquentielles, questions prédéfinies, pas de moteur conversationnel LLM. Elle est
fonctionnelle et sérieuse, mais elle ne creusera pas d'elle-même les signaux faibles
comme le fera la version cible (`audit-model.md`).

Conséquence pratique : **le rôle d'Alex est d'incarner la profondeur manquante** —
quand une réponse de Maryse mérite d'être creusée, Alex pose oralement la relance
(voir les relances ci-dessous) et Maryse enrichit sa réponse écrite. On note ces
moments : chaque relance orale d'Alex = une relance que la V-cible devra savoir
faire seule.

Autre point : l'accès à app.omar.paris passe par OAuth Google. Vérifier AVANT la
session que l'email de Maryse (ou un email invité) est autorisé, sinon prévoir la
session sur le compte d'Alex.

## Déroulé conseillé

### 1. Cadrage oral par Alex (2 min, avant l'écran)

Dire simplement, sans survendre :
« J'ai préparé un audit. Tu vas discuter avec mon agent, Omar. Il va te poser des
questions sur ton activité — réponds comme tu parles, il n'y a pas de bonne réponse.
Tu peux passer les sujets qui ne t'intéressent pas. À la fin, tu auras un rapport
personnalisé. Moi je reste à côté, je te laisse faire. »

Et une phrase de consentement : « J'enregistre l'écran pour améliorer l'outil,
ça te va ? »

### 2. Socle (étapes intro / activity / research de l'app)

Laisser faire. Points d'attention :

- Maryse choisira tutoiement/vouvoiement et le mode de conversation — noter son choix.
- Étape `research` (sources publiques) : elle donnera ou non son site, sa fiche
  Google, son SIRET. Ne pas pousser ; son niveau de confiance ici est une donnée.

### 3. Cœur (étapes pain / tools / risk / opportunities)

C'est là que les hypothèses de `maryse-cailloux-hypotheses.md` se confirment ou
tombent. Relances orales d'Alex, seulement si l'app reste en surface :

- Sur les journées : « Raconte une semaine type — tu es en tournée chez les
  boulangers ou au bureau ? Qu'est-ce qui déborde le soir ? »
- Sur les devis/propositions : « Quand tu fais une proposition à une boulangerie,
  ça te prend combien de temps ? Tu repars de zéro à chaque fois ? »
- Sur le suivi clients : « Tes notes de visite, elles vont où ? Tu les retrouves ? »
- Sur les relances : « Un devis sans réponse, une facture en retard — tu relances
  quand, et qu'est-ce que ça te coûte de le faire ? »
- Sur les chiffres spontanés : TOUJOURS creuser (« deux soirées par mois » → sur quoi
  exactement ?).
- Une seule question « cachée », au bon moment : « Qu'est-ce qui t'agace le plus
  dans tout ça ? »

À l'étape `risk`, veiller à ce que soient posées les lignes rouges : données de SES
clients boulangers (elle est intermédiaire — ses données incluent les données de
tiers), ce qu'un agent ne doit jamais envoyer/payer/promettre seul.

### 4. Clôture (étapes autonomy / validation)

- Laisser Maryse corriger la synthèse — la correction vaut plus que la synthèse.
- Recueillir son mode : apprendre / déléguer / mixte.
- Avant de fermer : passer en revue `maryse-readiness-questions.md` (oralement si
  l'app ne les couvre pas) — PC, canaux, comptes existants, timing. Jamais de mots
  de passe.

### 5. Sortie et suite (5 min)

- Générer et montrer le rapport à l'écran ; proposer l'envoi email / téléchargement.
- Si Maryse est réceptive, montrer l'estimation « si Omar & Alex s'en occupe »
  (page /devis/ pré-orientée). Ne pas conclure de vente à chaud : dire qu'une
  proposition propre suivra sous 48 h, construite sur le rapport.
- Remercier pour le temps donné : c'est la vraie monnaie de l'audit gratuit.

## Grille d'observation (pour l'enregistrement et les notes d'Alex)

Produit (test utilisateur) :

- Où hésite la souris ? Quelles questions font relire deux fois ?
- À quel moment l'attention décroche (réponses qui raccourcissent) ?
- Les étapes affichées donnent-elles envie d'aller au bout ?
- Qu'a-t-elle demandé à voix haute que l'app aurait dû savoir dire ?

Audit (fond) :

- Les 3 cailloux qui reviennent le plus dans ses mots.
- Un chiffre de temps perdu par semaine, au moins un, confirmé par elle.
- Ses lignes rouges explicites.
- Son niveau de confiance envers l'IA (mots exacts).

## Après la session

1. Consigner les réponses dans le schéma `audit-output-schema.json` (même à la main
   pour cette première fois) — c'est la donnée qui nourrira devis et onboarding.
2. Lister les relances orales qu'Alex a dû faire : c'est le backlog de la V-cible.
3. Mettre à jour `maryse-cailloux-hypotheses.md` (confirmé / infirmé / nouveau).
4. Préparer la restitution : rapport + estimation, envoyés sous 48 h.

## Plan B (si l'app est indisponible ou bloque)

Mener l'audit en conversation directe, Alex posant les questions du socle puis des
sujets S1, S2, S4, S5, S6 de `audit-question-bank.md` (les plus probables pour une
consultante), en notant les verbatims. Le rapport sera rédigé ensuite à partir des
notes — l'important est la matière, pas l'outil.
