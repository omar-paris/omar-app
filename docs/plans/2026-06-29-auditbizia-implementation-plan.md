# AuditBizIA — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build AuditBizIA: a conversational business-audit intelligence layer that deeply understands a user's business, adapts questions dynamically, and produces a reusable MD/PDF business-understanding report.

**Architecture:** Use structured sector knowledge packs as the source of truth, an explicit audit state store for facts/hypotheses/answers, a next-best-question engine for adaptive conversation, and later a local vector index for retrieval over rich métier knowledge. Learning from conversations produces reviewed improvement proposals, not automatic uncontrolled mutations.

**Tech Stack:** Python, JSON/YAML knowledge packs, SQLite, optional sqlite-vec/LanceDB later, existing AppOmar audit backend/UI/tests.

---

## Decisions to tranche now

### D1 — Product promise

**Decision needed:** Is AuditBizIA primarily:

A. a lead-generation audit before OA sales, or
B. a standalone valuable business-understanding product, with OA sales downstream?

**Recommended:** B. The audit must be valuable even if the client does not buy OA afterward. It produces a business-understanding report usable with any agent.

### D2 — UX model

**Decision needed:** Should there be a visible “Question métier” button in final UX?

**Recommended:** No. Keep it only as dev/prototype aid if needed. In final UX, deep métier questions are native to the conversation.

### D3 — Macro-steps

**Decision needed:** Freeze a first stable step contract.

**Recommended V1 steps:**
1. Préférences de conversation
2. Identité / activité / contexte
3. Sources autorisées
4. Modèle métier
5. Opérations / outils / production
6. Clients / marché / concurrence
7. Finance / pilotage / priorités
8. Risques / conformité / garde-fous
9. Opportunités IA
10. Validation finale / rapport

### D4 — Knowledge architecture

**Decision needed:** RAG-only, SQL-only, or hybrid?

**Recommended:** Hybrid. Structured sector packs first; vector retrieval second. Never use vector search as the only source of audit logic.

### D5 — Storage V1

**Decision needed:** Start simple or introduce full vector DB immediately?

**Recommended:** Start with SQLite + JSON/YAML sector packs. Add sqlite-vec or LanceDB only after the question engine and audit state are stable.

### D6 — Learning governance

**Decision needed:** Should user conversations directly update sector knowledge?

**Recommended:** No. Store signals and generate improvement proposals. Promote proposals only after review/gate.

### D7 — First vertical depth

**Decision needed:** Which vertical proves AuditBizIA first?

**Recommended:** Boulangerie first, because Alex has source material and strong product intuition. Then restaurant, avocat, gestion de patrimoine.

### D8 — Report contract

**Decision needed:** What is the mandatory deliverable?

**Recommended:** MD first, PDF renderer second. Report must separate: user-declared facts, public sources, hypotheses, missing/ignored questions, risks, priorities, IA opportunities, and reusable instructions for future agents.

---

## Phase 1 — Foundation: Audit state and sector pack contract

### Task 1: Create AuditBizIA domain schemas

**Objective:** Define the data contract for sector packs, questions, audit facts, hypotheses, and question feedback.

**Files:**
- Create: `src/auditbiz_schema.py`
- Create: `tests/test_auditbiz_schema.py`

**Verification:**
- JSON/YAML examples validate.
- Missing required fields fail clearly.

### Task 2: Move bakery deep map into canonical knowledge pack

**Objective:** Stop growing `data/audit_sectors/bakery.json` as a monolith; create a structured sector pack.

**Files:**
- Create: `data/audit_knowledge/sectors/bakery/sector.yaml`
- Create: `data/audit_knowledge/sectors/bakery/facets.yaml`
- Create: `data/audit_knowledge/sectors/bakery/questions.yaml`
- Create: `data/audit_knowledge/sectors/bakery/risks.yaml`
- Create: `data/audit_knowledge/sectors/bakery/sources.md`
- Modify: `src/audit_intelligence.py`

**Verification:**
- Existing bakery tests still pass.
- New loader reads canonical pack.

### Task 3: Add explicit audit state store

**Objective:** Persist structured facts, hypotheses, questions asked, skips, and validation status.

**Files:**
- Create: `src/auditbiz_store.py`
- Create: `tests/test_auditbiz_store.py`

**Storage V1:** SQLite.

**Verification:**
- Can create session.
- Can add fact with source/confidence/validated.
- Can add hypothesis requiring validation.
- Can record skipped question.
- Can resume session.

---

## Phase 2 — Next Best Question Engine

### Task 4: Implement candidate question retrieval from structured packs

**Objective:** Generate candidate questions by sector and step.

**Files:**
- Create: `src/auditbiz_question_engine.py`
- Create: `tests/test_auditbiz_question_engine.py`

**Verification:**
- Bakery activity step returns ranked activity question.
- Risk step returns HACCP/allergen/human-validation questions.
- Finance step returns margin/pricing/treasury questions.

### Task 5: Implement scoring logic

**Objective:** Score questions by usefulness, missing fields, fatigue, sensitivity, skip history, and report impact.

**Initial scoring signals:**
- fills missing critical field
- validates low-confidence hypothesis
- unlocks IA recommendation
- asks a risk/garde-fou question
- has not been asked before
- not too sensitive too early
- not skipped repeatedly

**Verification:**
- Question already asked is penalized.
- Sensitive finance question is delayed if trust/context low.
- Skipped question does not block progress.

### Task 6: Replace “Question métier” with native next question flow

**Objective:** Conversation endpoint automatically uses next-best-question instead of requiring a visible button.

**Files:**
- Modify: `src/proposal_server.py`
- Modify: `pages-app/audit.html`
- Modify: tests

**Verification:**
- Final UI has no `Question métier` dev button.
- Backend returns next question with why/options/skip/save metadata.
- Chat renders choices naturally.

---

## Phase 3 — Learning signals

### Task 7: Record question quality feedback

**Objective:** Store whether a question was answered, skipped, unclear, too deep, useful, or required explanation.

**Files:**
- Modify: `src/auditbiz_store.py`
- Modify: `pages-app/audit.html`
- Create/modify tests

**Verification:**
- `skip` records a signal.
- `why` records that explanation was requested.
- answered question records answer quality metadata.

### Task 8: Generate knowledge improvement proposals

**Objective:** Aggregate feedback into human-reviewable proposals, not automatic pack mutation.

**Files:**
- Create: `src/auditbiz_learning.py`
- Create: `tests/test_auditbiz_learning.py`
- Create: `data/audit_knowledge/proposals/.gitkeep`

**Verification:**
- Several skipped questions produce a proposal to move/rewrite question.
- Several useful answers produce a proposal to keep/promote question.

---

## Phase 4 — Report contract

### Task 9: Build AuditBizIA MD report exporter

**Objective:** Produce a reusable business-understanding report.

**Files:**
- Create: `src/auditbiz_report.py`
- Create: `tests/test_auditbiz_report.py`

**Report sections:**
1. Portrait de l’entreprise
2. Faits déclarés validés
3. Sources publiques utilisées/refusées
4. Hypothèses à confirmer
5. Questions passées / non répondues
6. Carte métier
7. Forces
8. Fragilités
9. Risques / garde-fous
10. Priorités business
11. Opportunités IA
12. Premières boucles IA recommandées
13. Instructions réutilisables pour futurs agents

**Verification:**
- Report separates facts/hypotheses/sources.
- Report includes skipped questions without blocking completion.

---

## Phase 5 — Retrieval / RAG local

### Task 10: Add local vector retrieval after structured engine works

**Objective:** Improve recall over rich métier notes/sources/examples without making vector retrieval the decision-maker.

**Decision after Phase 2:** sqlite-vec vs LanceDB.

**Recommended default:** sqlite-vec if easy to package with current app; LanceDB if embedding/document workflow is simpler.

**Verification:**
- Retrieval returns relevant métier snippets.
- Question engine can cite retrieved knowledge as context.
- No private user conversation is inserted into shared sector knowledge without anonymization/review.

---

## Immediate execution recommendation

Do not start with RAG. Start with:

1. schemas,
2. canonical bakery knowledge pack,
3. SQLite audit state,
4. next-best-question engine,
5. remove final-product dependency on the `Question métier` button.

This produces the core product before adding vector complexity.
