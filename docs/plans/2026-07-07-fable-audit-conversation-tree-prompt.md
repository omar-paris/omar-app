# Prompt Fable — Arbre conversationnel initial Audit Omar & Alex

## Contexte

Tu es Fable, designer produit/conversationnel pour Omar & Alex.

Nous construisons l’audit public d’Omar & Alex : un audit IA autoportant qu’un dirigeant de TPE/PME peut réaliser seul, sans rendez-vous initial, dans une interface conversationnelle aussi fluide qu’un fil Telegram/WhatsApp.

Objectif business : permettre au prospect de comprendre concrètement où l’IA peut l’aider, quelles limites/risques existent, quelles preuves ou sources sont nécessaires, puis générer un rapport exploitable qui mène vers une proposition, un devis, un onboarding agent et un dry-run de mise en place.

Le client ne doit pas sentir un formulaire administratif. Il doit sentir qu’Omar discute, comprend, reformule, vérifie, puis produit un vrai livrable.

## Contraintes produit non négociables

1. L’audit doit être **autoportant** : le client doit pouvoir aller au bout seul.
2. L’interface doit être **ergonomique comme Telegram** : messages courts, actions contextuelles, saisie libre toujours disponible.
3. Les messages d’Omar doivent être **simples, directs, premium**, jamais verbeux.
4. Une réponse Omar = **un paragraphe maximum**, idéalement 2–3 lignes, sauf résumé/rapport.
5. Certaines questions doivent être en **QCM/boutons rapides**.
6. Certaines questions doivent être en **champ libre** quand il faut de la nuance.
7. Certaines étapes doivent utiliser une **barre de remplissage/progression** ou des micro-validations, pas uniquement du texte.
8. L’audit doit produire de la **profondeur métier**, pas un questionnaire générique.
9. Omar doit adapter ses questions selon le métier, la taille, les outils, le niveau IA, les contraintes, les réponses précédentes et les sources autorisées.
10. L’audit ne doit jamais déclencher de paiement, provisioning, contact externe, publication ou action sensible sans GO humain explicite.

## Livrables attendus de Fable

Produis un arbre conversationnel initial complet, structuré et actionnable, pas une simple liste d’idées.

### 1. Architecture générale de l’audit

Définis les grandes étapes et sous-étapes nécessaires pour atteindre un audit complet.

Base possible, à améliorer si besoin :

1. Préférences de conversation
2. Identification activité / entreprise
3. Sources autorisées et preuves publiques
4. Problèmes et blocages opérationnels
5. Outils actuels et flux de travail
6. Données sensibles, risques, limites, conformité
7. Opportunités IA concrètes
8. Priorisation / ROI / faisabilité
9. Autonomie souhaitée : apprendre, déléguer, mixte
10. Rapport final + propositions de solutions
11. Préparation onboarding agent
12. Commandes CLI / prompts / premières actions de test

Pour chaque étape, donne :

- objectif de l’étape ;
- informations à collecter ;
- critères de complétion ;
- type d’interaction recommandé : QCM, boutons, saisie libre, slider, checklist, validation, upload/document, recherche publique autorisée ;
- exemples de messages Omar courts ;
- branches conditionnelles selon réponses ;
- signaux de risque / blocage ;
- données qui iront dans le rapport ;
- données qui iront dans l’onboarding agent.

### 2. Arbre conversationnel détaillé

Pour chaque étape, fournis un arbre sous cette forme :

```yaml
step_id: activity
label: Activité
completion_goal: Comprendre qui est l’entreprise et son contexte réel.
entry_message: "Dites-moi simplement votre métier, votre ville et la taille de l’équipe. Je m’occupe de structurer ensuite."
inputs:
  - id: business_activity
    type: free_text
    required: true
    question: "Vous faites quoi, concrètement ?"
  - id: company_size
    type: quick_replies
    required: true
    options: ["Solo", "2–5", "6–20", "20+"]
  - id: location
    type: free_text
    required: true
    question: "Vous intervenez où ?"
validation:
  ready_when:
    - business_activity present
    - company_size present
    - location present
branches:
  - if: regulated_profession
    then: activate_regulated_guardrails
  - if: local_business
    then: ask_public_presence_sources
report_fields:
  - company_context
  - sector_hypothesis
onboarding_fields:
  - business_type
  - location
  - team_size
```

### 3. Messages Omar prêts à l’emploi

Écris une banque de messages courts, utilisables directement dans le produit.

Style :

- tutoiement par défaut, mais adaptable au vouvoiement ;
- direct ;
- chaleureux mais pas commercial ;
- une idée par message ;
- pas de jargon IA inutile ;
- pas de promesse magique ;
- toujours orienté vers la prochaine réponse utile.

Exemples de types de messages à fournir :

- première prise de contact ;
- demande de précision ;
- reformulation humble ;
- validation d’étape ;
- proposition de QCM ;
- explication “pourquoi je demande ça” ;
- demande de source publique ;
- refus prudent si données sensibles ;
- transition vers rapport ;
- transition vers onboarding agent ;
- génération de prompts / CLI.

### 4. Ergonomie type Telegram

Propose comment l’UI doit fonctionner concrètement :

- message court Omar ;
- boutons rapides sous certains messages ;
- champ libre toujours visible ;
- validation par puces simples : “Oui”, “À corriger”, “Passer”, “Je ne sais pas” ;
- barre de progression discrète ;
- indicateur “ce qu’Omar a compris” ;
- résumé éditable avant rapport ;
- pas de scroll interne parasite dans le module conversation : la page doit respirer naturellement.

Précise pour chaque étape si l’entrée idéale est :

```txt
quick_replies | free_text | mixed | checklist | slider | file_or_url | consent_gate | validation_card
```

### 5. Rapport final attendu

Définis la structure du rapport final généré par Omar.

Le rapport doit séparer clairement :

- déclarations du client ;
- sources publiques vérifiées ;
- documents fournis ;
- hypothèses Omar ;
- risques et limites ;
- recommandations ;
- quick wins ;
- ce qu’il ne faut pas automatiser ;
- prompts prêts à copier ;
- commandes CLI ou procédures locales ;
- plan onboarding agent ;
- prochaines décisions humaines.

### 6. Onboarding agent

Définis ce que l’audit doit produire pour initialiser un agent Omar & Alex :

- nom/persona de l’agent ;
- mission ;
- canaux ;
- outils/connecteurs ;
- données autorisées/interdites ;
- validations humaines obligatoires ;
- premières routines ;
- prompts système et prompts utilisateur ;
- checklist de mise en route ;
- dry-run provisioning contract ;
- commandes CLI utiles quand pertinent.

### 7. Cas métiers prioritaires

Propose au moins 5 verticales initiales avec branches spécifiques :

- artisan bâtiment : plombier/électricien/rénovation ;
- restaurant ;
- boulangerie ;
- profession juridique ;
- gestion de patrimoine/finance ;
- cabinet médical/paramédical si utile, avec prudence.

Pour chaque verticale :

- questions spécifiques ;
- signaux de valeur ;
- risques ;
- premières automatisations réalistes ;
- exemples de prompts ;
- sources publiques utiles ;
- limites à afficher.

### 8. Format de sortie demandé

Réponds avec :

1. une synthèse courte ;
2. un tableau étapes × type interaction × données collectées × sortie rapport/onboarding ;
3. un arbre YAML complet ;
4. une banque de messages Omar ;
5. recommandations UI ;
6. risques / angles morts ;
7. version V0 à implémenter en premier et version V1 plus profonde.

## Niveau d’exigence

Ne propose pas un chatbot superficiel. L’objectif est de remplacer un premier rendez-vous de découverte très qualitatif, pas de remplir un formulaire.

L’audit doit être assez profond pour que le rapport final donne envie de dire :

> “Ils ont compris mon activité et ils savent quoi faire concrètement.”

Mais il doit rester assez simple pour qu’un dirigeant fatigué puisse aller au bout sur mobile.
