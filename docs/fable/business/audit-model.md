# Modèle d'audit OA — conversation de diagnostic générique

Version : 0.1 — 2026-07-02 — Fable 2 (couloir business/produit)
Statut : proposition, à valider par Alex puis à implémenter dans AppOmar.
Sources : brief `brief-fable-business-audit-onboarding-20260701.md`, audit existant AppOmar
(`src/audit_intelligence.py`, `pages-app/audit.html`), onboarding qgfinance
(`qgfinance-site/backend/main.py`), audit Google Form 2024 (présence en ligne),
landing V0.4.1, échanges Alex 2026-07-01/02.

---

## 1. Ce qu'est l'audit

L'audit est **le produit** que la landing vend aujourd'hui. Il est gratuit en argent,
payé en temps et en confiance : si un indépendant nous donne 20 minutes de
conversation sincère sur son activité, c'est déjà une vente réussie.

Ce n'est pas un formulaire. C'est une occasion rare, pour un artisan, un commerçant,
un consultant ou une profession libérale, de **parler de son business** avec un
interlocuteur qui écoute tout, ne juge pas, n'oublie rien, et produit à la fin un
diagnostic personnalisé réellement utile.

Trois exigences fondatrices :

1. **Profondeur** : chaque question doit apprendre quelque chose au client sur
   lui-même. Les options de réponse elles-mêmes sont auto-diagnostiques (héritage du
   Form 2024 : « Oui, ma fiche est optimisée à 100 % » / « Je ne sais pas » — répondre,
   c'est déjà se situer).
2. **Liberté** : le client choisit de quoi il parle. Un sujet peut durer 15 secondes
   (« pas envie d'en parler ») ou 15 minutes (ça le passionne ou ça le ronge). On ne
   chronomètre pas.
3. **Honnêteté** : limites réelles de l'IA en 2026, pas de magie, pas de promesse de
   connexion non vérifiée, petites victoires d'abord.

Et une exigence produit : **double sortie**. L'audit produit à la fois le rapport
humain (long, personnalisé, la valeur perçue) et une donnée structurée
(`audit-output-schema.json`) qui alimente automatiquement le devis puis l'onboarding.
Le rapport impressionne ; la donnée exécute. C'est ce qui évite que le client reste
« coincé avec un très long document » : chez nous, le document a une suite en un clic.

## 2. Place dans le tunnel

| Étape | Rôle | Support |
|---|---|---|
| Landing | Attire | landing.omar.paris, recentrée audit |
| **Audit** | **Intéresse** | app.omar.paris/audit — ce document |
| Restitution + devis | Crée le désir | rapport + estimation prix générée depuis la donnée d'audit |
| Onboarding | Action | configuration agent + provisioning, pré-rempli par l'audit |

Contrat de conception transversal : **aucune information demandée deux fois**.
Ce que l'audit apprend, le devis et l'onboarding le réutilisent.

## 3. Architecture de la conversation : socle + carte + clôture

L'audit n'est PAS un couloir linéaire de N étapes. Il a trois temps, dont le
deuxième est modulaire.

### Temps 1 — Socle (obligatoire, 3-5 min)

Reprend et resserre les étapes `intro`, `activity`, `research` de l'existant :

- **Calibrage** : tutoiement/vouvoiement, mode (guidé / libre / synthèses), aisance
  numérique et IA. Ce calibrage pilote le ton et la profondeur de toute la suite.
- **Portrait express** : métier exact, localisation/zone, taille, ancienneté,
  typologie de clients, ordre de grandeur du CA (refus possible et respecté).
- **Consentements sources publiques** : site, fiche Google, SIRET, réseaux — par type
  de source, avec refus explicite possible (mécanisme déjà en place, à conserver).

À la fin du socle, l'agent détecte le secteur (mécanisme `detect_sector()` existant)
et personnalise la carte des sujets.

### Temps 2 — Exploration (le cœur, modulaire, 10-60+ min)

L'agent présente une **carte de sujets** (~10) adaptée au secteur, et propose un
ordre — mais le client reste maître : il choisit, saute, revient, approfondit.

Sujets génériques (déclinés par secteur via `data/audit_sectors/*.json`) :

| # | Sujet | Ce qu'on cherche |
|---|---|---|
| S1 | Vos journées et votre temps | routines réelles, où part l'énergie, charge mentale |
| S2 | Vos clients | acquisition, fidélisation, relation, grincheux |
| S3 | Communication et présence en ligne | site, fiche Google, réseaux, avis |
| S4 | Paperasse et administratif | factures, devis, compta, courrier, obligations |
| S5 | Relances, impayés et suivis | ce qui se perd, ce qui traîne, ce qui coûte |
| S6 | Organisation et information | documents, notes, « où sont les choses » |
| S7 | Outils et abonnements | stack actuelle, doubles saisies, ruptures |
| S8 | Équipe et délégation | qui fait quoi, dépendances, fragilités |
| S9 | Sécurité et lignes rouges | données sensibles, ce qu'on n'automatise jamais |
| S10 | Vos projets, envies et rapport à l'IA | ambitions, peurs, expériences passées, colères |

Chaque sujet est un **module** avec la même mécanique interne :

1. *Ouverture* : une question large, facile, qui invite à raconter.
2. *Approfondissement adaptatif* : 2 à 5 questions selon les signaux (voir §4),
   mélange de texte libre et de micro-choix QCM quand ça allège.
3. *Extraction de cailloux* : chaque irritant détecté est nommé, qualifié
   (fréquence, douleur, temps perdu, contournement actuel) et confirmé par le client.
4. *Mini-synthèse validée* : « Voilà ce que j'ai compris sur ce sujet — c'est juste ? »
   (le pattern reformulation humble + validation des STEP_CONTRACTS existants).

Règles du temps 2 :

- **Sauter est une donnée.** Un sujet refusé est enregistré `skipped`, sans
  culpabilisation ni insistance. Un refus sec sur un sujet sensible (ex. impayés)
  est un signal en soi, noté comme hypothèse, jamais renvoyé au client.
- **Pas de minimum imposé.** Trois sujets explorés à fond valent mieux que dix
  survolés. L'agent recommande de couvrir au moins S1 + le sujet le plus douloureux.
- **La carte reste visible** (UI : progression par sujet, à la manière de la colonne
  étapes de qgfinance), le client voit ce qui reste et décide quand s'arrêter.

### Temps 3 — Clôture (obligatoire, 5-10 min)

Reprend `opportunities`, `autonomy`, `validation` de l'existant, enrichis :

1. **Tri des cailloux ensemble** : l'agent présente la liste collectée et propose un
   classement gros / moyens / petits / faux (voir §5). Le client corrige — c'est SA
   hiérarchie qui compte, l'agent argumente seulement le réalisme.
2. **Limites dites en face** : ce que l'IA 2026 fait bien, ce qu'elle fait mal, ce
   qui exigera toujours validation humaine, ce qui demande un setup particulier.
3. **Premières victoires** : 2-3 boucles crédibles à moins de deux semaines,
   choisies parmi les gros cailloux faisables.
4. **Niveau d'accompagnement** : apprendre / déléguer / mixte, rythme réaliste.
5. **Synthèse générale validée** : vrai / hypothétique / manquant (pattern existant).
6. **Sortie** — quatre options, toutes disponibles :
   - visualiser le rapport à l'écran ;
   - le recevoir par email ;
   - le télécharger (Markdown/PDF) ;
   - **« Combien ça coûterait avec Omar & Alex ? »** → estimation générée depuis
     `build_devis_source()` (existant, à enrichir), avec offre promotionnelle
     éventuelle (coupon, premier mois, essai). C'est le pont vers le devis.

## 4. Mécanique d'adaptation

Signaux qui déclenchent l'approfondissement d'un sujet :

- **émotion** : agacement, lassitude, fierté, inquiétude dans la formulation ;
- **chiffres spontanés** (« ça me prend deux soirées par mois ») : toujours creuser ;
- **répétition** : un thème qui revient dans plusieurs sujets est un gros caillou
  probable ;
- **absolus** : « toujours », « jamais », « personne d'autre ne peut le faire » ;
- **auto-accusation** : « je devrais… mais je ne le fais jamais » — c'est de la
  charge mentale, pas une faute ; reformuler sans culpabiliser.

Le caché (peurs, colères, désirs) s'écoute, ne s'extorque pas : une seule question
douce par sujet maximum (« qu'est-ce qui vous agace le plus là-dedans ? »), et le
sujet S10 offre un espace dédié en fin de parcours, quand la confiance est établie.

Adaptation au niveau : le calibrage du socle fixe un registre (novice / à l'aise /
avancé) qui change le vocabulaire, la part de QCM (plus de micro-choix pour les
novices), et la précision technique des exemples.

## 5. Scoring et classement des cailloux

Chaque caillou confirmé porte :

| Champ | Échelle | Sens |
|---|---|---|
| `douleur` | 1-5 | intensité ressentie |
| `frequence` | 1-5 | quotidien=5 … annuel=1 |
| `temps_perdu` | h/semaine estimées | déclaré ou estimé ensemble |
| `faisabilite` | 1-5 | réalisme IA 2026, jugé par l'agent |
| `risque` | 1-5 | sensibilité données / conséquences d'erreur |

Classement (proposé par l'agent, arbitré par le client) :

- **Gros caillou** : douleur×fréquence élevées ET faisabilité ≥ 3 ET risque maîtrisable
  avec garde-fous. C'est là qu'on commence.
- **Moyen** : utile, mais moins douloureux ou moins fréquent.
- **Petit** : confort, automatisable plus tard.
- **Faux caillou** : séduisant mais faisabilité basse, risque élevé ou ROI faible.
  On le dit honnêtement, avec la raison — c'est ce qui crée la confiance.

## 6. Artefacts de sortie

1. **Rapport humain** (structure héritée de `build_audit_report()`, enrichie) :
   portrait ; carte des cailloux classés avec verbatims ; opportunités ; limites et
   lignes rouges ; premières victoires ; trajectoire ; tutoriel + prompts pour
   démarrer seul. Ton : celui du brief (humain, précis, pas magique).
2. **Donnée structurée** : `audit-output-schema.json` (fichier voisin) — la colonne
   vertébrale audit → devis → onboarding.
3. **Source de devis** : recommandations catalogue avec raison et confiance
   (`build_devis_source()` existant, à faire pointer sur les cailloux plutôt que sur
   les seules réponses brutes : chaque ligne de devis cite le caillou qui la justifie).

## 7. Implémentation — s'appuyer sur l'existant, ne rien réinventer

Constat : AppOmar `/audit/` V0.5.0 est **déterministe** (aucun LLM branché) ; la
profondeur conversationnelle visée exige un moteur génératif. qgfinance
(`backend/main.py`) a exactement ce moteur : prompt système dynamique
(étape + profil accumulé + historique), tokens de contrôle `[PROFILE:k=v]`,
`[DOC:...]`, `[NEXT_STEP]`, sessions JSON, front 3 colonnes.

Chemin recommandé (chantier code B4, périmètre à confirmer avec H-Omar) :

- porter le mécanisme qgfinance dans `proposal_server.py` / `audit_intelligence.py` ;
- remplacer la logique linéaire `[NEXT_STEP]` par une navigation par sujets :
  tokens `[CAILLOU:{json}]`, `[SUJET:S4=done|skipped]`, `[SYNTHESE:...]` ;
- les `STEP_CONTRACTS` existants deviennent les contrats du socle et de la clôture ;
  les `data/audit_sectors/*.json` deviennent les banques de questions par sujet×secteur
  (bakery.json est déjà riche et sert de gabarit) ;
- l'UI audit.html adopte la carte des sujets (colonne gauche) + chat (centre) +
  cailloux collectés en direct (colonne droite) — le client voit son audit se
  construire, comme les documents dans qgfinance.

Garde-fous inchangés : jamais de secrets ni mots de passe dans l'audit, consentements
par source, validation humaine avant toute action externe, aucune action payante.

## 8. Ce que ce modèle ne fait pas

- Il ne vend pas pendant l'exploration : le prix n'apparaît qu'en clôture, à la
  demande du client.
- Il ne promet aucune intégration non vérifiée (règle brief).
- Il ne remplace pas l'onboarding : il le prépare. La configuration effective
  (agent, canaux, droits, VPS/PC) vit dans `onboarding-after-audit.md` (mission B3).
