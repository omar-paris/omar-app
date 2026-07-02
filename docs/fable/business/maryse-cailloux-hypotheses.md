# Maryse — hypothèses de cailloux (à confirmer pendant l'audit)

Version : 0.1 — 2026-07-02 — Fable 2
Règle d'usage : ce sont des HYPOTHÈSES construites sur son profil (consultante
auprès de boulangeries, solo présumée, PC local, Google Workspace + Stripe
pressentis). Elles servent à écouter mieux, pas à orienter ses réponses. Ne jamais
les lui présenter comme des faits. Mettre à jour après la session :
confirmé / infirmé / nouveau.

## Hypothèses fortes (confiance haute)

| # | Caillou supposé | Pourquoi on y croit | Signal à écouter |
|---|---|---|---|
| H1 | Propositions/devis longs à produire, repartant souvent de zéro | cœur du métier de consultante ; module `devis` déjà pressenti dans son profil | « chaque proposition me prend des heures », réutilisation de vieux docs Word |
| H2 | Notes de visites terrain non structurées | consultante en tournée chez des boulangers ; la matière s'accumule (papier, téléphone, tête) | « je note dans un carnet », « je sais que je l'ai quelque part » |
| H3 | Relances qui glissent (devis sans réponse, factures) | solo = personne ne relance à sa place ; module `relances` pressenti | gêne à relancer, montants laissés de côté |
| H4 | Administratif du soir/week-end (factures, compta) | classique du solo ; module `compta` pressenti | « je fais ça le dimanche », fatigue dans la formulation |
| H5 | Suivi multi-clients dispersé (mails + fichiers + tête) | plusieurs boulangeries suivies en parallèle, pas de CRM connu | « ça dépend des clients », historique introuvable |

## Hypothèses moyennes

| # | Caillou supposé | Pourquoi | Signal |
|---|---|---|---|
| H6 | Agenda et déplacements coûteux à organiser | métier de tournées régionales | « je passe ma vie sur la route », rendez-vous déplacés |
| H7 | Supports récurrents à refaire (formations, comptes rendus, recommandations) | livrables du conseil, probablement proches d'une mission à l'autre | copier-coller d'anciens documents |
| H8 | Présence en ligne personnelle négligée | cordonnier mal chaussé : elle conseille les boulangers, son propre marketing attend | gêne ou autodérision sur le sujet |
| H9 | Veille métier chronophage ou culpabilisante (prix matières, normes, tendances boulangerie) | valeur ajoutée du conseil = être à jour | « je devrais suivre ça de plus près » |

## Hypothèses faibles (à ne tester que si l'occasion se présente)

| # | Caillou supposé | Pourquoi |
|---|---|---|
| H10 | Encaissements/paiements à fluidifier | connecteur Stripe pressenti dans son profil — à comprendre : facturation ? acomptes ? |
| H11 | Emails entrants qui s'accumulent | universel, mais volume inconnu pour elle |
| H12 | Peur de l'usine à gaz technologique | cas pilote PC local — le choix « chez moi, sur ma machine » peut traduire un besoin de contrôle |

## Faux cailloux probables (vigilance)

- **Tout automatiser la production de conseil** : son jugement métier EST le produit ;
  l'agent prépare et structure, il ne conseille pas les boulangers à sa place.
  Si elle le demande, honnêteté : c'est la ligne « ce qui doit rester humain ».
- **Site web / marketing avancé en premier** : séduisant, mais probablement pas le
  caillou le plus douloureux au quotidien — à classer derrière les gains de temps
  admin sauf si elle démontre le contraire.

## Données de tiers — point de vigilance propre à Maryse

Ses dossiers contiennent des données de SES clients boulangers (chiffres, marges,
peut-être données salariés). Toute automatisation chez elle traite donc des données
de tiers : le rapport et l'onboarding devront le nommer explicitement (garde-fous,
anonymisation, pas d'envoi externe sans validation).

## Après la session

Pour chaque hypothèse : statut (confirmé / infirmé / non abordé), verbatim de Maryse
si confirmé, scoring selon `audit-output-schema.json` (douleur, fréquence, temps
perdu, faisabilité, risque, catégorie). Les nouveaux cailloux non prévus ici sont
les plus précieux : ils mesurent ce que nos hypothèses valent.
