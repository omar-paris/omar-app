# Contrat telemetry minimal AppOmar audit — sessions, boutons, validations

Date: 2026-07-10
Carte: t_fd769994 (incident auth supersédé par t_14740e85, mais contrat produit ici comme artefact intégrable)
Statut: artefact de contrat/tests, sans modification runtime.
Conflit repo: la lane AppOmar principale t_efc08ffe est traitée comme potentiellement active sur `pages-app/audit.html`, `src/proposal_server.py` et `src/audit_intelligence.py`; ce R2 se limite donc à ce document avant intégration.

## Objectif

Définir un contrat minimal d'événements pour comprendre le tunnel audit AppOmar sans collecter de PII inutilement :

- création de session ;
- boutons affichés et cliqués ;
- étapes validées ;
- recherche publique lancée ;
- rapport créé ;
- abandon heuristique.

Le contrat doit rester compatible avec l'état actuel : backend Python simple, sessions JSON dans `var/audit_sessions/`, front `pages-app/audit.html`, et politique stricte de séparation déclaré / vérifié / hypothèse.

## État actuel vérifié

### Backend sessions

Fichiers observés :

- `src/proposal_server.py:1547` crée une session via `POST /api/audit-sessions` puis l'écrit dans `var/audit_sessions/`.
- `src/proposal_server.py:1562` route les actions de session : `message`, `validate-step`, `research-plan`, `public-research`, `report`.
- `src/proposal_server.py:811` écrit la session JSON après contrôle d'id et refus de littéraux secrets.
- `src/audit_intelligence.py:1056` crée les sessions `oa_audit_session.business_tech.v1`.
- `src/audit_intelligence.py:1133` valide les étapes business-tech, met à jour `validated_steps`, `current_step`, `completion`, `status`.

### Metrics existants

- Legacy/fable seulement : `src/audit_intelligence.py:674` initialise `metrics.act_events`, et `src/audit_intelligence.py:717` ajoute un événement `step_validated`.
- Business-tech courant : les sessions récentes `var/audit_sessions/*.json` n'ont pas de clé `metrics`; les événements internes sont surtout `state.<step>.events` avec `answers_recorded`.
- Les 5 sessions les plus récentes vérifiées avaient `metrics keys []`, `act_events 0`, `action_events 0`.

### Front boutons

- `pages-app/audit.html:225` rend les quick replies.
- `pages-app/audit.html:230` expose seulement `data-reply` et `data-intent` aujourd'hui.
- `pages-app/audit.html:235` appelle `handleQuickReply(reply, intent)` sans `action_id`, `rank`, ni `score`.
- `pages-app/audit.html:314` traite des boutons localement ou via `/message` + `/validate-step`.

### Recherche et rapport

- `pages-app/audit.html:256` appelle `/api/audit-sessions/{sid}/public-research`.
- `src/proposal_server.py:1605` exécute/trace le bloc public-research dans `session.public_research[]`, mais pas encore dans `metrics`.
- `src/proposal_server.py:1656` génère le rapport via `safe_write_audit`, mais ne trace pas encore `report_created` dans la session.

## Principes de collecte

1. Pas de texte libre client dans les événements analytics.
2. Pas d'email, téléphone, nom public, adresse, SIRET, URL ou contenu de rapport dans `metrics`.
3. Les événements sont rattachés à un `session_id` opaque déjà généré côté backend.
4. Les boutons peuvent être analysés par `action_id`, `intent`, `rank`, `step`, jamais par texte client.
5. Les tests internes Alex/H-Omar doivent être enregistrés mais peser zéro : `telemetry_weight: 0.0`.
6. L'abandon est heuristique côté lecture/agrégateur, pas forcément écrit à chaque seconde par le front.
7. La recherche publique trace seulement le type de source autorisée/exécutée, pas le résultat brut.

## Enveloppe commune

Tous les événements proposés vont dans :

```json
{
  "schema": "oa.audit.telemetry_event.v1",
  "event": "button_clicked",
  "at": "2026-07-10T12:34:56Z",
  "session_id": "audit-session-20260710T023729Z-f91cc313",
  "tree_id": "business_tech",
  "tree_version": "2026-07-10",
  "step": "pacte",
  "acte": "rencontre",
  "source": "backend|frontend",
  "is_tester": false,
  "telemetry_weight": 1.0,
  "privacy": {
    "pii": false,
    "contains_free_text": false,
    "retention": "product_analytics_90d"
  }
}
```

Champs communs :

| Champ | Obligatoire | Note |
|---|---:|---|
| `schema` | oui | `oa.audit.telemetry_event.v1` |
| `event` | oui | enum ci-dessous |
| `at` | oui | ISO UTC |
| `session_id` | oui | id opaque existant |
| `tree_id` | recommandé | `business_tech` si disponible |
| `tree_version` | recommandé | version du YAML runtime |
| `step` | recommandé | étape courante |
| `acte` | optionnel | acte produit si disponible |
| `source` | oui | `backend` ou `frontend` |
| `is_tester` | oui | déduit d'un flag local/test/admin |
| `telemetry_weight` | oui | `0.0` pour test interne, sinon `1.0` |
| `privacy` | oui | garde-fou machine-testable |

## Événements JSON minimaux

### 1. `session_created`

Moment : juste après création et écriture de session.

```json
{
  "schema": "oa.audit.telemetry_event.v1",
  "event": "session_created",
  "at": "2026-07-10T12:00:00Z",
  "session_id": "audit-session-20260710T120000Z-12345678",
  "tree_id": "business_tech",
  "tree_version": "2026-07-10",
  "step": "pacte",
  "source": "backend",
  "entrypoint": "audit_page",
  "runtime_schema": "oa_audit_session.business_tech.v1",
  "is_tester": false,
  "telemetry_weight": 1.0,
  "privacy": {"pii": false, "contains_free_text": false, "retention": "product_analytics_90d"}
}
```

À exclure : message initial, nom entreprise, email, user-agent complet, IP brute.

### 2. `button_displayed`

Moment : quand le backend renvoie une liste d'actions OU quand le front rend les quick replies. Pour éviter les doublons, V0 recommande backend-only si les actions viennent du backend ; front-only seulement pour boutons locaux (`state.localQuickReplies`).

```json
{
  "schema": "oa.audit.telemetry_event.v1",
  "event": "button_displayed",
  "at": "2026-07-10T12:00:01Z",
  "session_id": "audit-session-20260710T120000Z-12345678",
  "tree_id": "business_tech",
  "tree_version": "2026-07-10",
  "step": "pacte",
  "source": "backend",
  "actions": [
    {"action_id": "continue_without_account", "intent": "confirm", "rank": 1, "stores_answer": true, "advances_step": true},
    {"action_id": "save", "intent": "save", "rank": 2, "stores_answer": false, "advances_step": false},
    {"action_id": "more_info", "intent": "explain", "rank": 3, "stores_answer": false, "advances_step": false}
  ],
  "is_tester": false,
  "telemetry_weight": 1.0,
  "privacy": {"pii": false, "contains_free_text": false, "retention": "product_analytics_90d"}
}
```

À exclure : libellé exact si une future variante contient des données client ; conserver `action_id` stable.

### 3. `button_clicked`

Moment : avant toute mutation d'état métier quand un bouton est cliqué.

```json
{
  "schema": "oa.audit.telemetry_event.v1",
  "event": "button_clicked",
  "at": "2026-07-10T12:00:04Z",
  "session_id": "audit-session-20260710T120000Z-12345678",
  "tree_id": "business_tech",
  "tree_version": "2026-07-10",
  "step": "pacte",
  "source": "frontend",
  "action_id": "continue_without_account",
  "intent": "confirm",
  "rank": 1,
  "stores_answer": true,
  "advances_step": true,
  "is_tester": false,
  "telemetry_weight": 1.0,
  "privacy": {"pii": false, "contains_free_text": false, "retention": "product_analytics_90d"}
}
```

Fallback si le front n'a pas encore `action_id` : générer `action_id: "legacy_intent:<intent>"` et `rank: null`, mais ne pas utiliser le label comme id durable.

### 4. `step_validated`

Moment : juste après validation réussie.

```json
{
  "schema": "oa.audit.telemetry_event.v1",
  "event": "step_validated",
  "at": "2026-07-10T12:01:20Z",
  "session_id": "audit-session-20260710T120000Z-12345678",
  "tree_id": "business_tech",
  "tree_version": "2026-07-10",
  "step": "pacte",
  "next_step": "identity_public_context",
  "source": "backend",
  "completion_pct_after": 8,
  "missing_count_before": 0,
  "is_tester": false,
  "telemetry_weight": 1.0,
  "privacy": {"pii": false, "contains_free_text": false, "retention": "product_analytics_90d"}
}
```

Note : le legacy fable a déjà un équivalent partiel dans `metrics.act_events`. Business-tech doit converger vers `metrics.telemetry_events` ou `metrics.audit_events`.

### 5. `research_run`

Moment : à la fin de `/public-research`, que des appels externes aient été tentés ou non.

```json
{
  "schema": "oa.audit.telemetry_event.v1",
  "event": "research_run",
  "at": "2026-07-10T12:03:10Z",
  "session_id": "audit-session-20260710T120000Z-12345678",
  "tree_id": "business_tech",
  "tree_version": "2026-07-10",
  "step": "public_sources_consent",
  "source": "backend",
  "dry_run": false,
  "external_calls_attempted": true,
  "connectors": [
    {"id": "public_web", "attempted": true, "status": "ok|error|skipped"},
    {"id": "recherche_entreprises", "attempted": false, "status": "skipped"}
  ],
  "consent_snapshot": {
    "public_web_search": true,
    "legal_registry_lookup": false,
    "social_media_lookup": false
  },
  "facts_count": 2,
  "errors_count": 0,
  "is_tester": false,
  "telemetry_weight": 1.0,
  "privacy": {"pii": false, "contains_free_text": false, "retention": "product_analytics_90d"}
}
```

À exclure : URL saisie, nom public, adresse, fiches récupérées, texte des erreurs si elles peuvent contenir une URL client.

### 6. `report_created`

Moment : après `safe_write_audit()` réussi.

```json
{
  "schema": "oa.audit.telemetry_event.v1",
  "event": "report_created",
  "at": "2026-07-10T12:20:00Z",
  "session_id": "audit-session-20260710T120000Z-12345678",
  "tree_id": "business_tech",
  "tree_version": "2026-07-10",
  "step": "validation",
  "source": "backend",
  "audit_id": "audit-20260710T122000Z-abcdef12",
  "status_after": "draft_report_ready",
  "sections_count": 17,
  "documents_available": true,
  "share_available": true,
  "is_tester": false,
  "telemetry_weight": 1.0,
  "privacy": {"pii": false, "contains_free_text": false, "retention": "product_analytics_90d"}
}
```

`audit_id` est un identifiant opaque acceptable si l'accès au rapport reste contrôlé. Ne pas inclure titre, résumé, recommandations, transcript, ni champs structurés.

### 7. `abandon_heuristic` / `abandon` heuristique

V0 recommandée : ne pas écrire un événement à chaud. Le calcul se fait par agrégation des sessions incomplètes.

Heuristique :

```json
{
  "schema": "oa.audit.telemetry_derived_event.v1",
  "event": "abandon_heuristic",
  "computed_at": "2026-07-10T13:00:00Z",
  "session_id": "audit-session-20260710T120000Z-12345678",
  "tree_id": "business_tech",
  "last_step": "operations_week",
  "last_event_at": "2026-07-10T12:06:00Z",
  "validated_steps_count": 4,
  "completion_pct": 31,
  "threshold_minutes": 30,
  "reason": "no_event_after_threshold_and_status_running",
  "privacy": {"pii": false, "contains_free_text": false, "retention": "product_analytics_90d"}
}
```

Règle V0 : session `status=running`, pas d'événement telemetry ni de message depuis 30 minutes, aucun `report_created`. L'agrégateur peut ignorer `is_tester=true` ou le garder avec `telemetry_weight=0.0`.

## Stockage recommandé

### Dans la session JSON V0

Ajouter :

```json
{
  "metrics": {
    "schema": "oa.audit.session_metrics.v1",
    "telemetry_events": []
  }
}
```

Pourquoi : intégration minimale, pas de nouveau datastore, testable avec les sessions existantes.

Limites : les sessions JSON grossissent ; pour V1, exporter aussi en JSONL append-only : `var/audit_telemetry/events-YYYYMMDD.jsonl`.

### Helper backend proposé

Fichier proposé : `src/audit_telemetry.py`

API minimale :

```python
def append_telemetry_event(session: dict, event: dict) -> dict: ...
def make_session_created(session: dict, *, is_tester: bool = False) -> dict: ...
def make_step_validated(session: dict, step: str, next_step: str | None, completion: dict) -> dict: ...
def make_research_run(session: dict, result: dict, plan: dict, payload: dict) -> dict: ...
def make_report_created(session: dict, audit: dict, report: dict) -> dict: ...
```

La fonction doit :

- injecter l'enveloppe commune ;
- refuser `contains_free_text=true` pour les events analytics ;
- supprimer/normaliser tout champ non autorisé ;
- forcer `telemetry_weight=0.0` si `is_tester`.

## Fichiers touchés proposés

Ordre d'intégration conseillé, pour éviter les conflits avec la lane AppOmar principale :

1. `tests/test_audit_telemetry_contract.py` — tests purs du helper, sans toucher au front.
2. `src/audit_telemetry.py` — helper et allowlist d'événements.
3. `src/audit_intelligence.py` — créer `session_created`, `button_displayed` backend pour actions business-tech, `step_validated` business-tech.
4. `src/proposal_server.py` — tracer `research_run`, `report_created`, et éventuellement endpoint `POST /api/audit-sessions/{sid}/telemetry` pour clic front.
5. `pages-app/audit.html` — ajouter `data-action-id`, `data-rank`, `data-score` aux boutons, poster `button_clicked` avant mutation avec fallback no-op.
6. `tests/test_proposal_server.py` — smoke API session/research/report avec vérification `metrics.telemetry_events`.
7. `tests/test_static_contract.py` — contrat front : les boutons exposent action id/rank, pas seulement reply/intent.

## Tests proposés

### Tests unitaires helper

```python
def test_append_telemetry_event_rejects_free_text_and_pii():
    session = {"id": "audit-session-20260710T120000Z-12345678", "schema": "oa_audit_session.business_tech.v1"}
    event = {"event": "button_clicked", "step": "pacte", "action_id": "continue_without_account", "privacy": {"pii": False, "contains_free_text": False}}
    out = append_telemetry_event(session, event)
    assert out["metrics"]["telemetry_events"][0]["schema"] == "oa.audit.telemetry_event.v1"
```

```python
def test_tester_events_have_zero_weight():
    session = {"id": "audit-session-20260710T120000Z-12345678", "runtime": {"tester": "alex"}}
    out = append_telemetry_event(session, {"event": "session_created", "privacy": {"pii": False, "contains_free_text": False}})
    assert out["metrics"]["telemetry_events"][0]["is_tester"] is True
    assert out["metrics"]["telemetry_events"][0]["telemetry_weight"] == 0.0
```

### Tests backend business-tech

```python
def test_business_tech_session_created_records_minimal_telemetry():
    created = audit_intelligence.create_session({"tree_id": "business_tech"})
    events = created["session"]["metrics"]["telemetry_events"]
    assert [e["event"] for e in events] == ["session_created", "button_displayed"]
    assert all(e["privacy"] == {"pii": False, "contains_free_text": False, "retention": "product_analytics_90d"} for e in events)
```

```python
def test_business_tech_validate_step_records_step_validated_without_answer_text():
    session = completed_pacte_session()
    result = audit_intelligence.validate_step(session, "pacte")
    event = result["session"]["metrics"]["telemetry_events"][-1]
    assert event["event"] == "step_validated"
    assert event["step"] == "pacte"
    assert "Continuer sans compte" not in json.dumps(event, ensure_ascii=False)
```

### Tests API

```python
def test_public_research_records_research_run_without_public_name_or_url(tmp_path):
    status, data = request_json("POST", f"/api/audit-sessions/{sid}/public-research", {"company_public_name": "Boulangerie Demo", "website": "https://demo.example", "dry_run": True})
    event = data["session"]["metrics"]["telemetry_events"][-1]
    assert event["event"] == "research_run"
    assert "Boulangerie Demo" not in json.dumps(event, ensure_ascii=False)
    assert "demo.example" not in json.dumps(event, ensure_ascii=False)
```

```python
def test_report_created_records_opaque_audit_id_only(tmp_path):
    status, data = request_json("POST", f"/api/audit-sessions/{sid}/report", report_payload)
    event = data["session"]["metrics"]["telemetry_events"][-1]
    assert event["event"] == "report_created"
    assert event["audit_id"].startswith("audit-")
    assert "repetitive_tasks" not in event
    assert "transcript" not in json.dumps(event, ensure_ascii=False)
```

### Tests front

```python
def test_audit_page_buttons_expose_action_metadata_without_label_as_id():
    build_site()
    html = (PUBLIC / "audit" / "index.html").read_text(encoding="utf-8")
    assert "data-action-id" in html
    assert "data-rank" in html
    assert "button_clicked" in html
```

## Risques RGPD et garde-fous

| Risque | Garde-fou |
|---|---|
| Capter des réponses libres dans analytics | `privacy.contains_free_text=false` obligatoire et test JSON négatif |
| Déduire l'identité via URL/site/SIRET | ne stocker que connecteurs + counts, jamais valeurs sources |
| Polluer les signaux avec tests Alex | `is_tester=true`, `telemetry_weight=0.0`, bucket interne |
| Transformer une action helper en réponse métier | `stores_answer=false` pour help/value/challenge/unknown/focus ; test que ces clics ne modifient pas `answers` |
| Conserver trop longtemps des données comportementales | retention produit 90 jours ; agrégats anonymisés ensuite |
| Événement abandon trop agressif | calcul dérivé, seuil 30 min configurable, jamais notification commerciale automatique |
| Conflit avec logs serveur contenant IP/user-agent | ce contrat n'utilise pas les logs HTTP ; pas d'IP brute dans `metrics` |

## Quick win sans PII

Quick win recommandé : implémenter uniquement `session_created`, `button_displayed` et `step_validated` côté backend business-tech dans `metrics.telemetry_events`.

Pourquoi :

- aucun besoin de changer le front ;
- pas de clic individuel ni texte libre ;
- mesure déjà le volume de sessions, la progression par étape et les boutons proposés ;
- donne un signal d'abandon dérivé : dernière étape validée + absence de rapport ;
- faible risque de conflit avec la lane UI active.

Scope quick win :

1. Ajouter `src/audit_telemetry.py`.
2. Appeler le helper dans `create_business_tech_session()` et `business_tech_validate_step()`.
3. Tester que les sessions business-tech récentes auraient une clé `metrics.telemetry_events` sans changer leur payload métier.

## Critères d'acceptation intégration

- Une session business-tech neuve contient `metrics.schema == "oa.audit.session_metrics.v1"`.
- Les événements ne contiennent aucun texte client ni source publique brute.
- Les boutons affichés ont des ids stables et un rang exploitable.
- Une validation d'étape ajoute exactement un `step_validated`.
- Une recherche publique ajoute un `research_run` même en `dry_run`.
- Une création de rapport ajoute un `report_created` sans transcript ni contenu rapport.
- Les tests internes peuvent être pondérés à zéro.
- L'abandon est calculable depuis les événements/sessions sans ping permanent front.
