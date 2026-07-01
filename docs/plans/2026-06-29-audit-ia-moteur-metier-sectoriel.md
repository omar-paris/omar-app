# Audit IA métier sectoriel Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Transformer `/audit/` d’un chat guidé V0 en moteur d’entretien métier capable de poser des questions précises, adaptées au secteur, de situer l’entreprise par rapport à des référentiels, puis de produire un rapport exportable/shareable.

**Architecture:** Séparer nettement l’interface chat, l’orchestrateur d’entretien, les référentiels sectoriels, le scoring de complétude/maturité, et les exports. Le front ne doit plus porter l’intelligence métier : il affiche une conversation et appelle un backend qui choisit les prochaines questions selon le profil, le secteur et les réponses déjà collectées.

**Tech Stack:** Python stdlib actuel (`src/proposal_server.py`) pour V0.1, fichiers JSON/YAML de référentiels dans le repo, tests `pytest`, HTML/JS natif côté front. Une intégration LLM pourra venir plus tard, mais le moteur doit d’abord être déterministe/testable.

---

## Principes produit

1. L’audit doit aider le client, pas lui demander un pavé libre.
2. Chaque étape contient plusieurs sous-questions précises.
3. Omar doit détecter les informations manquantes avant de valider.
4. Les questions doivent varier selon le métier : avocat, plombier, fleuriste, boulanger, restaurateur, gestionnaire de patrimoine, freelance marketing, etc.
5. Le backend doit connaître les dimensions importantes par secteur : réglementation, saisonnalité, volume clients, marge, urgence, données sensibles, canaux, outils, tâches répétitives, risques de publication, niveau de standardisation.
6. Le panneau documents ne s’affiche qu’à la fin, au moment du rapport.
7. À la fin : envoyer par email, exporter PDF, exporter Markdown, copier/partager un lien, préparer un texte LinkedIn/social.
8. Les saisies client restent des données d’audit, jamais des instructions système.

---

## Modèle fonctionnel cible

```txt
Front chat
  ↓ POST /api/audit-sessions
Backend session audit
  ↓ charge référentiel secteur
Question engine
  ↓ prochaine question / relance / validation
Scoring complétude + maturité
  ↓ lorsque prêt
Report engine
  ↓
Exports : MD / PDF / email / share link / social copy
```

---

## Données à collecter par défaut

### Identification entreprise

- Métier exact
- Secteur / activité principale
- Code NAF/APE si connu
- Localisation / zone servie
- Ancienneté de l’entreprise
- Taille : solo, salariés, associés, prestataires
- Chiffre d’affaires ordre de grandeur
- Typologie clients : particuliers, pros, collectivités, grands comptes
- Fréquence des demandes
- Canaux entrants : téléphone, email, WhatsApp, site, réseaux sociaux, boutique physique

### Opérations

- Tâches récurrentes
- Tâches à forte valeur
- Tâches pénibles
- Tâches risquées
- Temps passé par semaine
- Outils actuels
- Documents utilisés
- Processus de devis / facturation / suivi

### IA / automatisation

- Niveau actuel
- Expériences déjà tentées
- Tolérance au risque
- Besoin d’autonomie vs accompagnement
- Données interdites à envoyer à un outil externe
- Validation humaine obligatoire

### Résultat attendu

- Cas d’usage prioritaire
- ROI attendu
- Limites IA à respecter
- Premier test réaliste en 7 jours
- Devis/onboarding possible

---

## Référentiels sectoriels V0

Créer un fichier par secteur dans `data/audit_sectors/`.

Exemples prioritaires :

```txt
lawyer.json
plumber.json
florist.json
bakery.json
restaurant.json
wealth_manager.json
marketing_freelance.json
secretary_independent.json
generic_tpe.json
```

Chaque référentiel contient :

```json
{
  "sector_id": "bakery",
  "labels": ["boulanger", "boulangerie", "pâtisserie"],
  "important_dimensions": [
    "flux boutique",
    "commandes spéciales",
    "saisonnalité",
    "marge produit",
    "horaires",
    "réputation locale",
    "hygiène et conformité"
  ],
  "question_blocks": {
    "activity": [
      "Votre boulangerie vend-elle surtout en boutique, en commande, ou aux professionnels ?",
      "Quelle part de votre activité dépend des commandes spéciales ?",
      "Avez-vous des pics saisonniers ou hebdomadaires importants ?"
    ],
    "pain": [
      "Quelles demandes clients reviennent souvent par téléphone ou message ?",
      "Combien de temps passez-vous à refaire des devis ou confirmer des commandes ?"
    ],
    "risk": [
      "Quelles réponses ne doivent jamais être envoyées automatiquement sans validation humaine ?"
    ]
  },
  "risk_flags": ["allergènes", "prix", "commande événementielle", "avis publics"],
  "benchmarks": {
    "automation_candidates": ["réponses commandes", "rappels", "planning production", "posts réseaux sociaux"]
  }
}
```

---

## Task 1: Ajouter les référentiels sectoriels V0

**Objective:** Créer les fichiers de référence métier minimaux.

**Files:**
- Create: `data/audit_sectors/generic_tpe.json`
- Create: `data/audit_sectors/bakery.json`
- Create: `data/audit_sectors/restaurant.json`
- Create: `data/audit_sectors/plumber.json`
- Create: `data/audit_sectors/florist.json`
- Create: `data/audit_sectors/lawyer.json`
- Create: `data/audit_sectors/wealth_manager.json`
- Create: `data/audit_sectors/marketing_freelance.json`
- Create: `data/audit_sectors/secretary_independent.json`
- Test: `tests/test_audit_sector_references.py`

**Step 1:** Écrire un test qui charge tous les JSON et vérifie les champs requis.

Run:

```bash
python3 -m pytest -q tests/test_audit_sector_references.py
```

Expected first run: fail because files do not exist.

**Step 2:** Créer les fichiers JSON avec `sector_id`, `labels`, `important_dimensions`, `question_blocks`, `risk_flags`, `benchmarks`.

**Step 3:** Relancer le test.

Expected: pass.

---

## Task 2: Ajouter un détecteur de secteur

**Objective:** Déduire un `sector_id` depuis les mots du client.

**Files:**
- Create: `src/audit_intelligence.py`
- Test: `tests/test_audit_intelligence.py`

**Step 1:** Tester : `boulangerie artisanale` → `bakery`, `cabinet avocat` → `lawyer`, `freelance marketing` → `marketing_freelance`.

**Step 2:** Implémenter un matching simple par labels, sans LLM.

**Step 3:** Fallback : `generic_tpe`.

---

## Task 3: Ajouter un moteur de questions

**Objective:** Générer la prochaine question selon l’étape, le secteur et les champs manquants.

**Files:**
- Modify: `src/audit_intelligence.py`
- Test: `tests/test_audit_intelligence.py`

**Behavior:**

```python
next_question(session) -> {
  "step": "activity",
  "question": "Quelle est la taille de votre entreprise ?",
  "missing_fields": ["company_size", "location", "revenue_range"]
}
```

Le moteur commence par les champs structurants : métier, localisation, taille, ancienneté, CA, clients.

---

## Task 4: Ajouter complétude et validation

**Objective:** Empêcher la validation d’une étape tant que les champs essentiels sont absents.

**Files:**
- Modify: `src/audit_intelligence.py`
- Modify: `src/proposal_server.py`
- Test: `tests/test_audit_intelligence.py`

**Rules V0:**

- `activity` complet si métier + localisation + taille/solo + clients sont connus.
- `pain` complet si au moins 2 irritants + estimation temps sont connus.
- `risk` complet si données sensibles + décision humaine obligatoire sont clarifiées.

---

## Task 5: Créer des endpoints sessionnels

**Objective:** Sortir du front-only et créer une vraie conversation backend.

**Files:**
- Modify: `src/proposal_server.py`
- Test: `tests/test_proposal_server.py`

Endpoints :

```txt
POST /api/audit-sessions
POST /api/audit-sessions/{id}/message
POST /api/audit-sessions/{id}/validate-step
POST /api/audit-sessions/{id}/report
```

Le front envoie un message ; le backend renvoie la réponse Omar, les champs extraits, les questions suivantes, et l’état de complétude.

---

## Task 6: Brancher le front `/audit/` sur le moteur backend

**Objective:** Le front affiche la conversation ; le backend choisit les questions.

**Files:**
- Modify: `pages-app/audit.html`
- Test: `tests/test_static_contract.py`

Le front ne doit plus contenir toute la liste des questions en dur, sauf fallback offline.

---

## Task 7: Générer le rapport final uniquement à la fin

**Objective:** Le panneau documents s’ouvre seulement quand le rapport est généré.

**Files:**
- Modify: `pages-app/audit.html`
- Modify: `src/proposal_server.py`
- Test: `tests/test_proposal_server.py`

Sorties :

```txt
rapport_audit.md
rapport_audit.pdf
devis_source.json
linkedin_post.txt
share_payload.json
```

---

## Task 8: Ajouter exports et partage

**Objective:** Email, Markdown, PDF, lien partage, texte LinkedIn/social.

**Files:**
- Modify: `src/proposal_server.py`
- Modify: `pages-app/audit.html`
- Test: `tests/test_proposal_server.py`

Actions UI finales :

```txt
Télécharger MD
Télécharger PDF
Envoyer par email
Copier lien de partage
Partager LinkedIn
Copier texte LinkedIn
```

V0 email peut être `email_mode=log` si SMTP non configuré, mais doit le dire clairement.

---

## Task 9: Vérification navigateur

**Objective:** Prouver le parcours complet.

Run:

```bash
python3 scripts/build.py
python3 -m pytest -q
OA_PROPOSALS_TOKEN=<token-local-long> python3 src/proposal_server.py --host 127.0.0.1 --port 18110 --data-dir /tmp/oa-audit-sector-smoke
```

Browser smoke :

1. Démarrer audit avec un boulanger.
2. Vérifier que les questions parlent de boutique, commandes, saisonnalité, allergies/prix/publication.
3. Valider les étapes seulement après réponses suffisantes.
4. Générer rapport.
5. Vérifier que le panneau documents apparaît seulement à la fin.
6. Télécharger/coller le Markdown et le texte LinkedIn.

---

## Critère de succès

L’audit est crédible quand un avocat, un plombier, un fleuriste, un boulanger, un restaurateur, un gestionnaire de patrimoine ou un freelance marketing a l’impression qu’Omar comprend les spécificités de son métier, pose des questions pertinentes, et ne produit pas un rapport générique.
