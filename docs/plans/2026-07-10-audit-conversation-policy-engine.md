# Audit Conversation Policy Engine Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build AppOmar's own conversation policy engine so audit quick replies are ranked, contextual, traceable, and validated before becoming product behavior.

**Architecture:** Keep the audit tree as the declarative product contract, but move runtime decisions into a deterministic `conversation_policy` layer. The engine classifies intent, computes missing-field state, scores candidate actions, emits ranked `next_best_actions`, and records why actions were shown/clicked without treating helper clicks as factual business answers.

**Tech Stack:** Python 3.11, existing `src/audit_intelligence.py`, `src/audit_tree.business_tech.v1.yaml`, pytest, current proposal server APIs, browser smoke tests for `/audit/`.

---

## Product thesis

The objective is not to hard-code every possible quick reply. The objective is:

```txt
question → user/context signal → intent classification → missing-field scoring → ranked next-best-actions → trace → optional validation → answer storage / step transition
```

Quick replies are not decoration. They are a **policy output** with probabilities and reasons.

A button shown to the user should carry:

```json
{
  "id": "identity_continue_without_account",
  "label": "Continuer sans compte",
  "intent": "confirm",
  "rank": 1,
  "score": 0.94,
  "confidence": 0.88,
  "reason": "Opening pact asks save-vs-start; fastest non-blocking path is continue without account.",
  "evidence": ["current_step:pacte", "missing:sauvegarde_choix", "user_not_authenticated"],
  "stores_answer": false,
  "advances_step": true,
  "safety": "no_paid_action"
}
```

---

## Non-negotiables

1. **Free text always available.** Buttons guide; they never replace conversation.
2. **Ranked actions, not unordered buttons.** The first button is Omar's best guess.
3. **Explainability.** Every action has `score_reasons` and `evidence`.
4. **No fake answers.** `Voir un exemple`, `Pourquoi utile ?`, `Je précise`, etc. must never populate business fields.
5. **Alex test mode.** Alex clicking every button must not poison product analytics.
6. **Validation mode.** Before public stabilization, H-Omar/Alex can review whether the top 2-3 buttons are acceptable per step.
7. **No LLM free-for-all.** A future LLM may propose candidates, but deterministic policy ranks/filters/gates them.
8. **No paid action.** This engine cannot trigger checkout, provisioning, or external POST side effects.

---

## Core data contract

### `PolicyContext`

Create a normalized context object for the current decision:

```python
@dataclass(frozen=True)
class PolicyContext:
    session_id: str
    current_step: str
    expected_fields: list[str]
    missing_fields: list[str]
    last_user_text: str | None
    last_intent: str | None
    user_is_authenticated: bool
    is_tester: bool
    step_answers: dict[str, Any]
    transcript_tail: list[dict[str, Any]]
    sector_id: str
    public_source_consent: dict[str, bool]
```

### `CandidateAction`

```python
@dataclass(frozen=True)
class CandidateAction:
    id: str
    label: str
    intent: str
    action_type: Literal["answer", "helper", "navigation", "validation", "source_consent"]
    stores_answer: bool = False
    advances_step: bool = False
    requires_free_text: bool = False
    safety: str = "no_side_effect"
```

### `RankedAction`

```python
@dataclass(frozen=True)
class RankedAction:
    id: str
    label: str
    intent: str
    rank: int
    score: float
    confidence: float
    score_reasons: list[str]
    evidence: list[str]
    action_type: str
    stores_answer: bool
    advances_step: bool
    telemetry_weight: float
```

### API shape returned to front

Every `omar` response should include:

```json
{
  "actions_schema": "oa.audit.next_best_actions.v1",
  "actions_mode": "ranked",
  "actions": [
    {
      "id": "...",
      "label": "...",
      "intent": "...",
      "rank": 1,
      "score": 0.94,
      "confidence": 0.88,
      "score_reasons": ["..."],
      "evidence": ["..."],
      "stores_answer": false,
      "advances_step": true,
      "telemetry_weight": 1.0
    }
  ]
}
```

---

## Scoring model V1

Use deterministic additive scoring first. Keep it simple and testable.

### Base factors

| Factor | Example | Weight |
|---|---:|---:|
| Matches current question goal | button directly answers save-vs-start | +0.35 |
| Resolves a required missing field | `nom_entreprise` expected | +0.25 |
| Low friction / no account wall | start without account | +0.12 |
| Helps when user seems confused | last intent = `clarify` | +0.18 |
| Preserves safety | no external source without consent | +0.20 |
| Avoids premature validation | helper action on incomplete step | +0.15 |
| Repeated / already shown recently | same helper clicked twice | -0.10 |
| Placeholder mistaken as answer risk | `Je précise`, `Autre`, `Je ne sais pas` | -0.30 for stores_answer |

### Confidence V1

Confidence is not the same as score.

```python
confidence = clamp(
    0.45
    + 0.20 if expected_field_known else 0
    + 0.15 if current_step_has_policy else 0
    + 0.10 if last_intent_clear else 0
    - 0.20 if ambiguous_text else 0,
    0,
    1,
)
```

### Ranking rules

- Return 2-4 actions; default target = 3.
- If one action is clearly dominant (`score >= second + 0.25`), allow 2 actions only.
- If the user is confused, rank helper action first.
- If the step is complete, rank validation/continue first.
- If public-source consent is needed, never rank external research as implicit; it must be explicit.

---

## Analytics and trace model

### Show event

Every time actions are emitted:

```json
{
  "event": "actions_shown",
  "at": "ISO-8601",
  "step": "identity_public_context",
  "question_id": "identity.name_city.v1",
  "actions": [{"id": "...", "rank": 1, "score": 0.92}],
  "policy_version": "conversation_policy.v1",
  "is_tester": true
}
```

### Click event

Every button click posts an event before any state mutation:

```json
{
  "event": "action_clicked",
  "at": "ISO-8601",
  "step": "identity_public_context",
  "action_id": "identity_help_example",
  "rank": 2,
  "intent": "help",
  "is_tester": true,
  "stores_answer": false,
  "advances_step": false
}
```

### Tester weighting

If `is_tester=true`, record events but set:

```json
{"telemetry_weight": 0.0, "analysis_bucket": "internal_test"}
```

This solves Alex's concern: Alex can click everything while testing without corrupting product signal.

---

## Validation workflow for Alex/H-Omar

Before public release, add a validation mode that lets us review the top actions without pretending user data proves they are good.

### Validation artifact

Create a local/test JSON artifact per step:

```json
{
  "step": "identity_public_context",
  "question": "Commençons simple...",
  "ranked_actions": [...],
  "review": {
    "status": "pending|approved|rejected|needs_change",
    "reviewer": "alex|h-omar|h-athena",
    "notes": "..."
  }
}
```

### Review statuses

- `approved`: top 2-3 are acceptable.
- `needs_change`: labels/order/reasons need edits.
- `rejected`: wrong mental model for the step.
- `pending`: not reviewed.

### Gate rule

For a public/prospect gate:

```txt
No release if any V0 step has ranked actions unreviewed or rejected.
```

This can later be part of H-Athena review.

---

## Implementation tasks

### Task 1: Add failing tests for ranked pacte actions

**Objective:** Prove the opening save/start question returns relevant ranked actions, not generic buttons.

**Files:**
- Modify: `tests/test_audit_tree_runtime.py`

**Test:**

```python
def test_business_tech_pacte_returns_ranked_save_start_actions():
    created = ai.create_session({"tree_id": "business_tech"})
    q = created["omar"]
    assert q["actions_schema"] == "oa.audit.next_best_actions.v1"
    labels = [a["label"] for a in q["actions"]]
    assert labels[:3] == ["Continuer sans compte", "Se connecter pour sauvegarder", "En savoir plus"]
    assert q["actions"][0]["rank"] == 1
    assert q["actions"][0]["score"] > q["actions"][1]["score"]
    assert any("current_step:pacte" in e for e in q["actions"][0]["evidence"])
```

**Run:**

```bash
python3 -m pytest tests/test_audit_tree_runtime.py::test_business_tech_pacte_returns_ranked_save_start_actions -q
```

Expected: fail until policy engine exists.

---

### Task 2: Create `src/audit_conversation_policy.py`

**Objective:** Introduce policy dataclasses and a first `rank_actions(context)` implementation.

**Files:**
- Create: `src/audit_conversation_policy.py`
- Test: `tests/test_audit_conversation_policy.py`

**Minimal API:**

```python
def build_policy_context(session: dict[str, Any], step_id: str, *, last_user_text: str | None = None) -> PolicyContext: ...
def candidate_actions_for_step(context: PolicyContext) -> list[CandidateAction]: ...
def rank_actions(context: PolicyContext, candidates: list[CandidateAction] | None = None) -> list[dict[str, Any]]: ...
```

**Verification:**

```bash
python3 -m pytest tests/test_audit_conversation_policy.py -q
```

---

### Task 3: Wire ranked actions into `next_question()` for business-tech sessions

**Objective:** Replace `_tree_contextual_actions()` generic return with policy-ranked actions for `BUSINESS_TECH_SESSION_SCHEMA`.

**Files:**
- Modify: `src/audit_intelligence.py`

**Rule:**
- `next_question()` still returns `actions` for the front.
- Add `actions_schema`, `actions_mode`, `policy_version`.
- Preserve old labels only if no policy candidates exist.

**Verification:**

```bash
python3 -m pytest tests/test_audit_tree_runtime.py tests/test_j1ter_conversation_documents.py -q
```

---

### Task 4: Add trace recording for shown/clicked actions

**Objective:** Record why actions were shown and which were clicked, without corrupting answer state.

**Files:**
- Modify: `src/audit_intelligence.py`
- Possibly modify: `src/proposal_server.py` if a dedicated action event endpoint is cleaner.
- Test: `tests/test_audit_conversation_policy_trace.py`

**Session field:**

```python
session.setdefault("metrics", {}).setdefault("action_events", []).append(event)
```

**Events:**
- `actions_shown`
- `action_clicked`

**Verification:**

```bash
python3 -m pytest tests/test_audit_conversation_policy_trace.py -q
```

---

### Task 5: Front posts action click metadata

**Objective:** When a quick reply is clicked, the front sends `action_id`, `rank`, and `intent`, not only label text.

**Files:**
- Modify: `pages-app/audit.html`

**Rule:**
- Helper actions (`help`, `value`, `challenge`, `unknown`, `focus`) are not posted as business answers.
- Navigation/answer actions include action metadata.
- If backend endpoint is not ready, keep a safe no-op fallback.

**Verification:**

Browser console expression:

```js
[...document.querySelectorAll('#quick-replies button')].map(b => ({
  id: b.dataset.actionId,
  rank: b.dataset.rank,
  score: b.dataset.score,
  text: b.innerText
}))
```

---

### Task 6: Add Alex/internal tester mode

**Objective:** Let internal tests record events with `telemetry_weight=0.0`.

**Options:**
- Query param: `/audit/?tester=alex`
- Session payload flag: `{tester: true}`
- Authenticated admin flag later

**V1 rule:**
Use query param only for local/PR testing. Do not expose as trusted security feature.

**Verification:**

```python
assert event["is_tester"] is True
assert event["telemetry_weight"] == 0.0
```

---

### Task 7: Add review artifact exporter

**Objective:** Produce a JSON report of ranked actions for every V0 step so Alex/H-Omar can validate the button set before release.

**Files:**
- Create: `scripts/export_audit_action_review.py`
- Output: `artifacts/audit_action_review.<timestamp>.json`

**Command:**

```bash
python3 scripts/export_audit_action_review.py --tree business_tech --out /tmp/audit_action_review.json
```

**Expected sections:**
- step id / label
- question
- missing fields
- top actions
- scores
- reasons
- pending review status

---

### Task 8: Add regression transcript tests

**Objective:** Preserve the behavior Alex cares about: ambiguous/test clicks do not fill wrong fields and ranked actions adapt.

**Files:**
- Modify/create: `tests/test_audit_conversation_policy_transcripts.py`

**Cases:**
1. Alex clicks every helper button: no business fields are filled.
2. User asks “pourquoi ?”: helper ranked first next time.
3. User gives clear answer: validate/continue ranked first.
4. User gives off-field answer: store transcript, do not fill wrong field.
5. Opening pacte never shows `Je réponds / Montrez-moi des exemples / Je ne sais pas encore`.

---

### Task 9: Browser smoke for first two steps

**Objective:** Verify visible behavior, not only Python tests.

**Checks:**
- `/audit/` opening shows ranked save/start/help buttons.
- Buttons have `data-rank`, `data-score`, `data-action-id`.
- `Pourquoi utile ?` stays on same step.
- `Continuer sans compte` advances to Identité.
- Identité top action is appropriate to missing nom/ville.
- Fullscreen preserved.

---

## Release gate

Before merging/deploying:

```bash
node --check /tmp/audit-script.js
python3 -m pytest tests -q
git diff --check
```

Browser smoke:

```js
document.body.scrollHeight === window.innerHeight
```

Policy smoke:

```python
all(a["rank"] == i+1 for i, a in enumerate(actions))
all("score_reasons" in a and a["evidence"] for a in actions)
```

H-Athena gate should verify:

- no helper click stored as factual answer;
- no generic quick replies on pacte/identity;
- all V0 steps have ranked actions;
- public-source research still requires explicit consent;
- no payment/provisioning side effect added.

---

## Open decisions

1. **Button count:** default 3, allow 2 when one action dominates, allow 4 only when explanation/helper/focus are all valuable.
2. **Tester detection:** V1 query param is enough; later admin/auth flag.
3. **LLM role:** no LLM in V1 ranking. Later, LLM can propose candidate labels, but deterministic ranker must approve/filter.
4. **Analytics storage:** V1 session JSON/DB metrics; later aggregate dashboard.
5. **Validation UI:** V1 JSON artifact; later internal review panel.

---

## Definition of done

- Opening audit and every V0 step return `actions_schema=oa.audit.next_best_actions.v1`.
- Actions are ranked with score/confidence/reasons/evidence.
- Click events are traced.
- Tester clicks are recorded but analytics weight is zero.
- Helper clicks never become business facts.
- Alex/H-Omar can review the ranked actions artifact before release.
- Full test suite passes.
- Browser smoke proves the first two steps visually.
