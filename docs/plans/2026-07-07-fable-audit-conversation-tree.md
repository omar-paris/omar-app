# Arbre conversationnel Audit Omar & Alex — design Fable

*Fable, designer produit/conversationnel — 07/07/2026. Réponse au brief `2026-07-07-fable-audit-conversation-tree-prompt.md`. Ancré dans l'existant : moteur auditbiz (choice/rank/confirm), 8 packs secteur, rail 8 étapes, prompt Omar (coach, ≤4 lignes, zéro vente), et le feedback fondateur d'Alex : « les questions étaient trop fermées, on n'avançait pas ».*

## 1. Synthèse

L'audit est conçu comme **une conversation de coach en 3 actes** — la Rencontre (5 min), la Plongée (10-12 min), la Livraison (3 min + rapport) — et non un questionnaire en 12 écrans. Le principe directeur qui corrige le défaut constaté : **la règle 70/30** — Omar pose des questions *ouvertes* de coach (70 %), et les boutons ne servent qu'à *accélérer la confirmation* de ce qu'il a compris (30 %), jamais à poser la question à la place de l'écoute. Le mécanisme de confiance central est la **carte « Ce qu'Omar a compris »** en fin de chaque acte : le client corrige d'un tap, et c'est cette carte validée — pas les réponses brutes — qui nourrit le rapport et l'onboarding. La profondeur métier vient des packs secteur existants (8 déjà écrits), injectés comme *relances* dans les questions ouvertes, pas comme QCM. Le tout doit se traverser sur mobile, pouce et fatigue compris, en moins de 20 minutes pour la V0.

## 2. Tableau maître — étapes × interaction × données × sorties

| # | Étape (acte) | Interaction dominante | Données collectées | → Rapport | → Onboarding |
|---|---|---|---|---|---|
| 0 | Accueil & pacte (R) | quick_replies | vouvoiement imposé, rythme, temps dispo | — | preferences |
| 1 | Activité (R) | free_text + quick_replies confirm | métier réel, taille, zone, ancienneté | company_context | business_type, location, team_size |
| 2 | Sources publiques (R) | consent_gate + file_or_url | URLs autorisées (site, GMB, réseaux), consentement par source | verified_sources | allowed_sources |
| 3 | La semaine réelle (P) | free_text (cœur du coach) | routines, volumes, « cailloux », émotions | pain_map, time_sinks | candidate_routines |
| 4 | Outils & flux (P) | free_text + checklist confirm | outils réels, ruptures de flux, double-saisies | tool_stack, flow_breaks | connectors_candidates |
| 5 | Données & limites (P) | consent_gate + quick_replies | données sensibles, interdits client, conformité métier | risk_register | forbidden_data, guardrails |
| 6 | Opportunités & tri (P) | validation_card + rank | opportunités IA reformulées, priorités client | opportunities, roi_hypotheses | mission_candidates |
| 7 | Autonomie souhaitée (P) | slider + quick_replies | apprendre/déléguer/mixte, validations humaines voulues | autonomy_profile | human_gates |
| 8 | Carte de synthèse (L) | validation_card éditable | corrections finales du client | client_validated_summary | (verrouille tout) |
| 9 | Rapport + suites (L) | validation + CTA | choix des suites (devis/onboarding/rappel Alex) | — | agent_charter, dry_run_contract |

Étapes 10-11 du brief (prompts/CLI, onboarding détaillé) = **sorties du rapport** (sections générées), pas des étapes conversationnelles — un dirigeant fatigué ne « converse » pas sur des prompts CLI ; il les reçoit dans son livrable.

## 3. Arbre YAML complet

### Acte I — la Rencontre

```yaml
step_id: welcome_pact
acte: rencontre
label: Accueil & pacte
completion_goal: Le client sait à quoi s'attendre (durée, gratuité, contrôle). Le vouvoiement est imposé pour l'audit public.
entry_message: "Bonjour, je suis Omar, un agent formé par Alexandre Willemetz et biberonné sur les meilleurs standard en gestion et en informatique. Je vais vous poser des questions. Vous me répondez à votre rythme et selon vos objectifs. A la fin vous pourriez télécharger votre Audit Business & Tech."
inputs:
  - id: rythme
    type: quick_replies
    required: true
    question: "Tu préfères aller droit au but, ou prendre le temps ?"
    options: ["Droit au but", "Prendre le temps"]
  - id: temps_dispo
    type: quick_replies
    required: false
    question: "Tu as combien de temps là, maintenant ?"
    options: ["10 min", "20 min", "Pas de limite"]
validation:
  ready_when: [pacte présenté, rythme present]
branches:
  - if: temps_dispo == "10 min"
    then: activer_mode_express   # saute les relances d'approfondissement non critiques
  - if: rythme == "Droit au but"
    then: messages_encore_plus_courts
report_fields: []
onboarding_fields: [communication_preferences: vouvoiement]
signaux_risque: []
notes_ui: "Barre de progression apparaît APRÈS ce step (3 actes affichés, pas 10 étapes)."
```

```yaml
step_id: activity
acte: rencontre
label: Activité
completion_goal: Comprendre qui est l'entreprise, son vrai métier (pas l'étiquette), son contexte.
entry_message: "Racontez-moi votre activité simplement : vous faites quoi, où, avec qui ?"
inputs:
  - id: business_story
    type: free_text
    required: true
    # UNE question ouverte. Le moteur en extrait métier/taille/zone ; il ne
    # demande ENSUITE que ce qui manque, en confirmation rapide.
  - id: company_size
    type: quick_replies
    required: true
    condition: non_extrait_de(business_story)
    question: "Vous êtes combien à bosser, en vrai ?"
    options: ["Solo", "2-5", "6-20", "20+"]
  - id: anciennete
    type: quick_replies
    required: false
    question: "L'affaire existe depuis... ?"
    options: ["< 2 ans", "2-10 ans", "10+ ans", "Je reprends/lance"]
validation:
  ready_when: [métier identifié, taille identifiée, zone identifiée]
branches:
  - if: secteur_detecte in packs_disponibles     # bakery, plumber, restaurant, lawyer…
    then: charger_pack_secteur                    # les relances métier viennent du pack
  - if: secteur_detecte == null
    then: charger_pack_generic_tpe + demander_metier_en_clair
  - if: profession_reglementee (avocat, santé, finance)
    then: activer_guardrails_reglementes          # prudence conformité dès maintenant
  - if: commerce_local
    then: noter_pertinence_gmb_pour_step_sources
report_fields: [company_context, sector_hypothesis]
onboarding_fields: [business_type, location, team_size]
signaux_risque: ["multi-activités confuses → relance de clarification", "taille incohérente avec le récit"]
exemples_omar:
  - "Boulanger à Clichy, 4 personnes, four allumé à 4h — c'est noté. Le snacking du midi, c'est une grosse part ?"
  - "Donc plutôt rénovation que dépannage d'urgence, c'est ça ?"
```

```yaml
step_id: sources
acte: rencontre
label: Sources publiques & preuves
completion_goal: Obtenir le droit EXPLICITE, source par source, de regarder ce qui est public — et rien d'autre.
entry_message: "Si vous me montrez où vous existez en ligne, je peux vérifier des choses par moi-même au lieu de vous poser 15 questions. Vous m’autorisez à regarder quoi ?"
inputs:
  - id: consent_sources
    type: consent_gate            # NOUVEAU type — un toggle PAR source, jamais global
    required: true
    options:
      - {source: site_web, ask: "Votre site web ?", field: url}
      - {source: google_business, ask: "Votre fiche Google ?", field: url_ou_nom}
      - {source: reseaux, ask: "Un réseau social pro ?", field: url}
      - {source: avis, ask: "Tes avis clients publics ?", field: implicite_si_gmb}
  - id: docs_optionnels
    type: file_or_url
    required: false
    question: "Un document utile à me montrer ? (plaquette, grille tarifs…) — optionnel"
validation:
  ready_when: [consent_sources répondu (même si tout refusé)]
branches:
  - if: au_moins_une_source_autorisee
    then: lancer_recherche_publique_en_arriere_plan   # pendant l'acte II — les résultats
                                                       # nourrissent la carte de synthèse
  - if: tout_refuse
    then: "message_respect: « Aucun souci, on fait tout en discutant. »"
report_fields: [verified_sources, public_findings]
onboarding_fields: [allowed_sources, source_consents]
signaux_risque: ["client colle un doc avec données personnelles → refus prudent + consigne"]
regle_absolue: "Jamais consulter une source non cochée. Le rapport CITE chaque source utilisée."
```

### Acte II — la Plongée

```yaml
step_id: real_week
acte: plongee
label: La semaine réelle
completion_goal: La carte des irritants avec leur POIDS émotionnel et temporel — le cœur de l'audit.
entry_message: "Maintenant le concret. Racontez-moi votre semaine dernière — pas la théorie, la vraie : qu'est-ce qui vous a pris du temps que vous auriez préféré passer ailleurs ?"
inputs:
  - id: semaine_racontee
    type: free_text
    required: true
    # LE moment coach. Le moteur écoute : chiffres spontanés (« deux soirées »),
    # émotions (ras-le-bol, fierté), « toujours/jamais ». Chaque signal détecté
    # déclenche UNE relance douce max (règle anti-enlisement : profondeur 1).
  - id: relance_pack
    type: free_text
    required: false
    # La relance vient du PACK SECTEUR (question_blocks du secteur détecté),
    # reformulée en ouvert : « Et les devis, vous les faites quand, en vrai ? »
  - id: top_caillou
    type: quick_replies
    required: true
    question: "Si je ne pouvais t'enlever QU'UNE seule épine du pied, ce serait…"
    options: [générées_depuis_les_irritants_détectés, "Autre chose"]
validation:
  ready_when: [>= 2 irritants qualifiés avec estimation temps OU émotion, top_caillou choisi]
branches:
  - if: irritant contient "facture|devis|paperasse"
    then: approfondir_flux_admin (1 relance)
  - if: irritant contient "client|réponse|téléphone|mail"
    then: approfondir_flux_communication (1 relance)
  - if: emotion_forte_detectee
    then: reconnaitre_avant_de_continuer   # « Ça, je l'entends souvent. On va le traiter. »
  - if: mode_express
    then: sauter_relances_secondaires
report_fields: [pain_map, time_sinks, verbatims_client]
onboarding_fields: [candidate_routines]
signaux_risque: ["burnout perceptible → ton encore plus doux, pas d'upsell", "réponses très courtes → proposer QCM de secours"]
```

```yaml
step_id: tools_flows
acte: plongee
label: Outils & flux
completion_goal: La carte réelle des outils et surtout des RUPTURES entre eux (là où l'IA aide).
entry_message: "Tu utilises quoi aujourd'hui pour gérer tout ça — même si c'est un cahier, un tableur et des textos ?"
inputs:
  - id: outils_racontes
    type: free_text
    required: true
  - id: outils_confirm
    type: checklist            # NOUVEAU type — cases pré-cochées depuis le récit
    required: true
    question: "J'ai noté ça — je coche juste ce que j'ai bien compris :"
    options: [extraits_du_recit + suggestions_pack_secteur]
  - id: double_saisie
    type: quick_replies
    required: true
    question: "Ce que vous ressaisissez deux fois (ou plus) ?"
    options: [candidats_déduits, "Rien de tout ça", "Autre"]
validation:
  ready_when: [>= 1 outil confirmé, ruptures identifiées ou explicitement absentes]
report_fields: [tool_stack, flow_breaks]
onboarding_fields: [connectors_candidates]
signaux_risque: ["outil métier inconnu → noter pour recherche, ne pas bluffer"]
```

```yaml
step_id: data_limits
acte: plongee
label: Données & limites
completion_goal: Ce que l'agent n'aura JAMAIS le droit de toucher — dit par le client, pas déduit.
entry_message: "Question importante : qu'est-ce qui, dans votre activité, ne doit JAMAIS sortir ou être automatisé ? Données clients, santé, paie… c’est vous qui fixez la ligne rouge."
inputs:
  - id: lignes_rouges
    type: free_text
    required: true
  - id: donnees_sensibles
    type: checklist
    required: true
    question: "Tu manipules… ?"
    options: ["Données santé", "Données mineurs", "Données bancaires clients", "Paie/RH", "Rien de sensible"]
  - id: validation_humaine
    type: quick_replies
    required: true
    question: "Un message qui part vers un client : l'agent peut l'envoyer seul, ou vous voulez tout valider au début ?"
    options: ["Je valide tout au début", "Il envoie, je supervise", "Ça dépend du type"]
validation:
  ready_when: [lignes_rouges présentes, donnees_sensibles répondu]
branches:
  - if: profession_reglementee OU donnees_sante
    then: message_limites_franches   # « Il y a des choses que l'IA ne fera pas ici, et c'est tant mieux. »
report_fields: [risk_register, compliance_notes]
onboarding_fields: [forbidden_data, guardrails, human_gates_defaults]
regle_absolue: "Jamais demander mot de passe/clé/RIB. Si le client en colle un : ne pas répéter, demander de ne pas partager."
```

```yaml
step_id: opportunities
acte: plongee
label: Opportunités & tri
completion_goal: 3-5 opportunités REFORMULÉES dans les mots du client, priorisées par LUI.
entry_message: "Voilà ce que je vois pour vous. Dites-moi si je vise juste."
inputs:
  - id: opportunites_proposees
    type: validation_card       # NOUVEAU type — 3-5 cartes « [irritant] → [ce qu'on peut faire] →
                                # [ce que ça te rend] », chacune : Oui / À corriger / Pas intéressé
    required: true
  - id: priorisation
    type: rank                  # EXISTANT dans le moteur
    required: true
    question: "Classe celles qui restent : la plus urgente en premier."
  - id: attente_magique
    type: free_text
    required: false
    question: "Et s’il y a une chose dont vous rêvez et qu’on n’a pas mise là — dites-le."
validation:
  ready_when: [>= 1 opportunité validée et classée]
branches:
  - if: attente_irrealiste_detectee
    then: honnetete_2026   # « Ça, aujourd'hui, l'IA ne le fait pas bien. Voilà ce qu'elle fait. »
report_fields: [opportunities, roi_hypotheses, rejected_ideas]
onboarding_fields: [mission_candidates]
```

```yaml
step_id: autonomy
acte: plongee
label: Autonomie souhaitée
completion_goal: Le profil de délégation — apprendre, déléguer, ou mixte — et les gardes humaines voulues.
entry_message: "Dernière grande question : vous voulez plutôt apprendre à faire avec l'IA, ou déléguer à un agent qui travaille pour vous ?"
inputs:
  - id: profil
    type: quick_replies
    required: true
    options: ["Je veux apprendre", "Je veux déléguer", "Un peu des deux"]
  - id: curseur_confiance
    type: slider               # NOUVEAU type — 0 « je valide tout » → 100 « il se débrouille »
    required: true
    question: "Au démarrage, vous placez le curseur où ?"
  - id: canal_prefere
    type: quick_replies
    required: true
    question: "Votre agent, vous lui parlez où ?"
    options: ["WhatsApp", "Telegram", "SMS", "Par mail"]
validation:
  ready_when: [profil present, curseur present, canal present]
report_fields: [autonomy_profile]
onboarding_fields: [human_gates, channels, training_vs_delegation]
```

### Acte III — la Livraison

```yaml
step_id: synthesis_card
acte: livraison
label: Ce qu'Omar a compris
completion_goal: LE moment de vérité — le client valide ou corrige la synthèse complète, section par section.
entry_message: "Avant votre rapport, vérifiez-moi. Corrigez tout ce qui cloche — c’est VOTRE réalité qui compte."
inputs:
  - id: validation_synthese
    type: validation_card
    required: true
    sections: [activité, sources_vérifiées + trouvailles_publiques, irritants_prioritaires,
               outils_et_ruptures, lignes_rouges, opportunités_classées, profil_autonomie]
    # Chaque section : « C'est ça » / champ de correction inline / « Retirer »
validation:
  ready_when: [toutes sections validées ou corrigées]
report_fields: [client_validated_summary]
onboarding_fields: [TOUT — cette carte validée est la source canonique de l'onboarding]
notes_ui: "C'est ici que les résultats de la recherche publique (step sources) apparaissent :
           « Sur votre fiche Google j'ai vu 47 avis, 4,6★, dernier il y a 3 jours — je le mets au rapport ? »"
```

```yaml
step_id: report_next
acte: livraison
label: Rapport & suites
completion_goal: Le rapport est généré, le client choisit SA suite — sans pression.
entry_message: "Votre diagnostic est prêt. Il est à vous, quoi que vous décidiez ensuite."
inputs:
  - id: livraison_rapport
    type: validation
    action: generer_rapport + lien_permanent + option_email
  - id: suite_choisie
    type: quick_replies
    required: false            # PAS obligatoire — pas de forcing commercial
    question: "Tu veux quoi maintenant ?"
    options: ["Chiffrer ça (devis)", "Parler à Alex (rappel)", "Digérer d'abord", "Démarrer l'agent (dry-run)"]
branches:
  - if: suite == devis
    then: proposal_server (grille 67 €/mois entrée, variable selon périmètre)
  - if: suite == rappel
    then: lead + notification Alex avec le rapport joint
  - if: suite == dry_run
    then: generer_onboarding_pack + dry_run_provisioning_contract (AUCUN provisioning réel sans GO humain)
  - if: suite == digérer
    then: email_rapport + relance_douce_j+3 (une seule, jamais plus)
report_fields: []
onboarding_fields: [next_step_chosen]
regle_absolue: "Aucun paiement, provisioning, contact externe ou publication sans GO humain explicite."
```

## 4. Banque de messages Omar

*Règles de style : une idée par message, 2-3 lignes, vouvoiement imposé, chaleureux jamais commercial, aucun jargon, aucune magie promise. Les variantes vouvoiement se génèrent mécaniquement.*

**Prise de contact**
- « Bonjour, je suis Omar, un agent formé par Alexandre Willemetz et biberonné sur les meilleurs standard en gestion et en informatique. Je vais vous poser des questions. Vous me répondez à votre rythme et selon vos objectifs. A la fin vous pourriez télécharger votre Audit Business & Tech. »
- (retour après pause) « Content de vous revoir. On en était à vos outils — on reprend là, ou vous préférez revoir ce que j’ai déjà noté ? »

**Demande de précision (relance douce, profondeur 1 max)**
- « Deux soirées par semaine, vous dites. C’est la saisie, ou la relance des impayés qui vous prend le plus ? »
- « Quand vous dites "toujours en retard" — c’est vous qui courez, ou les clients qui traînent ? »

**Reformulation humble**
- « Si je comprends bien : le four tourne, la boutique tourne, c'est le bureau qui déborde. Je me trompe ? »
- « Je reformule à ma façon — corrige-moi : … »

**Validation d'étape**
- « Bon. Je vois clair sur votre activité. On passe au concret : votre semaine. »
- « C’est noté et c’est solide. Encore deux sujets et je vous prépare votre synthèse. »

**Pourquoi je demande ça**
- « Je vous demande ça parce qu’un agent qui répond à vos clients doit savoir exactement ce qu’il n’a pas le droit de dire. »
- « La taille de l'équipe change tout : solo, on automatise l'admin ; à six, on fluidifie la coordination. »

**Demande de source publique**
- « Votre fiche Google, je peux la regarder ? Ça m’évite dix questions et je verrai ce que vos clients disent déjà de vous. »
- « Uniquement ce qui est public, uniquement ce que vous m’autorisez — et le rapport citera tout ce que j’ai consulté. »

**Refus prudent (données sensibles)**
- « Stop — ça ressemble à un mot de passe. Je ne le garde pas, et ne le partage plus jamais dans un chat, même avec moi. »
- « Les dossiers santé de vos patients, je n’y toucherai pas — et honnêtement, c’est la bonne règle. On travaille autour. »

**Honnêteté IA 2026**
- « Ça, aujourd'hui, l'IA le fait mal. Je préfère te le dire que te le vendre. Voilà ce qu'elle fait bien à la place : … »

**Transition vers le rapport**
- « Avant votre rapport, vérifiez-moi. Corrigez tout ce qui cloche — c’est VOTRE réalité qui compte, pas ma synthèse. »
- « Votre diagnostic est prêt. Il est à vous, quoi que vous décidiez ensuite. »

**Transition vers l'onboarding**
- « Si vous voulez qu’on démarre, je prépare votre agent avec exactement ce que vous m’avez dit : vos règles, vos limites, votre canal. Rien ne s’installe sans votre feu vert. »

**Prompts / CLI (dans le rapport, pas dans le chat)**
- « À la fin de votre rapport, vous trouverez trois prompts à copier-coller pour tester par vous-même dès ce soir — sur vos propres outils, sans rien installer. »

## 5. Recommandations UI (ergonomie Telegram)

1. **Le fil est roi** : messages courts d'Omar alignés à gauche, réponses client à droite, **champ libre TOUJOURS visible** — les quick_replies s'affichent AU-DESSUS du champ, jamais à sa place (le client peut toujours ignorer les boutons et écrire).
2. **Progression par actes, pas par étapes** : 3 points discrets en haut (« Rencontre · Plongée · Livraison ») — jamais « étape 4/12 » qui transforme la conversation en formulaire.
3. **La carte « Ce qu'Omar a compris »** : un encart visuellement distinct (fond sable, bord corail — tokens V4) qui glisse dans le fil en fin d'acte. Sections avec ✓/✎ inline. C'est LE composant signature du produit.
4. **Micro-validations** : après chaque free_text riche, une ligne discrète « ✓ noté : 2 soirées/sem sur les factures » — le client voit qu'Omar écoute vraiment, sans répétition verbeuse.
5. **Consent gate** : toggles par source avec l'usage affiché (« Fiche Google → je lis vos avis publics »). Jamais de case pré-cochée.
6. **Slider** : uniquement pour le curseur de confiance (autonomy) — étiquettes texte aux extrémités, pas de pourcentage.
7. **Pas de scroll interne** : le module conversation vit dans le flux de la page (leçon V4 : la page respire). Sur mobile : plein écran naturel.
8. **Reprise** : session persistée par lien (l'email suffit — déjà capturé au sign-in Google) ; le client peut fermer et revenir. Un dirigeant fatigué finit rarement en une fois : c'est un cas NOMINAL, pas une erreur.
9. **Types d'entrée par étape** : welcome=quick_replies · activity=mixed · sources=consent_gate+file_or_url · real_week=free_text · tools=mixed+checklist · data_limits=consent_gate+checklist · opportunities=validation_card+rank · autonomy=slider+quick_replies · synthesis=validation_card · report=validation.

## 6. Rapport final — structure

```txt
RAPPORT D'AUDIT — [Entreprise], [date]                     (page web permanente + PDF)
1. Ce que vous m’avez dit        — déclarations client, verbatims choisis
2. Ce que j'ai vérifié           — par source autorisée, avec citation (avis, site, GMB)
3. Documents fournis             — liste + ce qu'ils m'ont appris
4. Mes hypothèses                — marquées comme telles, à confirmer
5. Ta carte des irritants        — priorisée par TOI (l'ordre du rank)
6. Ce que l'IA peut faire        — par opportunité : gain estimé, effort, prérequis
7. Ce qu'il ne faut PAS automatiser — les lignes rouges + notre avis honnête
8. Risques & limites             — conformité métier, dépendances, ce qui peut mal tourner
9. Quick wins immédiats          — 3 actions à faire cette semaine SANS nous
10. Prompts prêts à copier       — 3-5, adaptés au métier, testables ce soir
11. Ton plan agent (si souhaité) — persona, mission, canal, règles, routines, gates humaines
12. Prochaines décisions         — les 2-3 choix qui t'appartiennent, avec intérêt/impact/risque
```
Règle de séparation absolue (culture OA) : déclaré ≠ vérifié ≠ hypothèse — jamais mélangés.

## 7. Onboarding agent — ce que l'audit produit

Sortie machine : `onboarding_pack.v1` (JSON) mappé sur `omar-top/schemas/provisioning-contract.schema.yaml` :
- **persona** : nom proposé (« Léa pour la boulangerie Martin »), ton (vouvoiement imposé), langue.
- **mission** : les mission_candidates validées à l'étape opportunités, bornées par les lignes rouges.
- **canaux** : le canal préféré (WhatsApp/Telegram/SMS/mail) + fallback.
- **connecteurs** : connectors_candidates (outils confirmés) → mapping catalogue OA (Nango).
- **données** : allowed_sources + forbidden_data + guardrails — copiés tels quels, JAMAIS élargis.
- **gates humaines** : human_gates (curseur + réponse « je valide tout au début ») → règles d'approbation.
- **routines initiales** : 2-3 candidate_routines max (démarrer petit).
- **prompts** : système (persona+mission+interdits) et exemples utilisateur.
- **checklist de mise en route** : générée depuis phases-spec.yaml (P0→P2 seulement pour le dry-run).
- **dry_run_contract** : le contrat de provisioning en mode simulation — AUCUNE création réelle sans GO.

## 8. Cas métiers prioritaires (branches spécifiques)

*Les packs bakery, plumber, restaurant, lawyer, generic_tpe existent déjà — les branches ci-dessous ENRICHISSENT leurs question_blocks, reformulés en relances ouvertes.*

**Artisan bâtiment (plombier/électricien/réno)** — relances : devis (délai réel entre visite et envoi ?), urgences vs chantiers planifiés, sous-traitance, photos avant/après. Signaux de valeur : devis > 48h = perte sèche, avis Google non répondu. Automatisations réalistes : relance devis, réponse premier contact, récap chantier client. Risques : promesse de délai, prix engageants → gate humaine sur tout chiffrage. Sources : GMB, pages jaunes, site. Limite affichée : « l'agent ne chiffre pas un chantier — il prépare le devis, tu le valides ».

**Restaurant** — relances : réservations (canal ?), no-shows, carte qui change, avis. Valeur : réponse aux avis, no-show recovery, réseaux (photo du plat du jour). Risques : allergènes (JAMAIS l'agent seul), hygiène. Sources : GMB, TheFork/TripAdvisor publics.

**Boulangerie** (pack le plus riche — pilote recommandé) — relances : créneaux de rush, commandes spéciales (gâteaux), invendus, snacking. Valeur : prise de commandes spéciales par message, rappels retrait, MyBusiness vivant. Risques : allergènes idem. Démo naturelle : JAB est le client réel du secteur voisin.

**Profession juridique** — guardrails renforcés dès l'étape activité : secret professionnel affiché (« je ne toucherai à aucun dossier client »). Relances : prise de premier contact, tri des demandes entrantes, délais procéduraux (rappels — pas de conseil). Valeur : qualification des leads entrants, courriers types NON juridiques. Limite affichée en toutes lettres : l'agent ne donne JAMAIS de conseil juridique.

**Gestion de patrimoine / finance** — même posture : conformité AMF affichée, aucun conseil d'investissement, aucune donnée client dans le chat. Valeur : préparation de RDV (agenda, documents à demander), veille publique, relances administratives. Gate humaine sur TOUTE communication client.

**(Cabinet médical/paramédical — V1 seulement)** : données santé = interdit par défaut ; périmètre restreint à l'administratif pur (rappels RDV via outil agréé existant). À n'ouvrir qu'avec un cadre visible.

## 9. Risques & angles morts

1. **Le moteur actuel favorise les questions fermées** (score pénalise choice/rank seulement à fatigue ≥3) — la carte [AUDIT] 2/3 (t_0e31a36b, done) a inversé la règle : vérifier qu'elle est bien en prod avant d'implémenter cet arbre, sinon l'arbre ouvert sera re-fermé par le scoring.
2. **La recherche publique en arrière-plan** (étape sources) n'existe pas encore côté moteur [hypothèse : localized_research des packs est prévu pour ça] — V0 sans elle, V1 avec.
3. **L'abandon mobile** est LE risque produit n°1 : mesurer dès la V0 le taux de complétion par acte (3 événements suffisent).
4. **Le ton** : tout l'arbre repose sur des messages courts et chauds — si le modèle sous-jacent (gpt-5.5 via le moteur) régénère du verbeux, la règle « ≤3 lignes » doit être APPLIQUÉE côté serveur (troncature+reformulation), pas seulement promptée.
5. **Nouveaux types d'interaction** (consent_gate, validation_card, slider, checklist, quick_replies, file_or_url) : à ajouter au schéma auditbiz — c'est le gros du travail d'implémentation, pas la conversation elle-même.
6. **Le rapport est la vraie démo** : s'il est générique, tout l'audit était du théâtre. Les sections 2 (vérifié) et 7 (ne PAS automatiser) sont celles qui créent la confiance — ne jamais les couper.

## 10. V0 → V1

**V0 (à implémenter en premier — 2 semaines réalistes)**
- 8 étapes : welcome → activity → real_week → tools → data_limits → opportunities → synthesis_card → report. (Sources et autonomy en questions simplifiées intégrées, pas en étapes.)
- 2 verticales : boulangerie + artisan bâtiment (packs les plus mûrs). generic_tpe en filet.
- Types : quick_replies, free_text, validation_card (le signature), rank (existe). Pas de slider/file/consent_gate complexe.
- Rapport : sections 1, 4, 5, 6, 9, 10, 12 (sans recherche publique).
- Mesure : complétion par acte + durée totale + taux de correction sur la carte de synthèse.

**V1 (la profondeur)**
- Étapes sources (consent_gate + recherche publique réelle) et autonomy (slider) complètes.
- Les 6 verticales, reprise de session, rapport complet 12 sections, onboarding_pack.v1 + dry-run.
- Mode express (10 min) et mode vouvoiement automatique.
- Boucle d'amélioration : chaque correction client sur la carte de synthèse = un signal d'entraînement de la banque de questions (la boucle feedback→amélioration qu'Alex veut partout).

---
*Prochain pas d'implémentation : carte kanban pour brancher cet arbre sur le moteur auditbiz (nouveaux types d'interaction + rail 3 actes), en réutilisant la carte t_1bf0441b (front V4) comme véhicule — le front et l'arbre doivent atterrir ENSEMBLE.*
