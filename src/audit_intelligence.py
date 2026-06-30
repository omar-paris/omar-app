from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from auditbiz_question_engine import choose_next_question as auditbiz_choose_next_question

ROOT = Path(__file__).resolve().parents[1]
SECTORS_DIR = ROOT / "data" / "audit_sectors"
REQUIRED_SECTOR_FIELDS = {"sector_id", "labels", "important_dimensions", "question_blocks", "risk_flags", "benchmarks"}

FIELD_LABELS = {
    "communication_preferences": "façon de parler souhaitée",
    "business_activity": "métier exact",
    "location": "localisation / zone servie",
    "company_size": "taille d’équipe",
    "company_age": "ancienneté",
    "revenue_range": "ordre de grandeur financier ou refus de le partager",
    "client_types": "types de clients",
    "public_research_scope": "sources publiques autorisées ou refusées",
    "repetitive_tasks": "sujets chronophages / blocages concrets",
    "time_spent": "fréquence ou volume concerné",
    "tools": "outils et canaux actuels",
    "sensitive_data": "données ou décisions sensibles",
    "human_validation": "validations humaines obligatoires",
}

FIELD_PATTERNS = {
    "communication_preferences": [r"\b(tu|toi|tutoyer|tutoie|vous|vouvoyer|vouvoie|formel|direct|guid[ée]|libre|questions? courtes?)\b", r"\b(mode|ton|style)\b"],
    "business_activity": [r"\b(boulanger|restaurant|plombier|fleuriste|avocat|patrimoine|marketing|secr[ée]taire)\b", r"je suis", r"nous sommes"],
    "location": [r"\b(à|a|sur|près de|pres de)\s+[A-ZÉÈÀÂÎÔÛa-zéèàâêîôûç-]{2,}", r"\b(lille|paris|lyon|marseille|bordeaux|nantes|toulouse|nice)\b"],
    "company_size": [r"\b\d+\s*(personnes?|salari[ée]s?|collaborateurs?|associ[ée]s?)\b", r"\bsolo\b", r"\bind[ée]pendant\b"],
    "company_age": [r"\b\d+\s*(ans?|ann[ée]es?)\b", r"cré[ée]e?\s+il y a"],
    "revenue_range": [r"\b\d+\s*(k€|ke|€|euros|m€)\b", r"chiffre d.?affaires", r"\bca\b"],
    "client_types": [r"\b(clients?|particuliers?|pros?|professionnels?|entreprises?|collectivit[ée]s?|artisans?)\b"],
    "public_research_scope": [r"\b(site|www\.|https?://|siret|sirene|google business|fiche google|linkedin|instagram|facebook)\b", r"\b(nom de l.?entreprise|s.?appelle|enseigne)\b", r"\b(autorise|refuse|pas de recherche|recherche web|sources? publiques?)\b"],
    "repetitive_tasks": [r"\b(relances?|devis|emails?|r[ée]ponses?|planning|rendez-vous|factures?|posts?)\b"],
    "time_spent": [r"\b\d+\s*(h|heures?|jours?)\b", r"par semaine", r"par jour"],
    "tools": [r"\b(email|excel|whatsapp|agenda|google|drive|crm|notion|facturation|t[ée]l[ée]phone)\b"],
    "sensitive_data": [r"\b(donn[ée]es?|confidentiel|secret|prix|factures?|paiement|allerg[èe]nes?|juridique|financi[èe]res?)\b"],
    "human_validation": [r"validation humaine", r"valider", r"jamais automatiquement", r"avant publication"],
}

REQUIRED_BY_STEP = {
    "intro": ["communication_preferences"],
    "activity": ["business_activity", "location", "company_size", "company_age", "revenue_range", "client_types"],
    "research": ["public_research_scope"],
    "pain": ["repetitive_tasks", "time_spent"],
    "tools": ["tools"],
    "risk": ["sensitive_data", "human_validation"],
    "opportunities": ["repetitive_tasks"],
    "autonomy": ["human_validation"],
    "validation": [],
}

FALLBACK_QUESTIONS = {
    "communication_preferences": "Avant de parler métier : préférez-vous que je vous tutoie ou que je vous vouvoie ? Plutôt mode guidé avec questions courtes, conversation libre, ou synthèses régulières à valider ?",
    "business_activity": "Quel est votre métier exact et votre secteur principal ?",
    "location": "Où est située l’entreprise et quelle zone servez-vous ?",
    "company_size": "Quelle est la taille de l’entreprise : solo, associés, salariés, prestataires ?",
    "company_age": "Depuis combien de temps l’entreprise existe-t-elle ?",
    "revenue_range": "Quel est l’ordre de grandeur du chiffre d’affaires annuel ?",
    "client_types": "Quels types de clients servez-vous principalement ?",
    "public_research_scope": "Donnez le nom public de l’entreprise, son site/fiche Google/SIRET si vous les avez, et dites si Omar peut utiliser les sources publiques pour compléter l’audit. Vous pouvez aussi refuser explicitement.",
    "repetitive_tasks": "Quelles tâches reviennent le plus souvent ?",
    "time_spent": "Combien de temps ces tâches prennent-elles par semaine ?",
    "tools": "Quels outils utilisez-vous aujourd’hui ?",
    "sensitive_data": "Quelles données ou décisions sont sensibles ?",
    "human_validation": "Quelles actions doivent toujours rester validées par un humain ?",
}

STEP_CONTRACTS = {
    "intro": {
        "goal": "Installer le bon ton et le bon mode de conversation avant de poser les questions métier.",
        "validation_criteria": [
            "Préférence tutoiement/vouvoiement clarifiée.",
            "Mode de conversation choisi : guidé, libre, ou synthèses régulières.",
            "Accord sur le principe : Omar reformule humblement puis demande validation/correction.",
        ],
    },
    "activity": {
        "goal": "Identifier précisément l’entreprise avant toute recommandation.",
        "validation_criteria": [
            "Métier exact et secteur compris.",
            "Localisation et zone servie explicites.",
            "Taille de l’équipe connue.",
            "Âge de l’entreprise connu.",
            "Ordre de grandeur du chiffre d’affaires connu ou refus explicite.",
            "Typologie de clients connue.",
        ],
    },
    "research": {
        "goal": "Définir quelles sources publiques Omar peut utiliser pour éviter au client de tout répéter.",
        "validation_criteria": [
            "Nom public, site, SIRET/SIRENE, fiche Google ou réseaux renseignés quand disponibles.",
            "Consentement ou refus explicite par type de source.",
            "Plan de recherche localisé préparé avant toute recherche externe.",
            "Sources, hypothèses et réponses client resteront séparées dans le rapport.",
        ],
    },
    "pain": {
        "goal": "Comprendre les points de blocage, limites et charges qui pèsent réellement sur l’activité.",
        "validation_criteria": ["Sujets chronophages ou complexes nommés.", "Fréquence, volume ou niveau de confiance estimé.", "Exemples concrets fournis sans vocabulaire culpabilisant."],
    },
    "tools": {
        "goal": "Cartographier les outils et flux actuels.",
        "validation_criteria": ["Outils principaux listés.", "Canaux entrants identifiés.", "Ruptures ou doubles saisies repérées."],
    },
    "risk": {
        "goal": "Identifier les données sensibles et les actions interdites à l’automatisation.",
        "validation_criteria": ["Données sensibles listées.", "Actions nécessitant validation humaine explicites.", "Limites métier acceptées."],
    },
    "opportunities": {
        "goal": "Choisir les premières boucles IA utiles et réalistes.",
        "validation_criteria": ["Une première boucle utile identifiée.", "Bénéfice attendu formulé.", "Risque acceptable ou garde-fou associé."],
    },
    "autonomy": {
        "goal": "Déterminer le niveau d’accompagnement souhaité.",
        "validation_criteria": ["Mode apprendre/déléguer/mixte choisi.", "Rythme réaliste défini.", "Validation humaine confirmée."],
    },
    "validation": {
        "goal": "Figer ce qui est vrai, hypothétique ou manquant avant rapport.",
        "validation_criteria": ["Client a relu la synthèse.", "Manques connus listés.", "Accord pour produire le rapport."],
    },
}


def step_contract(step: str) -> dict[str, Any]:
    return STEP_CONTRACTS.get(step, {"goal": "Clarifier cette étape.", "validation_criteria": ["Réponse concrète fournie."]})

def load_sector_references(sectors_dir: Path = SECTORS_DIR) -> dict[str, dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}
    for path in sorted(sectors_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_SECTOR_FIELDS - set(data)
        if missing:
            raise ValueError(f"{path.name} missing {sorted(missing)}")
        refs[str(data["sector_id"])] = data
    if "generic_tpe" not in refs:
        raise ValueError("generic_tpe sector missing")
    return refs

def detect_sector(text: str, refs: dict[str, dict[str, Any]] | None = None) -> str:
    refs = refs or load_sector_references()
    hay = (text or "").casefold()
    best = (0, "generic_tpe")
    for sid, ref in refs.items():
        score = sum(1 for label in ref.get("labels", []) if str(label).casefold() in hay)
        if score > best[0] and sid != "generic_tpe":
            best = (score, sid)
    return best[1]

def extract_fields(text: str) -> dict[str, bool]:
    hay = text or ""
    return {field: any(re.search(pattern, hay, re.I) for pattern in patterns) for field, patterns in FIELD_PATTERNS.items()}

def session_text(session: dict[str, Any]) -> str:
    parts=[]
    for msg in session.get("messages", []):
        parts.append(str(msg.get("text", "")))
    for value in (session.get("answers") or {}).values():
        parts.append(str(value))
    return "\n".join(parts)

def missing_fields(session: dict[str, Any], step: str) -> list[str]:
    found = extract_fields(session_text(session))
    return [f for f in REQUIRED_BY_STEP.get(step, []) if not found.get(f)]

def completion_for_step(session: dict[str, Any], step: str) -> dict[str, Any]:
    required = REQUIRED_BY_STEP.get(step, [])
    missing = missing_fields(session, step)
    done = len(required) - len(missing)
    pct = 100 if not required else round(done * 100 / len(required))
    contract = step_contract(step)
    return {"step": step, "goal": contract["goal"], "required_fields": required, "missing_fields": missing, "completion_pct": pct, "ready": not missing, "validation_criteria": contract["validation_criteria"]}


def _context_field_status(session: dict[str, Any]) -> list[dict[str, Any]]:
    found = extract_fields(session_text(session))
    return [
        {"field": field, "status": "present" if found.get(field) else "missing", "question": FALLBACK_QUESTIONS.get(field, "À préciser.")}
        for field in REQUIRED_BY_STEP["activity"]
    ]


def build_client_understanding(session: dict[str, Any]) -> dict[str, Any]:
    refs = load_sector_references()
    sector_id = str(session.get("sector_id") or detect_sector(session_text(session), refs))
    context_fields = _context_field_status(session)
    present = [str(FIELD_LABELS.get(item["field"], item["field"])) for item in context_fields if item["status"] == "present"]
    missing = [str(FIELD_LABELS.get(item["field"], item["field"])) for item in context_fields if item["status"] == "missing"]
    sector_label = sector_id.replace("_", " ")
    summary = f"Voici ce que j’ai compris pour l’instant : vous semblez être dans le secteur {sector_label}."
    if present:
        summary += f" J’ai déjà ces éléments, donc je ne vous les redemande pas : {', '.join(present)}."
    if missing:
        summary += f" Est-ce que vous pouvez valider, corriger, ou compléter ces points : {', '.join(missing)} ?"
    next_step = "research" if not missing else "activity"
    return {"schema": "oa_client_understanding.v1", "sector_id": sector_id, "summary": summary, "context_fields": context_fields, "next_step": next_step}


def next_question(session: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    step = step or str(session.get("current_step") or "activity")
    refs = load_sector_references()
    sector_id = str(session.get("sector_id") or detect_sector(session_text(session), refs))
    ref = refs.get(sector_id) or refs["generic_tpe"]
    missing = missing_fields(session, step)
    auditbiz_payload: dict[str, Any] | None = None
    if sector_id == "bakery":
        try:
            enriched_session = dict(session)
            enriched_session["questions_asked"] = [
                {"question_id": item.get("auditbiz_question_id") or item.get("question_id") or item.get("id") or "", "question": item.get("question", "")}
                for item in session.get("asked_questions", [])
                if isinstance(item, dict)
            ]
            auditbiz_payload = auditbiz_choose_next_question(enriched_session, step, sector_id="bakery")
        except Exception:
            auditbiz_payload = None
    if missing:
        question = FALLBACK_QUESTIONS.get(missing[0], "Pouvez-vous préciser ce point ?")
    elif auditbiz_payload:
        question = str(auditbiz_payload.get("question") or "Pouvez-vous préciser ce point métier ?")
    else:
        block = ref.get("question_blocks", {}).get(step) or []
        asked = {m.get("question") for m in session.get("asked_questions", [])}
        question = next((q for q in block if q not in asked), f"Pour l’étape {step}, souhaitez-vous ajouter une précision métier avant validation ?")
    sector_hint = ", ".join(ref.get("important_dimensions", [])[:4])
    contract = step_contract(step)
    result = {"step": step, "sector_id": sector_id, "sector_label": sector_id.replace("_", " "), "goal": contract["goal"], "question": question, "missing_fields": missing, "completion": completion_for_step(session, step), "validation_criteria": contract["validation_criteria"], "understanding": build_client_understanding(session), "sector_hint": sector_hint}
    if auditbiz_payload and not missing:
        result["auditbiz_question"] = auditbiz_payload
        result["interaction"] = auditbiz_payload.get("interaction")
        result["options"] = auditbiz_payload.get("options", [])
        result["why"] = auditbiz_payload.get("why", "")
        result["skip_allowed"] = auditbiz_payload.get("skip_allowed", True)
        result["save_resume_allowed"] = auditbiz_payload.get("save_resume_allowed", True)
        result["feedback_prompt"] = auditbiz_payload.get("feedback_prompt", "")
    return result

def create_session(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    initial = str(payload.get("message") or payload.get("activity") or "")
    refs = load_sector_references()
    sid = f"audit-session-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
    session = {"id": sid, "schema": "oa_audit_session.v0", "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "current_step": "intro", "sector_id": detect_sector(initial, refs), "messages": [], "answers": {}, "asked_questions": [], "validated_steps": [], "safety": {"paid_actions": "none", "provisioning": "none"}}
    if initial:
        session["messages"].append({"role": "client", "text": initial, "at": session["created_at"]})
    q = next_question(session, "intro")
    session["asked_questions"].append({"step": "intro", "question": q["question"], "auditbiz_question_id": (q.get("auditbiz_question") or {}).get("id")})
    return {"session": session, "omar": q}

def add_message(session: dict[str, Any], text: str) -> dict[str, Any]:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    session.setdefault("messages", []).append({"role": "client", "text": text, "at": now})
    session["sector_id"] = detect_sector(session_text(session))
    q = next_question(session, str(session.get("current_step") or "activity"))
    session.setdefault("asked_questions", []).append({"step": q["step"], "question": q["question"], "auditbiz_question_id": (q.get("auditbiz_question") or {}).get("id")})
    return {"session": session, "omar": q}

def validate_step(session: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    step = step or str(session.get("current_step") or "activity")
    c = completion_for_step(session, step)
    if not c["ready"]:
        return {"ok": False, "error": "step_incomplete", "completion": c, "omar": next_question(session, step)}
    validated = session.setdefault("validated_steps", [])
    if step not in validated:
        validated.append(step)
    steps = list(REQUIRED_BY_STEP)
    idx = steps.index(step) if step in steps else 0
    if idx < len(steps)-1:
        session["current_step"] = steps[idx+1]
    return {"ok": True, "session": session, "completion": c, "next": next_question(session, str(session.get("current_step")))}

CONSENT_KEYS = [
    "public_web_search",
    "legal_registry_lookup",
    "social_media_lookup",
    "document_analysis",
    "market_trends_lookup",
    "anonymized_improvement",
]


def normalize_consents(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    raw = payload.get("consents") if isinstance(payload.get("consents"), dict) else payload.get("consent")
    raw = raw if isinstance(raw, dict) else {}
    permissions = {key: bool(raw.get(key, False)) for key in CONSENT_KEYS}
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "schema": "oa_audit_consent.v0",
        "permissions": permissions,
        "accepted_at": raw.get("accepted_at") or (now if any(permissions.values()) else None),
        "consent_version": str(raw.get("consent_version") or "2026-06-29.rigorous-audit.v1"),
        "notes": str(raw.get("notes") or ""),
        "required_for_external_research": ["public_web_search", "legal_registry_lookup", "social_media_lookup"],
        "improvement_opt_in": permissions["anonymized_improvement"],
    }


def _source_consent_key(label: str) -> str:
    hay = label.casefold()
    if any(token in hay for token in ["siret", "sirene", "orias", "registre", "barreau", "annuaire"]):
        return "legal_registry_lookup"
    if any(token in hay for token in ["linkedin", "instagram", "facebook", "réseaux", "reseaux", "social"]):
        return "social_media_lookup"
    if any(token in hay for token in ["macro", "marché", "marche", "insee", "ocde", "dbnomics", "tendances"]):
        return "market_trends_lookup"
    return "public_web_search"


def _source_execution_metadata(label: str, status: str) -> dict[str, Any]:
    hay = label.casefold()
    if "orias" in hay:
        return {
            "connector": "orias_manual_verification",
            "official_url": "https://www.orias.fr/home/showAdvancedSearch",
            "execution": "manual_review_link_prepared_connector_not_auto_executed" if status == "authorized" else "planned_only_no_external_call",
            "reason": "ORIAS est une source métier critique : lien officiel préparé, exécution automatique à valider séparément.",
        }
    if "barreau" in hay or "annuaire" in hay:
        return {
            "connector": "cnb_annuaire_manual_verification",
            "official_url": "https://cnb.avocat.fr/annuaire-des-avocats-de-france",
            "execution": "manual_review_link_prepared_connector_not_auto_executed" if status == "authorized" else "planned_only_no_external_call",
            "reason": "Annuaire avocat public : lien officiel préparé, pas d’automatisation tant que l’accès/API n’est pas contracté.",
        }
    if "google" in hay or "business profile" in hay:
        return {
            "connector": "google_business_manual_verification",
            "official_url": "https://www.google.com/search",
            "execution": "manual_review_link_prepared_connector_not_auto_executed" if status == "authorized" else "planned_only_no_external_call",
            "reason": "Google/Maps demande une stratégie API/conditions d’usage dédiée avant exécution automatique.",
        }
    return {"connector": "generic_public_source", "execution": "planned_only_no_external_call"}


def build_research_plan(session: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Construit un plan de recherche public, sans exécuter d'appel externe.

    Le plan sert de gate : quelles sources Omar propose, quels faits collecter,
    quelles concurrences cartographier, et quels garde-fous appliquer avant toute
    recherche personnalisée/localisée. Il ne scrape rien en V1.
    """
    payload = payload or {}
    refs = load_sector_references()
    sector_id = str(session.get("sector_id") or detect_sector(session_text(session), refs))
    ref = refs.get(sector_id) or refs["generic_tpe"]
    consent_snapshot = normalize_consents(payload)
    permissions = consent_snapshot["permissions"]
    localized = ref.get("localized_research") or {}
    sources = []
    for label in localized.get("authorized_sources", []):
        key = _source_consent_key(str(label))
        status = "authorized" if permissions.get(key) else "refused"
        meta = _source_execution_metadata(str(label), status)
        sources.append({
            "label": str(label),
            "consent_key": key,
            "status": status,
            **meta,
        })
    text = session_text(session)
    context_fields = _context_field_status(session)
    provided = {
        "company_public_name": str(payload.get("company_public_name") or payload.get("public_name") or "").strip(),
        "website": str(payload.get("website") or payload.get("site") or "").strip(),
        "siret": str(payload.get("siret") or payload.get("sirene") or "").strip(),
        "location_hint": str(payload.get("location") or "").strip(),
    }
    competitors = ref.get("competitor_mapping") or {"direct": [], "indirect": [], "questions": []}
    risk_flags = [str(x) for x in ref.get("risk_flags", [])]
    guardrails = [
        "Ne jamais utiliser de source privée, paywalled ou nécessitant un login sans validation explicite.",
        "Séparer dans le rapport : déclarations client, sources publiques vérifiées, documents fournis, hypothèses Omar.",
        "Aucun paiement, provisioning, publication ou contact tiers pendant la recherche.",
    ] + [f"Point de vigilance métier : {flag}" for flag in risk_flags[:8]]
    return {
        "schema": "oa_audit_research_plan.v1",
        "status": "planned_not_executed",
        "session_id": session.get("id"),
        "sector_id": sector_id,
        "company": provided,
        "context_fields": context_fields,
        "sources": sources,
        "facts_to_collect": localized.get("facts_to_collect", []),
        "competitors": {
            "direct": competitors.get("direct", []),
            "indirect": competitors.get("indirect", []),
            "differentiation_questions": competitors.get("questions", []),
        },
        "guardrails": guardrails,
        "consent_snapshot": consent_snapshot,
        "open_questions": [item["question"] for item in context_fields if item["status"] == "missing"],
        "safety": {
            "execute_external_calls": False,
            "paid_actions": "none",
            "provisioning": "none",
            "requires_human_validation_before_use_in_report": True,
        },
    }


def sector_deep_facets(sector_id: str, refs: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    refs = refs or load_sector_references()
    ref = refs.get(sector_id) or refs.get("generic_tpe") or {}
    facets = ref.get("deep_facets") or []
    normalized: list[dict[str, Any]] = []
    for facet in facets:
        questions = []
        for q in facet.get("questions", []) if isinstance(facet.get("questions"), list) else []:
            if not str(q.get("question") or "").strip():
                continue
            questions.append({
                "id": str(q.get("id") or "").strip(),
                "interaction": str(q.get("interaction") or "open").strip(),
                "question": str(q.get("question") or "").strip(),
                "why": str(q.get("why") or "").strip(),
                "options": [str(x) for x in q.get("options", [])] if isinstance(q.get("options"), list) else [],
                "follow_up": str(q.get("follow_up") or "").strip(),
            })
        normalized.append({
            "id": str(facet.get("id") or "").strip(),
            "label": str(facet.get("label") or "").strip(),
            "purpose": str(facet.get("purpose") or "").strip(),
            "depth": str(facet.get("depth") or "").strip(),
            "source_basis": [str(x) for x in facet.get("source_basis", [])] if isinstance(facet.get("source_basis"), list) else [],
            "questions": questions,
        })
    return [facet for facet in normalized if facet["id"] and facet["questions"]]


def recommend_micro_questions(session: dict[str, Any], step: str, *, limit: int = 5) -> list[dict[str, Any]]:
    refs = load_sector_references()
    sector_id = str(session.get("sector_id") or detect_sector(session_text(session), refs))
    facets = sector_deep_facets(sector_id, refs)
    step_focus = {
        "activity": ["production_offre", "emplacement", "savoir_faire", "finance_pilotage"],
        "research": ["emplacement", "marketing_local", "experience_client"],
        "pain": ["production_offre", "stocks_achats", "equipe", "finance_pilotage"],
        "tools": ["production_offre", "stocks_achats", "equipe", "experience_client"],
        "risk": ["reglementaire", "finance_pilotage", "experience_client"],
        "opportunities": ["ia_potentiel", "production_offre", "experience_client", "marketing_local"],
        "autonomy": ["ia_potentiel", "equipe", "savoir_faire"],
        "validation": ["finance_pilotage", "reglementaire", "ia_potentiel"],
    }
    preferred = step_focus.get(step, [])
    ordered = sorted(facets, key=lambda f: (preferred.index(f["id"]) if f["id"] in preferred else 99, f["id"]))
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for facet in ordered:
        for question in facet["questions"]:
            qid = question["id"] or question["question"][:80]
            if qid in seen:
                continue
            seen.add(qid)
            result.append({
                "id": qid,
                "sector_id": sector_id,
                "step": step,
                "facet_id": facet["id"],
                "facet_label": facet["label"],
                "interaction": question["interaction"],
                "question": question["question"],
                "why": question["why"],
                "options": question["options"],
                "follow_up": question["follow_up"],
                "skip_allowed": True,
                "save_resume_allowed": True,
                "feedback_prompt": "Cette question était-elle utile, trop loin, mal posée, ou à approfondir ?",
            })
            if len(result) >= limit:
                return result
    return result


def sector_activity_options(sector_id: str, refs: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    refs = refs or load_sector_references()
    ref = refs.get(sector_id) or refs.get("generic_tpe") or {}
    options = ref.get("activity_facets") or []
    return [
        {"id": str(item.get("id") or item.get("label") or "").strip(), "label": str(item.get("label") or "").strip(), "why": str(item.get("why") or "").strip()}
        for item in options
        if str(item.get("label") or "").strip()
    ]


def infer_location_context(address: str, sector_id: str = "generic_tpe") -> dict[str, Any]:
    """Heuristic micro-classification for audit conversation, not a geocoder.

    The output is a question aid: Omar must ask the user to validate it.
    """
    raw = str(address or "").strip()
    hay = raw.casefold()
    hyper_markers = ["69001", "69002", "75001", "75002", "75003", "75004", "vieux lille", "rue de la république", "grand place", "place bellecour", "hypercentre", "centre-ville"]
    urban_markers = ["paris", "lyon", "marseille", "lille", "bordeaux", "nantes", "toulouse", "nice", "rennes", "strasbourg", "montpellier"]
    peri_markers = ["wasquehal", "roubaix", "tourcoing", "villeneuve-d'ascq", "villeneuve d'ascq", "saint-priest", "vénissieux", "venissieux", "mérignac", "merignac"]
    rural_markers = ["hameau", "lieu-dit", "route de", "chemin rural", "village"]
    if any(m in hay for m in hyper_markers):
        density = "hypercentre"
        confidence = 0.68
    elif any(m in hay for m in peri_markers):
        density = "périurbain"
        confidence = 0.62
    elif any(m in hay for m in urban_markers):
        density = "urbain"
        confidence = 0.58
    elif any(m in hay for m in rural_markers):
        density = "rural"
        confidence = 0.55
    else:
        density = "à valider"
        confidence = 0.35
    sector_implications = {
        "bakery": {
            "hypercentre": ["passage piéton et achats d’impulsion", "rush matin/midi", "concurrence immédiate forte"],
            "urbain": ["clients de quartier", "avis Google et horaires visibles", "livraison ou commandes locales à évaluer"],
            "périurbain": ["trajets domicile-travail et accès voiture", "parking/horaires plus importants", "commandes famille et week-end à valider"],
            "rural": ["fidélité locale et zone de chalandise large", "horaires et services de proximité", "commandes spéciales à anticiper"],
            "à valider": ["zone réelle à confirmer avec le client avant conclusion"],
        }
    }
    implications = sector_implications.get(sector_id, {}).get(density) or ["contexte local à valider avant recommandation"]
    return {
        "schema": "oa_location_context.v0",
        "address": raw,
        "sector_id": sector_id,
        "density": density,
        "confidence": confidence,
        "business_implications": implications,
        "validation_prompt": f"À partir de l’adresse, je classerais plutôt cette zone comme {density}. Est-ce que vous validez, ou faut-il corriger ?",
    }


def build_public_research_result(plan: dict[str, Any], fetched_pages: list[dict[str, Any]] | None = None, registry_records: list[dict[str, Any]] | None = None, *, external_calls_attempted: bool | None = None) -> dict[str, Any]:
    """Transforme des sources publiques autorisées en faits prudents avec provenance.

    Cette fonction ne fait pas le réseau. Elle normalise ce que le serveur a pu
    récupérer après consentement et garde les sources non exécutées visibles.
    """
    fetched_pages = fetched_pages or []
    registry_records = registry_records or []
    authorized_labels = [s for s in plan.get("sources", []) if s.get("status") == "authorized"]
    refused_labels = [s for s in plan.get("sources", []) if s.get("status") != "authorized"]
    facts: list[dict[str, Any]] = []
    for page in fetched_pages:
        title = str(page.get("title") or "").strip()
        text = re.sub(r"\s+", " ", str(page.get("text") or "")).strip()
        url = str(page.get("url") or "").strip()
        if title:
            facts.append({"type": "public_page_title", "value": title[:240], "source_url": url, "provenance": "public_web_authorized", "confidence": 0.7})
        if text:
            facts.append({"type": "public_page_excerpt", "value": text[:360], "source_url": url, "provenance": "public_web_authorized", "confidence": 0.65})
    for record in registry_records:
        source = str(record.get("source") or "registre public").strip()
        name = str(record.get("name") or "").strip()
        siren = str(record.get("siren") or "").strip()
        siret = str(record.get("siret") or "").strip()
        activity = str(record.get("activity") or "").strip()
        city = str(record.get("city") or "").strip()
        address = str(record.get("address") or "").strip()
        financial_summary = str(record.get("financial_summary") or "").strip()
        pieces = [p for p in [name, address, activity, city, financial_summary] if p]
        location_context = infer_location_context(address or city, str(plan.get("sector_id") or "generic_tpe")) if (address or city) else None
        if pieces:
            value = " — ".join(pieces)[:420]
            facts.append({
                "type": "legal_registry_record",
                "value": value,
                "source_url": record.get("url") or source,
                "provenance": "legal_registry_authorized",
                "confidence": 0.82,
                "validation_prompt": f"Voici les informations publiques que j’ai récupérées : {value}. Est-ce que vous validez, souhaitez-vous modifier, ou est-ce que ce n’est pas vous ?",
                "metadata": {"siren": siren, "siret": siret, "display_priority": ["name", "address", "activity", "city", "financial_summary"], "location_context": location_context},
            })
    not_executed = []
    for source in refused_labels:
        not_executed.append({"label": source.get("label"), "reason": "consent_missing_or_refused", "consent_key": source.get("consent_key"), "official_url": source.get("official_url")})
    if not fetched_pages:
        for source in authorized_labels:
            if source.get("consent_key") == "public_web_search":
                not_executed.append({"label": source.get("label"), "reason": "not_fetched_yet", "consent_key": source.get("consent_key")})
    if not registry_records:
        for source in authorized_labels:
            if source.get("consent_key") == "legal_registry_lookup":
                specialized = str(source.get("connector") or "").endswith("manual_verification")
                not_executed.append({
                    "label": source.get("label"),
                    "reason": "specialized_connector_not_auto_executed" if specialized else "not_fetched_yet",
                    "consent_key": source.get("consent_key"),
                    "official_url": source.get("official_url"),
                })
    specialized_skipped = {
        item.get("label") for item in not_executed if item.get("reason") == "specialized_connector_not_auto_executed"
    }
    for source in authorized_labels:
        specialized = str(source.get("connector") or "").endswith("manual_verification")
        if specialized and source.get("label") not in specialized_skipped:
            not_executed.append({
                "label": source.get("label"),
                "reason": "specialized_connector_not_auto_executed",
                "consent_key": source.get("consent_key"),
                "official_url": source.get("official_url"),
            })
    status = "partial" if facts and not_executed else "complete" if facts else "not_started"
    attempted = bool(fetched_pages or registry_records) if external_calls_attempted is None else bool(external_calls_attempted)
    return {
        "schema": "oa_public_research_result.v1",
        "status": status,
        "sector_id": plan.get("sector_id"),
        "company": plan.get("company", {}),
        "facts": facts,
        "activity_options": sector_activity_options(str(plan.get("sector_id") or "generic_tpe")),
        "not_executed": not_executed,
        "competitors_to_check": plan.get("competitors", {}),
        "guardrails": plan.get("guardrails", []),
        "safety": {
            "external_calls_attempted": attempted,
            "sources_require_human_validation": True,
            "facts_are_not_client_claims": True,
        },
    }


def build_sources_used(payload: dict[str, Any], session: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    answer_fields = ["activity", "urgency", "repetitive_tasks", "current_tools", "constraints", "opportunities", "autonomy", "validation"]
    if payload.get("transcript") or (session or {}).get("messages") or any(str(payload.get(k) or "").strip() for k in answer_fields):
        sources.append({"type": "user_answer", "label": "Réponses conversationnelles du client", "provenance": "declared_by_user"})
    docs = payload.get("uploaded_documents") if isinstance(payload.get("uploaded_documents"), list) else []
    if docs:
        sources.append({"type": "uploaded_document", "label": f"{len(docs)} document(s) fourni(s)", "provenance": "user_upload"})
    consents = normalize_consents(payload)["permissions"]
    if consents.get("public_web_search"):
        sources.append({"type": "public_web_authorized", "label": "Recherche web publique autorisée, non exécutée en V0 déterministe", "provenance": "consent"})
    if consents.get("legal_registry_lookup"):
        sources.append({"type": "legal_registry_authorized", "label": "Données légales publiques autorisées, non exécutées en V0 déterministe", "provenance": "consent"})
    if consents.get("social_media_lookup"):
        sources.append({"type": "social_media_authorized", "label": "Réseaux sociaux publics autorisés, non exécutés en V0 déterministe", "provenance": "consent"})
    sources.append({"type": "sector_reference", "label": str(payload.get("sector_id") or "generic_tpe"), "provenance": "oa_sector_reference"})
    return sources


def _contains_any(text: str, needles: list[str]) -> bool:
    hay = (text or "").casefold()
    return any(n.casefold() in hay for n in needles)


def build_devis_source(payload: dict[str, Any], report: dict[str, Any], consents: dict[str, Any] | None = None) -> dict[str, Any]:
    consents = consents or normalize_consents(payload)
    text = "\n".join(str(payload.get(k) or "") for k in ["activity", "urgency", "repetitive_tasks", "current_tools", "constraints", "opportunities", "autonomy", "validation"])
    recommendations: list[dict[str, Any]] = []
    def add(catalog_id: str, reason: str, *, confidence: float = 0.7, required: bool = True) -> None:
        if catalog_id not in [r["catalog_id"] for r in recommendations]:
            recommendations.append({"catalog_id": catalog_id, "required": required, "reason": reason, "evidence": "user_answers_and_sector_reference", "confidence": confidence})
    if _contains_any(text, ["multi", "équipe", "crm", "connecteur", "automatisation", "plusieurs"]):
        add("formule-pro", "Besoin probable de plusieurs boucles, suivi client ou connecteurs : formule Pro à valider humainement.", confidence=0.62)
    else:
        add("formule-starter", "Première version utile et bornée : agent IA accompagné sans sur-automatisation initiale.", confidence=0.74)
    add("presta-onboarding", "Sécuriser le démarrage : cadrage, limites, données à ne pas exposer, premiers tests et validation humaine.", confidence=0.78)
    if _contains_any(text, ["réseaux", "instagram", "facebook", "linkedin", "site", "google", "avis", "présence"]):
        add("mod-presence", "Présence publique, contenus ou avis identifiés comme levier d’amélioration.", confidence=0.66, required=False)
    if _contains_any(text, ["devis", "facture", "document", "paperasse", "contrat", "relance", "email", "whatsapp"]):
        add("mod-paperasse", "Documents, messages ou relances récurrents détectés : module paperasse à chiffrer.", confidence=0.72, required=False)
    if _contains_any(text, ["client", "crm", "suivi", "prospect", "pipeline", "commande"]):
        add("mod-crm", "Besoin de suivi client/prospect ou historique de demandes à structurer.", confidence=0.61, required=False)
    missing_consent = [k for k in ["public_web_search", "legal_registry_lookup", "market_trends_lookup"] if not consents.get("permissions", {}).get(k)]
    return {
        "schema": "oa_devis_source.v0",
        "status": "ready_for_user_validation",
        "audit_id": payload.get("audit_id"),
        "recommended_items": recommendations,
        "decision_basis": ["réponses du client", "référentiel sectoriel OA", "contraintes/risques déclarés", "documents fournis si autorisés"],
        "not_used_without_consent": missing_consent,
        "limits": report.get("limits", []),
        "governance": {
            "requires_user_validation_before_checkout": True,
            "requires_human_review_before_provisioning": True,
            "deletion_available": True,
            "rgpd_basis": "consentement explicite + mesures précontractuelles",
            "retention_default": "90 jours sans achat, puis suppression ou anonymisation si opt-in",
        },
        "explainability": {
            "facts_vs_hypotheses": "Les recommandations sont des hypothèses commerciales justifiées, à valider par le client avant paiement.",
            "confidence_overall": round(sum(r["confidence"] for r in recommendations) / max(1, len(recommendations)), 2),
        },
    }


def build_exports(audit: dict[str, Any]) -> dict[str, Any]:
    report = audit.get("report") or {}
    title = report.get("title", "Rapport audit IA")
    lines = [f"# {title}", "", report.get("summary", "")]
    for key, label in [("diagnostic","Diagnostic"),("opportunities","Opportunités"),("limits","Limites"),("tutorial","Tutoriel"),("prompts","Prompts"),("decisions","Décisions"),("next_steps","Plan d’action")]:
        items = report.get(key) or []
        lines += ["", f"## {label}"] + [f"- {item}" for item in items]
    if audit.get("devis_source"):
        lines += ["", "## Devis source", json.dumps(audit["devis_source"], ensure_ascii=False, indent=2)]
    md = "\n".join(lines).strip()+"\n"
    social = f"Je viens de réaliser un audit IA Omar & Alex : {report.get('summary','premiers enjeux IA clarifiés')[:220]}\n\nObjectif : identifier les vrais usages utiles, les limites et les prochaines étapes avant d’automatiser."
    return {"markdown": md, "pdf_status": "pending_renderer", "linkedin_text": social, "share_text": social, "email_subject": title}
