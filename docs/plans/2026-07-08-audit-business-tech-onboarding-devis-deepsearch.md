# AppOmar — Audit Business & Tech → onboarding → devis — cadrage Deep Search

> **For Hermes:** transformer ce cadrage en arbre YAML audit + contrats API + plan d’implémentation. Ne pas sauter vers le devis avant que le rapport/propositions soient justifiés.

**Date:** 2026-07-08
**Contexte:** feedback Alex après hotfix audit conversation_policy V2.
**Objectif:** AppOmar doit devenir un tunnel cohérent : audit business & technologique profond → enrichissement public consenti → rapport diagnostic → propositions justifiées → onboarding agent → devis/validation → dry-run provisioning.

---

## 1. Correction/reformulation du besoin Alex

Nous voulons construire dans `app.omar.paris` un véritable **audit Business & Tech conversationnel**, pas un formulaire ni un simple configurateur.

L’audit doit permettre de comprendre profondément :

- l’entreprise : identité, activité, secteur, localisation, taille, ancienneté, modèle économique, clients, concurrents, contraintes ;
- la personne : rôle, niveau de charge, attentes, objectifs, tolérance à l’autonomie, niveau numérique/IA ;
- la situation business : forces, faiblesses, opportunités, menaces, offre, marge, canaux de vente, marketing, achats, RH, organisation ;
- la situation technologique : outils, données, sécurité, emails, agenda, fichiers, CRM/facturation, site, Google Business, réseaux publics, automatisations possibles ;
- les irritants concrets : temps perdu, erreurs, tâches répétitives, moments critiques, risques ;
- les limites : ce qu’il ne faut pas automatiser, données sensibles, validation humaine, obligations métier ;
- les premières solutions : quick wins, agent IA, connecteurs, accompagnement, procédures, devis éventuel.

L’expérience doit être une conversation premium : Omar pose des questions personnalisées et profondes, interprète les réponses dans le contexte, propose des exemples si le client bloque, valide les faits un par un, et creuse selon le secteur.

Au début de l’audit, Omar doit aussi demander les éléments permettant une recherche publique consentie : nom public de l’entreprise, adresse, site, fiche Google, SIRET/SIRENE si connu. Avec consentement explicite, Omar doit pouvoir récupérer ou préparer la récupération d’informations publiques : SIRET, activité déclarée, adresse, avis, horaires, site, concurrents locaux, présence digitale. Ces informations doivent ensuite être présentées au client pour validation : `Oui c’est exact`, `À modifier`, `Ce n’est pas moi`, `Ignorer cette source`.

Le rapport final doit séparer clairement :

1. déclarations du client ;
2. sources publiques vérifiées ;
3. documents fournis ;
4. hypothèses Omar ;
5. diagnostic Business & Tech ;
6. SWOT ou diagnostic équivalent ;
7. plan d’action priorisé ;
8. propositions de solutions justifiées ;
9. limites et décisions humaines à prendre ;
10. éléments utiles pour onboarding et devis.

L’onboarding et le devis doivent être reconnectés à l’audit : ils ne doivent pas redemander bêtement ce que l’audit a déjà compris. L’onboarding doit transformer le rapport en `agent_profile`, périmètre, canaux, connecteurs, règles de sécurité, limites, procédures initiales. Le devis doit être une conséquence argumentée du diagnostic, pas une sélection libre déconnectée.

---

## 2. État réel vérifié le 2026-07-08

### Audit

- `/audit/` public : `GET 200`.
- API `/api/audit-sessions` opérationnelle.
- Hotfix PR #60 déployé : `conversation_policy V2`.
- Recherche publique consentie existe côté API :
  - `/api/audit-sessions/{id}/research-plan` → `200`, plan source + consent_snapshot.
  - `/api/audit-sessions/{id}/public-research` → `200`, support dry-run et connecteurs bornés.
- Rapport depuis session : `/api/audit-sessions/{id}/report` → `201`, produit `report`, `onboarding_pack`, `devis_source`.
- Limite actuelle majeure : rapport encore trop générique et parfois mal mappé entre transcript et champs structurés.

### Onboarding

- `/onboarding/` public : `GET 200`.
- API `/api/onboarding` opérationnelle si payload correct `{record, agent_profile, completed_sections, current_step}`.
- API `/api/onboarding/{id}/simulate` → `200`, produit dry-run preview, `paid_actions=none`.
- Limites : UX formulaire, pas encore réellement conversationnelle ; pas assez reconnectée automatiquement au rapport d’audit ; champs encore trop pauvres pour agent réel.

### Devis

- API `/api/catalog` opérationnelle.
- API `/api/devis` opérationnelle avec vrais IDs catalogue.
- API `/api/devis` depuis `audit_id` opérationnelle : utilise `devis_source`.
- Checkout bloque correctement si devis non validé : `409 devis_not_validated`.
- Stripe non configuré attendu ensuite : blocker paiement propre, pas un faux succès.
- Limite critique live : `/devis/` page retourne `302` OAuth ; donc pas encore public prospect côté UI.

### Conclusion readiness

Le tunnel n’est **pas prêt pour prospection**.

Il est partiellement fonctionnel techniquement : audit public, onboarding API/draft, devis API existent. Mais il manque le produit cohérent : arbre audit profond, rapport solide, source validation UX, onboarding dérivé de l’audit, devis public/justifié, et gate A→Z.

---

## 3. Architecture cible

```txt
Landing / promesse
  ↓
Audit conversationnel Business & Tech
  ↓
Collecte identité publique + consentements source par source
  ↓
Research plan : ce qu’Omar propose d’aller vérifier
  ↓
Public research bornée : site, SIRENE/SIRET, fiche Google/manual, annuaires, concurrents
  ↓
Micro-validation des faits trouvés
  ↓
Diagnostic : Business, Tech, SWOT, risques, opportunités, quick wins
  ↓
Rapport + propositions de solutions justifiées
  ↓
Onboarding prérempli : agent_profile, règles, canaux, connecteurs, limites, procédures
  ↓
Devis recommandé : items catalogue + justification + validation client
  ↓
Dry-run provisioning : paid_actions=none, human_go_required=true
```

---

## 4. Arbre YAML cible — sections minimales

```yaml
audit_tree:
  version: audit_business_tech.v1
  principles:
    - conversation_premium_not_form
    - declarations_sources_hypotheses_separated
    - consent_before_public_research
    - no_devis_before_diagnostic
    - onboarding_and_devis_derive_from_audit

  stages:
    - id: pacte
      goal: expliquer l'audit et obtenir accord

    - id: identity_public_context
      goal: identifier entreprise/personne et préparer recherche consentie
      fields:
        - person_name
        - role
        - company_public_name
        - legal_name_optional
        - address_or_zone
        - website_optional
        - siret_sirene_optional
        - google_business_optional
      outputs:
        - research_candidate

    - id: public_sources_consent
      goal: demander consentement source par source
      sources:
        - public_web_search
        - legal_registry_lookup
        - google_business_manual
        - public_reviews
        - public_socials
        - supplied_documents
      buttons:
        - Autoriser cette source
        - Refuser cette source
        - Je ne sais pas
        - On verra plus tard

    - id: activity_business_model
      goal: comprendre activité et modèle économique
      facets:
        - métier exact
        - offre principale
        - clients
        - panier moyen ou ordre de CA si accepté
        - saisonnalité
        - canaux vente
        - localisation
        - concurrents perçus

    - id: person_and_goals
      goal: comprendre la personne, ses attentes et sa charge mentale

    - id: operations_week
      goal: reconstruire une vraie semaine de travail

    - id: marketing_sales
      goal: comprendre acquisition, fidélisation, avis, relances, visibilité

    - id: admin_finance_purchasing
      goal: comprendre devis, factures, achats, fournisseurs, trésorerie

    - id: hr_team_organization
      goal: comprendre équipe, rôles, délégation, procédures

    - id: digital_tools_data
      goal: inventorier outils, données, sécurité, connecteurs

    - id: risks_limits
      goal: définir les lignes rouges et validations humaines

    - id: diagnosis
      goal: produire diagnostic Business & Tech + SWOT
      outputs:
        - strengths
        - weaknesses
        - opportunities
        - threats
        - risk_map
        - automation_candidates
        - do_not_automate

    - id: recommendations
      goal: prioriser solutions OA
      outputs:
        - quick_wins_7_days
        - plan_30_days
        - agent_profile_draft
        - connector_plan
        - devis_source

    - id: validation
      goal: faire valider faits, hypothèses, recommandations avant devis/onboarding
```

---

## 5. Prompt Google Deep Search

```text
Je veux concevoir pour Omar & Alex un audit conversationnel Business & Tech destiné aux TPE/PME, artisans, commerçants et professions libérales en France.

Contexte produit :
- L’audit se déroule dans une application web conversationnelle : app.omar.paris.
- Le client discute avec “Omar”, un agent IA formé par Alexandre Willemetz.
- L’objectif n’est pas seulement de vendre un devis : l’objectif est de comprendre profondément l’entreprise, produire un diagnostic utile, puis proposer des solutions IA/tech concrètes et prudentes.
- Le tunnel cible est : audit conversationnel → enrichissement public consenti → rapport diagnostic → propositions de solutions justifiées → onboarding agent → devis → dry-run provisioning.
- Public cible : TPE/PME françaises, artisans, commerçants, professions libérales, dirigeants non techniques.
- Contraintes : RGPD, consentement explicite avant recherche publique ou analyse documentaire, séparation entre déclarations client / sources vérifiées / hypothèses IA, aucune action payante ou provisioning sans validation humaine.

Je veux une recherche approfondie pour répondre à ces questions :

1. Quelles sont les meilleures pratiques 2025-2026 pour réaliser un audit Business & Tech complet pour une TPE/PME ?
2. Quelles grandes dimensions faut-il couvrir pour obtenir un diagnostic utile ? Par exemple : business model, clients, marketing, ventes, opérations, achats, RH, finance, outils numériques, données, sécurité, automatisation, IA, conformité, expérience client.
3. Comment structurer les questions pour qu’elles soient à la fois générales et capables de s’approfondir selon le secteur ?
4. Comment adapter les questions selon des signaux simples : solo vs équipe, activité locale vs à distance, B2B vs B2C, ancienneté, niveau de maturité digitale, outils déjà utilisés ?
5. Quelles méthodes de diagnostic recommander : SWOT, PESTEL léger, chaîne de valeur, customer journey, maturity model, risk matrix, automation opportunity matrix, ICE/RICE scoring, effort/impact matrix ? Lesquelles sont réalistes pour une TPE ?
6. Comment intégrer une étape de recherche publique consentie : nom entreprise, adresse, site web, SIRET/SIRENE, fiche Google Business, avis publics, réseaux sociaux publics, annuaires, concurrents locaux ? Quelles sources françaises sont fiables et légalement utilisables ?
7. Comment présenter au client les informations trouvées pour validation une par une ? Quels boutons / micro-validations utiliser ?
8. Comment transformer les résultats de l’audit en recommandations concrètes : quick wins 7 jours, plan 30 jours, procédures, prompts, agent IA, connecteurs, automatisations prudentes ?
9. Comment transformer les résultats en onboarding agent : agent_profile, mission, ton, canaux, connecteurs, limites, validations humaines, accès nécessaires, données interdites ?
10. Comment transformer les résultats en devis justifié : ligne de devis, raison, preuve issue de l’audit, confiance, limites, prérequis ?
11. Quelles questions faut-il absolument éviter pour ne pas fatiguer le client ou créer un effet formulaire ? Comment maintenir une expérience de conversation premium ?
12. Quels exemples d’audits ou frameworks comparables existent : digital maturity assessment, AI readiness assessment, SMB technology audit, operational excellence diagnostic, CRM/marketing audit, cybersecurity basics for SMBs ?
13. Quelles différences faut-il prévoir pour les premiers secteurs : boulangerie/pâtisserie, restaurant, avocat, gestion de patrimoine, artisan BTP, consultant/freelance ?
14. Quels livrables finaux produire dans le rapport : résumé exécutif, faits déclarés, sources vérifiées, hypothèses, SWOT, risques, opportunités, plan d’action, recommandations IA, limites, prochain rendez-vous, éléments onboarding, devis source ?
15. Quelles métriques ou signaux simples peuvent aider à scorer la maturité business/tech sans demander trop de chiffres sensibles ?

Je veux une réponse structurée avec :
- une architecture complète de l’audit ;
- une liste de sections et sous-sections ;
- une banque de questions conversationnelles ;
- des règles de branchement selon les réponses ;
- des exemples de micro-validations ;
- une structure YAML possible pour piloter l’arbre de conversation ;
- un modèle de rapport final ;
- un modèle d’onboarding agent ;
- un modèle de devis justifié ;
- les sources/références utilisées.

Important : proposer une solution adaptée aux petites entreprises françaises, pas un audit de grande entreprise trop lourd. Le ton doit être pragmatique, actionnable, et orienté mise en œuvre dans une application web conversationnelle.
```

---

## 6. Décisions CTO proposées

1. Ne pas refaire seulement `/audit/` : refaire le triptyque `audit → onboarding → devis` comme un seul produit.
2. Garder les endpoints existants, mais enrichir les contrats : ne pas casser ce qui marche.
3. Créer un fichier source YAML versionné pour l’arbre audit.
4. Ajouter un moteur `next_best_question` déterministe : tree + state + policy + sector pack.
5. Brancher les recherches publiques après consentement, avec sources séparées et micro-validation.
6. Faire du devis un artefact dérivé : `devis_source.recommended_items[]` avec `reason`, `evidence`, `confidence`, `limits`.
7. Faire de l’onboarding un artefact dérivé : `agent_profile`, `connector_plan`, `human_validation_rules`, `first_procedures`.
8. Gater avant prospection : smoke complet sans login sur audit/onboarding/devis public ou route post-audit accessible.

---

## 7. Première backlog technique

- [ ] Public route : décider si `/devis/` doit être public post-audit ou protégé ; aujourd’hui OAuth 302.
- [ ] Introduire `audit_tree.business_tech.v1.yaml`.
- [ ] Étendre `audit_intelligence.py` pour stages business/tech profonds.
- [ ] Corriger le mapping report : ne plus confondre activité, irritants, outils.
- [ ] Ajouter UX `Sources / compléments autorisés` dans `/audit/`.
- [ ] Ajouter micro-validation source : `Oui c’est exact`, `À modifier`, `Ce n’est pas moi`, `Ignorer`.
- [ ] Préremplir onboarding depuis `onboarding_pack` audit.
- [ ] Préremplir devis depuis `devis_source` audit côté UI.
- [ ] Tests A→Z : audit → research-plan → public-research dry-run → report → devis from audit → onboarding from audit → simulation.
- [ ] Gate Athena avant merge/release.
