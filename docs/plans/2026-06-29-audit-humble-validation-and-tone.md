# Humble Validation + Tone Preferences Implementation Plan

> **For Hermes:** Use software-development-lifecycle for implementation and verification.

**Goal:** Make the audit start with communication preferences and make every enriched public fact humble, client-validated, and sector-vocabulary aware.

**Architecture:** The backend owns step contracts, required fields, client understanding summaries, and public fact normalization. The UI mirrors the same steps and wording. Registry identifiers remain metadata; client-facing summaries prioritize address, public activity, public financial hints, and validation prompts.

**Tech Stack:** Python stdlib backend/tests, static HTML/JS frontend, pytest.

---

## Applied tasks

### Task 1: Add conversation preference gate

**Files:**
- Modified: `src/audit_intelligence.py`
- Modified: `pages-app/audit.html`
- Modified: `tests/test_audit_intelligence.py`

**Behavior:**
- New first step `intro` asks tutoiement/vouvoiement and conversation mode.
- Validation requires `communication_preferences`.
- UI rail starts with `Préférences`.

### Task 2: Make summaries humble and validation-first

**Files:**
- Modified: `src/audit_intelligence.py`
- Modified: `pages-app/audit.html`

**Behavior:**
- Omar says “Voici ce que j’ai compris / récupéré”.
- Public facts are not treated as truth before client validation.
- Client-facing prompts ask: validate, modify, or “ce n’est pas vous”.

### Task 3: De-emphasize SIREN/SIRET in client wording

**Files:**
- Modified: `src/audit_intelligence.py`
- Modified: `src/proposal_server.py`
- Modified: `pages-app/audit.html`

**Behavior:**
- SIREN/SIRET remain metadata for traceability.
- Client-facing fact value prioritizes name, exact address, activity, city, and public financial summary when present.
- `fetch_recherche_entreprises()` now captures address, creation date, employee range, and a public financial summary when the API exposes one.

### Task 4: Replace harsh “irritants” wording

**Files:**
- Modified: `src/audit_intelligence.py`
- Modified: `pages-app/audit.html`

**Behavior:**
- UI label becomes `Blocages`.
- Copy talks about points de blocage, limites, charge, complexité, confiance, compétence, fournisseurs, constraints — more diplomatic.

### Task 5: Improve sector vocabulary for lawyers

**Files:**
- Modified: `data/audit_sectors/lawyer.json`

**Behavior:**
- Lawyer vertical now explicitly asks for “spécialité / dominante de pratique”.

### Task 5: Add fluid quick replies and fact-action buttons

**Files:**
- Modified: `pages-app/audit.html`
- Modified: `tests/test_static_contract.py`

**Behavior:**
- The composer now includes `Réponses rapides` buttons for each audit step.
- Buttons send a real conversational answer, so the user can continue without typing.
- Public research results now expose direct action buttons: `Oui c’est moi`, `À modifier`, `Ce n’est pas moi`, `Ignorer cette source`.
- These buttons support the desired rhythm: Omar proposes, the user validates/corrects/refuses, then the conversation continues fluidly.

### Task 6: Add ranked micro-questions and local context intelligence

**Files:**
- Modified: `src/audit_intelligence.py`
- Modified: `pages-app/audit.html`
- Modified: `data/audit_sectors/bakery.json`
- Modified: `tests/test_audit_intelligence.py`
- Modified: `tests/test_static_contract.py`

**Behavior:**
- Bakery now exposes activity facets: boulangerie, pâtisserie, viennoiseries, sandwicherie/snacking, commandes spéciales/événementiel.
- The audit UI can launch a ranking mode: first click = rang #1, second click = rang #2, third click = rang #3, with an `Autre` option for free text.
- Registry addresses are turned into a cautious location context to validate: hypercentre, urbain, périurbain, rural, or à valider.
- Location context carries sector implications, e.g. bakery hypercentre = passage/rush/concurrence; périurbain = trajets/voiture/horaires.
- Public research summaries now show this as `Lecture locale à valider`, not as a conclusion.

### Task 7: Add deep bakery domain map and interruption controls

**Files:**
- Modified: `data/audit_sectors/bakery.json`
- Modified: `src/audit_intelligence.py`
- Modified: `pages-app/audit.html`
- Modified: `tests/test_audit_intelligence.py`
- Modified: `tests/test_static_contract.py`

**Implemented:**
- Added a deep bakery facet map from Alex's Caplain DOCX + public bakery-business sources:
  - savoir-faire / dirigeant dependency
  - emplacement / zone de chalandise / flux
  - production, offre, fraîcheur, pertes and invendus
  - achats, fournisseurs, stocks, traçabilité
  - équipe, planning, recrutement, transmission
  - expérience client, avis, fidélité, réclamations
  - marge, prix, trésorerie, pilotage
  - hygiène, HACCP, allergènes, conformité
  - concurrence, marketing local, visibilité
  - équipement, local, maintenance, capacité
  - potentiel IA and explicit guardrails
- Each deep question now carries:
  - interaction type (`open`, `choice`, `rank`)
  - why/explanation
  - options when relevant
  - follow-up
  - skip allowed
  - save/resume allowed
  - feedback prompt for question quality
- Added engine helpers:
  - `sector_deep_facets(sector_id)`
  - `recommend_micro_questions(session, step, limit=...)`
- Added UI controls:
  - `Question métier`
  - `Pourquoi cette question`
  - `Passer cette question`
  - `Enregistrer et reprendre plus tard`
- Added local browser draft save/restore (`localStorage`) for long audits.
- Verified the first deep question renders as a ranked activity question and avoids duplicate `Autre`.

**Validation:**
- `python3 -m pytest -q tests/test_audit_intelligence.py tests/test_static_contract.py` → `28 passed in 1.09s`
- `python3 scripts/build.py && python3 -m pytest -q tests` → `45 passed in 2.65s`
- `git diff --check` → clean
- Browser `/audit/` smoke: deep question button opens rank buttons, no JS console errors.

## Next exploration

1. Build a per-sector “critical vocabulary” map so each vertical has exact words that must appear: spécialité for avocat, carte/réservations for restaurant, allergènes/commandes for boulangerie, ORIAS/statut CIF for patrimoine.
2. Add a `facts_to_validate` queue with statuses: `pending`, `validated`, `corrected`, `not_me`, `ignored`.
3. Add UI buttons for public facts: “Oui c’est moi”, “Modifier”, “Ce n’est pas moi”.
4. Add report section: `Informations récupérées à valider` before recommendations.

## Verification

Run:

```bash
python3 -m pytest -q tests/test_audit_intelligence.py tests/test_proposal_server.py
python3 scripts/build.py
python3 -m pytest -q tests
```
