from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

from audit_telemetry import append_telemetry_event, make_button_displayed, make_session_created, make_step_validated
from auditbiz_question_engine import choose_next_question as auditbiz_choose_next_question

ROOT = Path(__file__).resolve().parents[1]
SECTORS_DIR = ROOT / "data" / "audit_sectors"
REQUIRED_SECTOR_FIELDS = {"sector_id", "labels", "important_dimensions", "question_blocks", "risk_flags", "benchmarks"}

FIELD_LABELS = {
        "business_activity": "métier exact",
    "location": "localisation / zone servie",
    "company_size": "taille d’équipe",
    "company_age": "ancienneté",
    "customer_type": "type de clients",
    "sales_channel": "façon de vendre",
    "public_research_scope": "sources publiques autorisées ou refusées",
    "repetitive_tasks": "semaine réelle / irritants",
    "time_spent": "fréquence ou volume concerné",
    "tools": "outils et canaux actuels",
    "flow_breaks": "ruptures de flux / double saisie",
    "sensitive_data": "données ou décisions sensibles",
    "human_validation": "validations humaines obligatoires",
    "opportunity_choice": "opportunités validées",
    "autonomy_profile": "profil d’autonomie",
    "synthesis_validation": "synthèse validée ou corrigée",
}

FIELD_PATTERNS = {
    "business_activity": [r"\b(boulanger|boulangerie|fournée|fournee|p[âa]tissier|p[âa]tissi[èe]re|p[âa]tisserie|restaurant|plombier|chauffagiste|rénovation|renovation|électricien|electricien|fleuriste|avocat|patrimoine|marketing|secr[ée]taire|traducteur|traductrice|traduction|freelance|consultant|consultante|coach|formateur|formatrice|commerce|boutique)\b", r"je suis", r"nous sommes", r"mon activité", r"mon métier"],
    "location": [r"\b(à|a|près de|pres de)\s+[A-ZÉÈÀÂÎÔÛa-zéèàâêîôûç-]{2,}", r"\b\d{1,4}\s+(rue|avenue|av\.?|boulevard|bd|chemin|route|place|impasse)\b", r"\b\d{5}\s+[A-ZÉÈÀÂÎÔÛa-zéèàâêîôûç-]{2,}", r"\b(lille|paris|lyon|marseille|bordeaux|nantes|toulouse|nice|clichy|roubaix|orly)\b"],
    "company_size": [r"\b\d+\s*(personnes?|salari[ée]s?|collaborateurs?|associ[ée]s?|employ[ée]s?)\b", r"\bsolo\b", r"\bind[ée]pendant\b", r"\béquipe\b"],
    "company_age": [r"\b\d+\s*(ans?|ann[ée]es?)\b", r"cré[ée]e?\s+il y a", r"reprise", r"\blanc[ée]e?\b", r"\blancement\b", r"depuis\s+\d+", r"moins d.un an", r"plus de 10 ans"],
    "customer_type": [r"\b(particuliers?|pros?|professionnels?|entreprises?|b2b|b2c|clients? finaux|pme|ind[ée]pendants?)\b"],
    "sales_channel": [r"\b(boutique|magasin|atelier|en ligne|site|e-commerce|marketplace|t[ée]l[ée]phone|email|mail|whatsapp|réseau|reseau|recommandations?|bouche[- ]à[- ]oreille|devis|appel d.offres|plateformes?)\b"],
    "public_research_scope": [r"\b(site|www\.|https?://|siret|sirene|google business|fiche google|linkedin|instagram|facebook|avis|autorise|refuse|sources? publiques?)\b"],
    "repetitive_tasks": [r"\b(semaine|relances?|devis|emails?|r[ée]ponses?|planning|rendez-vous|factures?|posts?|commandes?|appels?|whatsapp|paperasse|temps|soir[ée]es?)\b"],
    "time_spent": [r"\b\d+\s*(h|heures?|jours?|soir[ée]es?)\b", r"par semaine", r"par jour", r"souvent", r"toujours"],
    "tools": [r"\b(email|excel|whatsapp|agenda|google|drive|crm|notion|facturation|t[ée]l[ée]phone|cahier|tableur)\b"],
    "flow_breaks": [r"\b(double saisie|ressais|copie|coll[eé]|perd|oubli|manuel|entre deux outils|rupture)\b"],
    "sensitive_data": [r"\b(donn[ée]es?|confidentiel|secret|prix|factures?|paiement|allerg[èe]nes?|juridique|financi[èe]res?|sant[ée]|mineurs?)\b"],
    "human_validation": [r"validation humaine", r"valider", r"je valide", r"jamais automatiquement", r"avant publication", r"avant envoi", r"tout valider"],
    "opportunity_choice": [r"\b(oui|corriger|pas intéressé|priorit|urgent|opportunit|première boucle|premiere boucle|rêve|reve)\b"],
    "autonomy_profile": [r"\b(apprendre|d[ée]l[ée]guer|mixte|telegram|whatsapp|sms|mail|valide tout|supervise)\b"],
    "synthesis_validation": [r"\b(c'est ça|c’est ça|valid|corrige|corriger|retirer|ok pour le rapport|rapport)\b"],
}

FABLE_ACTS = {
    "rencontre": {"label": "Rencontre", "steps": ["intro", "activity"]},
    "plongee": {"label": "Plongée", "steps": ["real_week", "tools", "data_limits", "opportunities"]},
    "livraison": {"label": "Livraison", "steps": ["synthesis_card", "report"]},
}

STEP_ALIASES = {
    "welcome_pact": "intro",
    "research": "activity",  # V0 : sources simplifiées dans Rencontre, pas acte séparé.
    "pain": "real_week",
    "risk": "data_limits",
    "autonomy": "opportunities",  # V0 : autonomie intégrée à opportunités/synthèse.
    "validation": "synthesis_card",
}

REQUIRED_BY_STEP = {
    "intro": [],
    "activity": ["business_activity", "company_size", "company_age", "customer_type", "sales_channel", "location"],
    "real_week": ["repetitive_tasks", "time_spent"],
    "tools": ["tools"],
    "data_limits": ["sensitive_data", "human_validation"],
    "opportunities": ["opportunity_choice"],
    "synthesis_card": ["synthesis_validation"],
    "report": [],
}

FALLBACK_QUESTIONS = {
    "communication_preferences": "Bonjour, je suis Omar, un agent formé par Alexandre Willemetz et biberonné sur les meilleurs standard en gestion et en informatique. Je vais vous poser des questions. Vous me répondez à votre rythme et selon vos objectifs. A la fin vous pourriez télécharger votre Audit Business & Tech.",
    "business_activity": "Pour commencer, quel est votre métier exact ? Si vous hésitez, choisissez le plus proche puis corrigez en une phrase.",
    "location": "Vous intervenez où, concrètement ? Ville, quartier, zone ou rayon suffisent.",
    "company_size": "Vous êtes combien à travailler dans l’activité aujourd’hui ?",
    "company_age": "Depuis combien de temps l’activité existe ? Une approximation suffit.",
    "customer_type": "Vos clients sont plutôt des particuliers, des professionnels, ou un mélange des deux ?",
    "sales_channel": "Comment les clients arrivent et achètent aujourd’hui : boutique, site, téléphone, email, recommandations, plateformes ?",
    "public_research_scope": "Si vous avez un site ou une fiche Google, donnez-moi le lien ou refusez simplement. Je n’utilise que ce que vous autorisez.",
    "repetitive_tasks": "Racontez-moi votre semaine dernière — la vraie. Qu’est-ce qui vous a pris du temps inutilement ?",
    "time_spent": "Parmi ces irritants, lequel est prioritaire pour commencer, et quel ordre de grandeur cela prend par semaine ? Plusieurs irritants sont possibles ; on choisit seulement le premier à traiter.",
    "tools": "Qu’utilisez-vous aujourd’hui — même si c’est juste téléphone, WhatsApp, cahier ou Excel ?",
    "flow_breaks": "Ce que vous ressaisissez deux fois, ou recopiez d’un outil à l’autre, c’est quoi ?",
    "sensitive_data": "Qu’est-ce qui ne doit jamais sortir ou être automatisé : données clients, santé, prix, paiements, juridique ?",
    "human_validation": "Un message vers un client : l’agent peut envoyer seul, ou vous voulez tout valider au début ?",
    "opportunity_choice": "Voilà ce que je vois pour vous. Dites-moi si je vise juste, ou corrigez-moi.",
    "autonomy_profile": "Vous voulez plutôt apprendre, déléguer, ou un peu des deux ?",
    "synthesis_validation": "Avant votre rapport, vérifiez-moi. Corrigez tout ce qui cloche — c’est votre réalité qui compte.",
}

STEP_CONTRACTS = {
    "intro": {
        "act": "rencontre",
        "interaction": "quick_replies",
        "options": ["En savoir plus sur cet Audit.", "On commence !"],
        "goal": "Poser le pacte : audit gratuit, rythme client, rapport téléchargeable, vouvoiement par défaut.",
        "validation_criteria": ["Pacte présenté", "Vouvoiement imposé", "Aucun engagement ni action payante"],
    },
    "activity": {
        "act": "rencontre",
        "interaction": "quick_replies",
        "options": [],
        "goal": "Comprendre le vrai métier, la taille, l'ancienneté, les clients, les canaux de vente et la zone sans formulaire rigide.",
        "validation_criteria": ["Métier compris", "Taille approximative comprise", "Ancienneté comprise", "Type de clients compris", "Canal de vente compris", "Localisation / zone comprise"],
    },
    "real_week": {
        "act": "plongee",
        "interaction": "free_text",
        "options": [],
        "goal": "Faire émerger les irritants réels, leur poids temporel et émotionnel.",
        "validation_criteria": ["Deux irritants ou un irritant fort", "Volume ou fréquence estimé", "Priorité client détectée"],
    },
    "tools": {
        "act": "plongee",
        "interaction": "quick_replies",
        "options": ["WhatsApp", "Email", "Téléphone", "Excel", "Agenda", "Cahier", "Autre"],
        "goal": "Cartographier les outils et les ruptures entre eux.",
        "validation_criteria": ["Au moins un outil", "Rupture ou absence de rupture explicitée"],
    },
    "data_limits": {
        "act": "plongee",
        "interaction": "quick_replies",
        "options": ["Je valide tout au début", "Il prépare, j’envoie", "Rien de sensible", "Prix/paiement", "Données clients", "Allergènes/santé"],
        "goal": "Fixer les lignes rouges et les validations humaines.",
        "validation_criteria": ["Données sensibles identifiées", "Gates humaines définies"],
    },
    "opportunities": {
        "act": "plongee",
        "interaction": "validation_card",
        "options": ["Oui", "À corriger", "Pas maintenant", "Autre priorité"],
        "goal": "Proposer 3 opportunités en mots client, puis prioriser sans forcing.",
        "validation_criteria": ["Une opportunité validée ou corrigée", "Priorité client claire"],
    },
    "synthesis_card": {
        "act": "livraison",
        "interaction": "validation_card",
        "options": ["C’est ça", "À corriger", "Retirer", "OK pour le rapport"],
        "goal": "Faire valider la carte “Ce qu’Omar a compris”, source canonique du rapport et de l’agent.",
        "validation_criteria": ["Carte validée ou corrigée", "Rapport autorisé"],
    },
    "report": {
        "act": "livraison",
        "interaction": "quick_replies",
        "options": ["Chiffrer ça", "Parler à Alex", "Digérer d’abord", "Démarrer l’agent en dry-run"],
        "goal": "Livrer le rapport et proposer les suites sans pression.",
        "validation_criteria": ["Rapport généré", "Aucune action payante sans GO humain"],
    },
}


def normalize_step_id(step: str | None) -> str:
    raw = str(step or "intro").strip()
    return STEP_ALIASES.get(raw, raw if raw in REQUIRED_BY_STEP else "intro")


def fable_step_order() -> list[str]:
    return list(REQUIRED_BY_STEP.keys())


def step_contract(step: str) -> dict[str, Any]:
    normalized = normalize_step_id(step)
    base = STEP_CONTRACTS.get(normalized, {"goal": "Clarifier cette étape.", "validation_criteria": ["Réponse concrète fournie."], "act": "rencontre", "interaction": "free_text", "options": []})
    return {**base, "step": normalized, "act_label": FABLE_ACTS.get(base.get("act", "rencontre"), {}).get("label", "Rencontre")}

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
    step = normalize_step_id(step)
    found = extract_fields(session_text(session))
    answers = session.get("answers") or {}
    return [f for f in REQUIRED_BY_STEP.get(step, []) if not (found.get(f) or str(answers.get(f) or "").strip())]

def completion_for_step(session: dict[str, Any], step: str) -> dict[str, Any]:
    step = normalize_step_id(step)
    required = REQUIRED_BY_STEP.get(step, [])
    missing = missing_fields(session, step)
    done = len(required) - len(missing)
    pct = 100 if not required else round(done * 100 / len(required))
    contract = step_contract(step)
    return {"step": step, "act": contract.get("act"), "act_label": contract.get("act_label"), "goal": contract["goal"], "required_fields": required, "missing_fields": missing, "completion_pct": pct, "ready": not missing, "validation_criteria": contract["validation_criteria"]}


def _context_field_status(session: dict[str, Any]) -> list[dict[str, Any]]:
    missing = set(missing_fields(session, "activity"))
    return [
        {"field": field, "status": "missing" if field in missing else "present", "question": FALLBACK_QUESTIONS.get(field, "À préciser.")}
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



def current_act_for_step(step: str) -> str:
    step = normalize_step_id(step)
    for act_id, act in FABLE_ACTS.items():
        if step in act["steps"]:
            return act_id
    return "rencontre"


def act_metrics(session: dict[str, Any]) -> dict[str, Any]:
    validated = set(session.get("validated_steps", []) or [])
    metrics = {}
    for act_id, act in FABLE_ACTS.items():
        steps = act["steps"]
        done = len([s for s in steps if s in validated])
        metrics[act_id] = {
            "label": act["label"],
            "steps": steps,
            "completed_steps": done,
            "total_steps": len(steps),
            "completion_pct": round(done * 100 / max(1, len(steps))),
            "current": normalize_step_id(session.get("current_step")) in steps,
        }
    return metrics


def _last_user_text(session: dict[str, Any], *, max_len: int = 220) -> str:
    for msg in reversed(session.get("messages", []) or []):
        if msg.get("role") == "client" and str(msg.get("text") or "").strip():
            text = re.sub(r"\s+", " ", str(msg.get("text"))).strip()
            return text[:max_len]
    return "À compléter avec vos réponses."


def _last_client_messages(session: dict[str, Any], *, limit: int = 2) -> list[dict[str, Any]]:
    out = []
    for msg in reversed(session.get("messages", []) or []):
        if msg.get("role") == "client":
            out.append(msg)
            if len(out) >= limit:
                break
    return out


def build_synthesis_card(session: dict[str, Any]) -> dict[str, Any]:
    text = session_text(session)
    sector_id = str(session.get("sector_id") or detect_sector(text))
    fields = extract_fields(text)
    source_status = "Sources publiques autorisées/refusées à confirmer en V0" if fields.get("public_research_scope") else "Aucune source publique utilisée sans accord explicite."
    sections = [
        {"id": "activity", "label": "Activité", "kind": "declared", "summary": _last_user_text(session) if fields.get("business_activity") else "Métier, zone et taille à confirmer."},
        {"id": "sources", "label": "Sources", "kind": "verified", "summary": source_status},
        {"id": "pain", "label": "Irritants", "kind": "declared", "summary": "Irritants et charge réelle repérés dans la conversation." if fields.get("repetitive_tasks") else "Semaine réelle encore à préciser."},
        {"id": "tools", "label": "Outils", "kind": "declared", "summary": "Outils/canaux actuels mentionnés." if fields.get("tools") else "Outils actuels à confirmer."},
        {"id": "limits", "label": "Lignes rouges", "kind": "declared", "summary": "Validation humaine et données sensibles cadrées." if (fields.get("sensitive_data") or fields.get("human_validation")) else "Lignes rouges à poser avant toute automatisation."},
        {"id": "opportunities", "label": "Opportunités", "kind": "hypothesis", "summary": "Première boucle IA candidate à valider." if fields.get("opportunity_choice") else "Opportunités encore hypothétiques."},
    ]
    return {"schema": "oa_fable_synthesis_card.v0", "title": "Ce qu’Omar a compris", "sector_id": sector_id, "sections": sections, "actions": ["C’est ça", "À corriger", "Retirer", "OK pour le rapport"]}



def _short_list(value: str, *, fallback: str) -> list[str]:
    items = [re.sub(r"\s+", " ", part).strip(" -•\t") for part in re.split(r"[\n;,]+", value or "")]
    items = [item for item in items if item]
    return items or [fallback]

def build_onboarding_pack_v1(payload: dict[str, Any], report: dict[str, Any], session: dict[str, Any] | None = None) -> dict[str, Any]:
    text = "\n".join(str(payload.get(k) or "") for k in ["activity", "repetitive_tasks", "current_tools", "constraints", "opportunities", "autonomy", "validation"])
    sector_id = str(payload.get("sector_id") or (session or {}).get("sector_id") or detect_sector(text))
    forbidden = _short_list(str(payload.get("constraints") or ""), fallback="Validation humaine avant toute action externe sensible.")[:5]
    missions = (report.get("opportunities") or [])[:3]
    return {
        "schema": "onboarding_pack.v1",
        "status": "draft_from_audit",
        "source": "appomar.audit.fable_v0",
        "sector_id": sector_id,
        "persona": {"name": f"Agent Omar — {sector_id.replace('_', ' ')}", "tone": "vouvoiement, direct, clair, prudent"},
        "mission": missions,
        "channels": [c for c in ["Telegram" if "telegram" in text.casefold() else None, "WhatsApp" if "whatsapp" in text.casefold() else None, "Email" if "email" in text.casefold() or "mail" in text.casefold() else None] if c] or ["à choisir"],
        "connectors_candidates": _short_list(str(payload.get("current_tools") or ""), fallback="À confirmer")[:6],
        "forbidden_data": forbidden,
        "human_gates": ["GO humain avant paiement/provisioning", "Validation client avant envoi externe", *forbidden[:3]],
        "initial_routines": missions[:3],
        "prompts": report.get("prompts", [])[:5],
        "dry_run_contract": {"schema": "omartop.provisioning-contract.v1", "mode": "dry-run", "status": "pending_go", "paid_actions": "none", "go_humain": {"required": True, "provided": False}},
    }


def enforce_vouvoiement_text(text: str) -> str:
    """Best-effort guardrail: audit public uses vouvoiement only."""
    replacements = [
        ("Raconte-moi ton ", "Racontez-moi votre "),
        ("Raconte-moi ta ", "Racontez-moi votre "),
        ("raconte-moi ton ", "racontez-moi votre "),
        ("raconte-moi ta ", "racontez-moi votre "),
        ("Tu ", "Vous "),
        ("tu ", "vous "),
        (" t’", " vous "),
        (" t'", " vous "),
        (" te ", " vous "),
        (" ton ", " votre "),
        (" ta ", " votre "),
        (" tes ", " vos "),
        (" toi", " vous"),
        ("Toi", "Vous"),
        ("Ton ", "Votre "),
        ("Ta ", "Votre "),
        ("Tes ", "Vos "),
        ("c’est ta réalité", "c’est votre réalité"),
        ("C’est ta réalité", "C’est votre réalité"),
        ("vous fais", "vous faites"),
        ("vous veux", "vous voulez"),
        ("vous aimerais", "vous aimeriez"),
        ("vous utilises", "vous utilisez"),
        ("vous ressaisis ", "vous ressaisissez "),
        ("vous aurais", "vous auriez"),
        ("vous as", "vous avez"),
    ]
    out = str(text or "")
    for old, new in replacements:
        out = out.replace(old, new)
    return out


HELP_PATTERNS = [
    r"\bje ne sais pas\b",
    r"\bje sais pas\b",
    r"\baucune id[ée]e\b",
    r"\baidez[- ]?moi\b",
    r"\btu peux m.aider\b",
    r"\bvous pouvez m.aider\b",
    r"\bpas compris\b",
]

CLARIFY_PATTERNS = [
    r"\bheu\b",
    r"\bquoi\b",
    r"\bcomment ça\b",
    r"\bje ne comprends pas\b",
    r"\bj.ai pas compris\b",
    r"\bpas clair\b",
]

PRECISION_PLACEHOLDERS = {
    "Je précise",
    "Autre",
    "Autre métier",
    "Je ne sais pas encore",
    "Montrez-moi des exemples",
}

FIELD_EXPLANATIONS = {
    "business_activity": "Je cherche juste le métier réel, pas une catégorie parfaite. Exemple : boulangerie-pâtisserie, salon de coiffure, artisan bâtiment, restaurant italien, cabinet d’avocat.",
    "company_size": "Je cherche l’ordre de grandeur de l’équipe qui fait tourner l’activité : solo, 2-5, 6-20, ou plus. Une estimation suffit.",
    "company_age": "Je cherche l’ancienneté approximative, parce qu’une activité lancée cette année n’a pas les mêmes priorités qu’une maison installée depuis 10 ans.",
    "customer_type": "Je veux savoir pour qui vous travaillez vraiment : particuliers, professionnels, ou les deux. Ça change les opportunités utiles.",
    "sales_channel": "Je cherche le chemin d’arrivée des clients : boutique, téléphone, email, site, WhatsApp, recommandations, plateformes. Plusieurs réponses sont possibles.",
    "location": "Je cherche votre zone réelle : adresse, ville, quartier, rayon d’intervention, région, France entière ou à distance. Une adresse complète marche aussi.",
    "repetitive_tasks": "Je cherche ce qui vous mange du temps dans une vraie semaine : commandes, appels, devis, relances, messages, planning, factures, recherche d’infos, suivi client. Vous pouvez en citer plusieurs.",
    "time_spent": "Je cherche un ordre de grandeur et une priorité : tous les jours, chaque semaine, 1-2 h, 3-5 h, ou plus. Si vous avez plusieurs sujets, dites lequel traiter en premier.",
}


def classify_user_intent(text: str, expected_field: str | None = None) -> str:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw:
        return "empty"
    if raw in PRECISION_PLACEHOLDERS:
        return "precision"
    if expected_field == "time_spent" and raw in FIELD_OPTIONS.get("time_spent", []):
        return "answer"
    hay = raw.casefold()
    if any(re.search(pattern, hay, re.I) for pattern in HELP_PATTERNS):
        return "help"
    if any(re.search(pattern, hay, re.I) for pattern in CLARIFY_PATTERNS):
        return "clarify"
    if expected_field == "intro" and "en savoir plus" in hay:
        return "more_info"
    return "answer"


def is_answer_like(text: str, expected_field: str | None = None) -> bool:
    return classify_user_intent(text, expected_field) == "answer"


FIELD_OPTIONS = {
    "business_activity": ["Boulangerie / pâtisserie", "Commerce / boutique", "Restaurant / food", "Artisan bâtiment", "Cabinet / profession réglementée", "Autre métier"],
    "company_size": ["Solo", "2-5", "6-20", "20+", "Je précise"],
    "company_age": ["Moins d’un an", "1-3 ans", "4-10 ans", "Plus de 10 ans", "Reprise / transmission"],
    "customer_type": ["Particuliers", "Professionnels", "Les deux", "Je ne sais pas encore"],
    "sales_channel": ["Boutique / lieu physique", "Site ou formulaire", "Téléphone", "Email", "WhatsApp / SMS", "Recommandations", "Plateformes"],
    "location": ["Paris", "Île-de-France", "France entière", "À distance", "Je précise"],
    "repetitive_tasks": ["Commandes / demandes clients", "Devis / propositions", "Relances clients", "Emails / messages", "Factures / administratif", "Planning / rendez-vous", "Plusieurs sujets / je précise"],
    "time_spent": ["Tous les jours", "Chaque semaine", "1-2 h/semaine", "3-5 h/semaine", "Plus de 5 h/semaine", "Je ne sais pas"],
}

HELP_QUESTIONS = {
    "business_activity": "Je vous aide. Dites simplement votre métier comme sur une carte de visite. Exemples : boulangerie-pâtisserie, plombier, cabinet d’avocat, boutique en ligne, cabinet de conseil.",
    "company_size": "Pas besoin d'être précis : êtes-vous solo, 2 à 5, 6 à 20, ou plus ?",
    "company_age": "Une approximation suffit : activité lancée récemment, 1-3 ans, 4-10 ans, plus ancien, ou reprise ?",
    "customer_type": "Pensez à vos derniers clients : plutôt particuliers, professionnels, ou les deux ?",
    "sales_channel": "Pensez au dernier client signé : il est venu par recommandation, téléphone, email, boutique, site, plateforme, réseau ?",
    "location": "Indiquez seulement votre zone utile : ville, région, France entière, ou à distance.",
    "repetitive_tasks": "Je vous propose des pistes. La semaine dernière, est-ce que vous avez perdu du temps sur commandes, appels, devis/propositions, relances, emails, factures, planning, recherche d'informations, ou suivi client ? Vous pouvez en citer plusieurs.",
    "time_spent": "Même à la louche : tous les jours, chaque semaine, 1-2 h, 3-5 h, ou plus de 5 h par semaine ? Si plusieurs sujets ressortent, choisissez le premier à traiter.",
}

CONTEXTUAL_ANSWERS = {
    "Solo": "Je travaille solo.",
    "2-5": "Nous sommes 2 à 5 personnes.",
    "6-20": "Nous sommes 6 à 20 personnes.",
    "20+": "Nous sommes plus de 20 personnes.",
    "Moins d’un an": "L'activité existe depuis moins d'un an.",
    "1-3 ans": "L'activité existe depuis 1 à 3 ans.",
    "4-10 ans": "L'activité existe depuis 4 à 10 ans.",
    "Plus de 10 ans": "L'activité existe depuis plus de 10 ans.",
    "Reprise / transmission": "L'activité est une reprise ou une transmission.",
    "Particuliers": "Mes clients sont surtout des particuliers.",
    "Professionnels": "Mes clients sont surtout des professionnels.",
    "Les deux": "Mes clients sont à la fois des particuliers et des professionnels.",
    "Boutique / lieu physique": "Les clients achètent en boutique ou dans un lieu physique.",
    "Site ou formulaire": "Les clients arrivent par le site ou un formulaire.",
    "Téléphone": "Les clients arrivent surtout par téléphone.",
    "Email": "Les clients arrivent surtout par email.",
    "WhatsApp / SMS": "Les clients arrivent surtout par WhatsApp ou SMS.",
    "Recommandations": "Les clients arrivent surtout par recommandation ou bouche-à-oreille.",
    "Plateformes": "Les clients arrivent via des plateformes.",
    "À distance": "Je travaille principalement à distance.",
    "France entière": "J'interviens sur toute la France.",
    "Île-de-France": "J'interviens en Île-de-France.",
    "Devis / propositions": "Je perds du temps sur les devis ou propositions.",
    "Relances clients": "Je perds du temps sur les relances clients.",
    "Emails / messages": "Je perds du temps sur les emails ou messages.",
    "Factures / administratif": "Je perds du temps sur les factures ou l'administratif.",
    "Planning / rendez-vous": "Je perds du temps sur le planning ou les rendez-vous.",
    "Recherche d'infos": "Je perds du temps à chercher des informations.",
    "Commandes / demandes clients": "Je perds du temps sur les commandes ou demandes clients.",
    "Plusieurs sujets / je précise": "J’ai plusieurs irritants et je vais les préciser.",
    "Tous les jours": "Cela revient tous les jours.",
    "Chaque semaine": "Cela revient chaque semaine.",
    "1-2 h/semaine": "Cela prend environ 1 à 2 heures par semaine.",
    "3-5 h/semaine": "Cela prend environ 3 à 5 heures par semaine.",
    "Plus de 5 h/semaine": "Cela prend plus de 5 heures par semaine.",
}

def is_help_request(text: str) -> bool:
    hay = str(text or "").casefold()
    return any(re.search(pattern, hay, re.I) for pattern in HELP_PATTERNS)



def answer_matches_expected_field(raw_text: str, stored_text: str, expected_field: str | None) -> bool:
    if not expected_field:
        return False
    raw = re.sub(r"\s+", " ", str(raw_text or "")).strip()
    if not raw:
        return False
    intent = classify_user_intent(raw, expected_field)
    if intent != "answer":
        return False
    if raw in FIELD_OPTIONS.get(expected_field, []):
        return True
    if raw in CONTEXTUAL_ANSWERS and expected_field in {
        "company_size", "company_age", "customer_type", "sales_channel", "location", "repetitive_tasks", "time_spent"
    }:
        # Contextual buttons only validate the field currently being asked.
        return True
    fields = extract_fields(stored_text)
    if fields.get(expected_field):
        return True
    # Business activity is intentionally open: short profession labels are accepted in that context.
    if expected_field == "business_activity" and len(raw) >= 3 and not re.search(r"\?", raw):
        return True
    return False

def expand_contextual_answer(text: str, expected_field: str | None = None) -> str:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw:
        return raw
    mapped = CONTEXTUAL_ANSWERS.get(raw)
    if mapped:
        return mapped
    if expected_field == "business_activity" and raw in FIELD_OPTIONS["business_activity"] and raw != "Autre métier":
        return f"Mon métier est {raw}."
    if expected_field == "business_activity" and raw.casefold() in {"patissier", "pâtissier", "patisserie", "pâtisserie"}:
        return f"Mon métier est {raw}."
    if expected_field == "location" and raw in {"Paris", "Île-de-France", "France entière", "À distance"}:
        return CONTEXTUAL_ANSWERS.get(raw, f"J'interviens à {raw}.")
    return raw


def expected_field_for_step(session: dict[str, Any], step: str) -> str | None:
    missing = missing_fields(session, step)
    return missing[0] if missing else None


def question_for_field(field: str, session: dict[str, Any]) -> str:
    base = FALLBACK_QUESTIONS.get(field, "Pouvez-vous préciser ce point ?")
    last = _last_user_text(session, max_len=160)
    intent = classify_user_intent(last, field)
    recent = _last_client_messages(session, limit=2)
    repeated_precision = len(recent) == 2 and all(msg.get("expected_field") == field and msg.get("intent") == "precision" for msg in recent)
    if repeated_precision or intent == "clarify":
        return FIELD_EXPLANATIONS.get(field, HELP_QUESTIONS.get(field, base))
    if intent in {"help", "precision"}:
        return HELP_QUESTIONS.get(field, FIELD_EXPLANATIONS.get(field, base))
    return base


def options_for_field(field: str | None) -> list[str]:
    return list(FIELD_OPTIONS.get(str(field or ""), []))


def sector_question_for_missing_field(session: dict[str, Any], step: str, field: str | None) -> str | None:
    """Use concrete sector questions before generic field fallbacks.

    J1-bis: when the user says boulanger/boulangerie, the live audit must stop
    feeling like a generic form and ask bakery-shaped questions immediately.
    """
    refs = load_sector_references()
    sector_id = str(session.get("sector_id") or detect_sector(session_text(session), refs))
    if sector_id != "bakery" or not field:
        return None
    blocks = (refs.get("bakery") or {}).get("question_blocks") or {}
    mapping = {
        ("real_week", "repetitive_tasks"): ("pain", 0),
        ("real_week", "time_spent"): ("pain", 1),
        ("tools", "tools"): ("tools", 0),
        ("tools", "flow_breaks"): ("tools", 1),
        ("data_limits", "sensitive_data"): ("risk", 1),
        ("data_limits", "human_validation"): ("risk", 0),
    }
    key = mapping.get((step, field))
    if not key:
        return None
    block_name, idx = key
    block = blocks.get(block_name) or []
    if idx < len(block):
        return enforce_vouvoiement_text(str(block[idx]))
    return None



def next_question(session: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    if _is_business_tech_tree_session(session):
        return business_tech_next_question(session, step)
    step = normalize_step_id(step or str(session.get("current_step") or "intro"))
    refs = load_sector_references()
    sector_id = str(session.get("sector_id") or detect_sector(session_text(session), refs))
    ref = refs.get(sector_id) or refs["generic_tpe"]
    missing = missing_fields(session, step)
    auditbiz_payload: dict[str, Any] | None = None
    if sector_id == "bakery" and step not in {"intro", "synthesis_card", "report"}:
        try:
            enriched_session = dict(session)
            enriched_session["current_step"] = step
            enriched_session["questions_asked"] = [
                {"question_id": item.get("auditbiz_question_id") or item.get("question_id") or item.get("id") or "", "question": item.get("question", "")}
                for item in session.get("asked_questions", [])
                if isinstance(item, dict)
            ]
            auditbiz_payload = auditbiz_choose_next_question(enriched_session, step, sector_id="bakery")
        except Exception:
            auditbiz_payload = None
    contract = step_contract(step)
    if step == "intro":
        question = FALLBACK_QUESTIONS["communication_preferences"]
    elif step == "synthesis_card":
        question = "Avant votre rapport, vérifiez-moi. Corrigez tout ce qui cloche — c’est votre réalité qui compte."
    elif step == "report":
        question = "Votre diagnostic est prêt. Il est à vous, quoi que vous décidiez ensuite."
    elif missing:
        question = sector_question_for_missing_field(session, step, missing[0]) or question_for_field(missing[0], session)
    elif step == "activity":
        question = "J’ai assez d’éléments sur votre activité. Je passe à votre semaine réelle."
    elif auditbiz_payload and auditbiz_payload.get("interaction") == "open":
        question = str(auditbiz_payload.get("question") or FALLBACK_QUESTIONS.get(step, "Ajoutez un détail utile."))
    else:
        block = ref.get("question_blocks", {}).get(step) or ref.get("question_blocks", {}).get(STEP_ALIASES.get(step, step)) or []
        asked = {m.get("question") for m in session.get("asked_questions", [])}
        question = next((q for q in block if q not in asked), FALLBACK_QUESTIONS.get(step, "Ajoutez une précision utile."))
    question = enforce_vouvoiement_text(question)
    # V0 Fable: les boutons confirment ce qu'Omar a compris ; ils ne remplacent jamais le champ libre.
    interaction = contract.get("interaction", "free_text")
    options = [enforce_vouvoiement_text(str(x)) for x in list(contract.get("options", []))]
    if missing:
        options = [enforce_vouvoiement_text(str(x)) for x in options_for_field(missing[0])]
    if auditbiz_payload and auditbiz_payload.get("interaction") in {"rank", "confirm"} and step not in {"intro", "synthesis_card", "report"} and not missing:
        options = [enforce_vouvoiement_text(str(x)) for x in list(auditbiz_payload.get("options") or options)]
    sector_hint = ", ".join(ref.get("important_dimensions", [])[:4])
    result = {
        "step": step,
        "act": contract.get("act"),
        "act_label": contract.get("act_label"),
        "acts": act_metrics(session),
        "sector_id": sector_id,
        "sector_label": sector_id.replace("_", " "),
        "goal": contract["goal"],
        "question": question,
        "missing_fields": missing,
        "completion": completion_for_step(session, step),
        "validation_criteria": contract["validation_criteria"],
        "understanding": build_client_understanding(session),
        "synthesis_card": build_synthesis_card(session) if step in {"opportunities", "synthesis_card", "report"} else None,
        "sector_hint": sector_hint,
        "interaction": interaction,
        "options": options,
        "ui": {"free_text_always_available": True, "rule": "70_30_open_questions_buttons_confirm"},
    }
    if auditbiz_payload and not missing:
        result["auditbiz_question"] = auditbiz_payload
        result["why"] = auditbiz_payload.get("why", "")
        result["skip_allowed"] = auditbiz_payload.get("skip_allowed", True)
        result["save_resume_allowed"] = auditbiz_payload.get("save_resume_allowed", True)
        result["feedback_prompt"] = auditbiz_payload.get("feedback_prompt", "")
    return result

def create_session(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if _wants_business_tech_tree(payload):
        return create_business_tech_session(payload)
    initial = str(payload.get("message") or payload.get("activity") or "")
    refs = load_sector_references()
    sid = f"audit-session-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
    session = {"id": sid, "schema": "oa_audit_session.fable_v0", "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "current_step": "intro", "sector_id": detect_sector(initial, refs), "messages": [], "answers": {}, "asked_questions": [], "validated_steps": [], "metrics": {"act_events": []}, "safety": {"paid_actions": "none", "provisioning": "none"}}
    if initial:
        session["messages"].append({"role": "client", "text": initial, "at": session["created_at"]})
    q = next_question(session, "intro")
    session["asked_questions"].append({"step": "intro", "question": q["question"], "auditbiz_question_id": (q.get("auditbiz_question") or {}).get("id")})
    return {"session": session, "omar": q}

def add_message(session: dict[str, Any], text: str) -> dict[str, Any]:
    if _is_business_tech_tree_session(session):
        return business_tech_add_message(session, text)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    session["current_step"] = normalize_step_id(str(session.get("current_step") or "intro"))
    current_step = str(session.get("current_step") or "intro")
    expected = expected_field_for_step(session, current_step)
    intent = classify_user_intent(text, expected or current_step)
    stored_text = expand_contextual_answer(text, expected)
    session.setdefault("messages", []).append({"role": "client", "text": stored_text, "raw_text": text, "expected_field": expected, "intent": intent, "at": now})
    session.setdefault("conversation_policy", {})["last_intent"] = intent
    if expected and answer_matches_expected_field(text, stored_text, expected):
        session.setdefault("answers", {})[expected] = stored_text
    elif intent == "answer":
        detected = extract_fields(stored_text)
        for field, present in detected.items():
            if present and field in REQUIRED_BY_STEP.get(current_step, []) and field not in (session.get("answers") or {}):
                session.setdefault("answers", {})[field] = stored_text
                break
    session["sector_id"] = detect_sector(session_text(session))
    q = next_question(session, current_step)
    session.setdefault("asked_questions", []).append({"step": q["step"], "question": q["question"], "auditbiz_question_id": (q.get("auditbiz_question") or {}).get("id")})
    return {"session": session, "omar": q}

def validate_step(session: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    if _is_business_tech_tree_session(session):
        return business_tech_validate_step(session, step)
    step = normalize_step_id(step or str(session.get("current_step") or "intro"))
    c = completion_for_step(session, step)
    if not c["ready"]:
        return {"ok": False, "error": "step_incomplete", "completion": c, "omar": next_question(session, step)}
    validated = session.setdefault("validated_steps", [])
    if step not in validated:
        validated.append(step)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    act_id = current_act_for_step(step)
    session.setdefault("metrics", {}).setdefault("act_events", []).append({"at": now, "event": "step_validated", "step": step, "act": act_id})
    steps = fable_step_order()
    idx = steps.index(step) if step in steps else 0
    if idx < len(steps)-1:
        session["current_step"] = steps[idx+1]
    session["acts"] = act_metrics(session)
    return {"ok": True, "session": session, "completion": c, "next": next_question(session, str(session.get("current_step")))}

BUSINESS_TECH_TREE_PATH = ROOT / "src" / "audit_tree.business_tech.v1.yaml"
BUSINESS_TECH_SESSION_SCHEMA = "oa_audit_session.business_tech.v1"
TREE_V0_ALLOWED_INTERACTIONS = {"free_text", "quick_replies", "validation_card", "rank"}


def load_business_tech_tree(path: Path = BUSINESS_TECH_TREE_PATH) -> dict[str, Any]:
    """Load the executable audit tree as data; no LLM prompt free-form fallback."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != "oa.audit-tree/1":
        raise ValueError("invalid business tech audit tree schema")
    if not isinstance(data.get("steps"), list) or not data["steps"]:
        raise ValueError("business tech audit tree has no steps")
    return data


def _wants_business_tech_tree(payload: dict[str, Any]) -> bool:
    return str(payload.get("tree_id") or payload.get("runtime") or "").strip() in {"business_tech", "business_tech_v1", "oa.audit-tree/1"}


def _is_business_tech_tree_session(session: dict[str, Any]) -> bool:
    return str(session.get("schema") or "") == BUSINESS_TECH_SESSION_SCHEMA


def _tree_steps_by_id(tree: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(step.get("step_id")): step for step in tree.get("steps", []) if step.get("step_id")}


def _tree_v0_scope(tree: dict[str, Any]) -> list[str]:
    return [str(step_id) for step_id in ((tree.get("v0_scope") or {}).get("steps") or [])]


def _limit_message_lines(text: str, max_lines: int = 3) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(text or "").splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines[:max(1, int(max_lines or 3))]) if lines else "Pouvez-vous préciser ce point ?"


def _tree_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _coerce_tree_answer_payload(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if not raw:
        return {"answers": {}}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"answers": {"free_text": raw}, "raw_text": raw}
    if isinstance(parsed, dict):
        answers = parsed.get("answers") if isinstance(parsed.get("answers"), dict) else parsed
        return {"step_id": parsed.get("step_id"), "answers": answers, "raw_text": raw}
    return {"answers": {"value": parsed}, "raw_text": raw}


def _tree_detect_product_feedback(text: str) -> dict[str, Any] | None:
    """Detect user critique about the audit/product, not business facts.

    This is a deterministic guardrail for the public audit: if the user is saying
    “your question/flow/report is wrong”, we must not persist that sentence as a
    bakery activity, weekly pain, or risk answer. It becomes product feedback and
    the current step remains incomplete until a real business answer is provided.
    """
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw:
        return None
    hay = raw.casefold()
    critique_markers = [
        "tu ne", "tu n'", "tu n’", "tes questions", "ta question", "vos questions",
        "tu dois", "tu devrais", "il faut que tu", "tu réponds même pas", "tu passes à la question",
        "c'est horrible", "c’est horrible", "désagréable", "désagréables", "nul", "nulle",
        "ça ne sert à rien", "ne sert à rien", "bouton", "ne fait rien", "vocabulaire",
        "rapport tronqué", "je peux même pas", "je ne peux même pas",
        "de quoi tu me parles", "comme un voisin", "boîte", "cette boîte",
    ]
    product_terms = [
        "question", "questions", "audit", "rapport", "diagnostic", "récit", "recit", "bouton",
        "vocabulaire", "transition", "tu", "omar", "page", "chat", "écran", "ecran",
    ]
    if any(marker in hay for marker in critique_markers) and any(term in hay for term in product_terms):
        return {
            "kind": "product_critique",
            "severity": "blocking",
            "verbatim": raw,
            "signals": [marker for marker in critique_markers if marker in hay][:8],
        }
    return None


def _tree_latest_feedback_blocks_step(session: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    """Return latest unresolved product feedback for a step, if it should block validation."""
    latest_feedback: dict[str, Any] | None = None
    latest_feedback_index = -1
    latest_answer_index = -1
    for index, msg in enumerate(session.get("messages", []) or []):
        if str(msg.get("step") or "") != step_id:
            continue
        if msg.get("intent") == "product_feedback":
            latest_feedback = {"step": step_id, "at": str(msg.get("at") or ""), "verbatim": msg.get("text")}
            latest_feedback_index = index
        else:
            latest_answer_index = index
    if latest_feedback and latest_feedback_index > latest_answer_index:
        for item in reversed(session.get("feedback", []) or []):
            if str(item.get("step") or "") == step_id and str(item.get("at") or "") == latest_feedback.get("at"):
                return item
        return latest_feedback
    return None


def _tree_feedback_repair_question(feedback: dict[str, Any], step_id: str) -> str:
    if step_id == "activity_business_model":
        return (
            "Je vous ai mal accompagné : je ne vais pas enregistrer cette critique comme une réponse métier. "
            "Je reprends concrètement : votre établissement, son quartier, sa concurrence directe, l’équipe, les horaires et le chiffre d’affaires relatif sont à cadrer. "
            "Pour repartir proprement, décrivez en une phrase l’activité réelle et ce qu’il faut absolument comprendre sur votre boulangerie."
        )
    if step_id == "public_sources_consent":
        return (
            "Je garde votre correction à part : une recherche publique doit montrer des faits sourcés ou dire clairement qu’elle n’a pas été exécutée. "
            "Voulez-vous corriger l’identité/source, ignorer ces sources, ou relancer la recherche ?"
        )
    return (
        "Je garde votre remarque comme critique du parcours, pas comme réponse métier. "
        "Je reformule avant de continuer : qu’est-ce que je dois comprendre concrètement pour cette étape ?"
    )


CONSULTANT_STEPS_REQUIRING_ACTIONABLE_TEXT = {
    "activity_business_model",
    "person_and_goals",
    "operations_week",
    "admin_finance_purchasing",
    "digital_tools_data",
    "risks_limits",
    "diagnosis",
    "recommendations",
    "validation",
}

NON_ACTIONABLE_EXACT = {
    "oui",
    "non",
    "ok",
    "d'accord",
    "daccord",
    "je ne sais pas",
    "je sais pas",
    "aucune idée",
    "aucune idee",
    "n'importe quoi",
    "n’importe quoi",
    "a la la la",
    "alala",
    "lalala",
    "heu",
    "euh",
}

NON_ACTIONABLE_PATTERNS = [
    r"\bje ne sais pas\b",
    r"\bje sais pas\b",
    r"\btu m.?aides\b",
    r"\bvous m.?aidez\b",
    r"\baidez[- ]?moi\b",
    r"\btu valides\b",
    r"\bvous validez\b",
    r"\btu me poses? une question\b",
    r"\bquestion ou c.?est une affirmation\b",
    r"\bn.?importe quoi\b",
]


def _tree_plain_text_actionability(step_id: str, text: str) -> dict[str, Any]:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    hay = raw.casefold()
    if step_id not in CONSULTANT_STEPS_REQUIRING_ACTIONABLE_TEXT or not raw:
        return {"actionable": True}
    if step_id == "operations_week" and hay in {"tout", "un peu tout", "tout ça", "tout ca"}:
        return {"actionable": True}
    if step_id == "digital_tools_data" and hay in {"beaucoup", "plein", "plein de choses", "pas mal", "beaucoup de choses"}:
        return {"actionable": True}
    if step_id in {"diagnosis", "recommendations", "validation"} and hay in {"oui", "ok", "d'accord", "daccord", "oui je valide"}:
        return {"actionable": True}
    if hay in NON_ACTIONABLE_EXACT or any(re.search(pattern, hay, re.I) for pattern in NON_ACTIONABLE_PATTERNS):
        return {"actionable": False, "kind": "non_actionable", "reason": "weak_or_confused_input", "verbatim": raw}
    words = re.findall(r"[\wÀ-ÿ']+", raw, flags=re.UNICODE)
    if len(words) < 3 and step_id not in {"diagnosis", "recommendations", "validation"}:
        return {"actionable": False, "kind": "non_actionable", "reason": "too_short_for_consultant_step", "verbatim": raw}
    if "?" in raw and any(token in hay for token in ["tu ", "vous ", "omar", "valide", "question"]):
        return {"actionable": False, "kind": "non_actionable", "reason": "user_question_not_business_answer", "verbatim": raw}
    return {"actionable": True}


def _tree_non_actionable_repair_question(classification: dict[str, Any], step_id: str) -> str:
    if step_id == "operations_week" and classification.get("reason") == "weak_or_confused_input":
        return "C’est normal si vous ne savez pas encore. Je ne vais pas inventer. Choisissez une piste à explorer : commandes clients, production/invendus, achats/fournisseurs, caisse/factures, planning/équipe, ou dites-moi ce que vous voulez qu’on observe ensemble."
    if step_id == "admin_finance_purchasing":
        return "Je ne peux pas transformer “je ne sais pas” en diagnostic. Pour vous aider : achats, factures, impayés, caisse, marge ou trésorerie — quel sujet mérite qu’on creuse en premier ?"
    if step_id == "digital_tools_data":
        return "Je ne vais pas valider ça comme cartographie d’outils. Dites-moi simplement ce que vous utilisez aujourd’hui : caisse, téléphone, WhatsApp, Excel, logiciel de factures, Google Business, réseaux, cahier papier — même incomplet."
    if step_id == "risks_limits":
        return "Non : je ne dois pas tout valider seul. La règle à définir ici est justement ce qui reste sous validation humaine : allergènes, prix, paiements, avis, commandes, données clients ou autre. Que voulez-vous garder sous contrôle humain ?"
    if step_id == "diagnosis":
        return "Je comprends que le diagnostic ne vous va pas. Je ne le valide pas. Dites-moi ce qui est faux en priorité : identité, activité, irritants, outils, risques, recommandations — ou écrivez “tout est à reprendre”."
    if step_id == "person_and_goals":
        return "Bonne remarque : si ce n’était pas clair, je pose une vraie question. Votre priorité personnelle aujourd’hui : rentabilité quotidienne, temps libéré, investissement, patrimoine, transmission, ou autre chose ?"
    return "Je ne peux pas valider cette réponse comme donnée métier fiable. Reformulons concrètement : quel fait dois-je retenir pour cette étape ?"


def _tree_sector_specific_question(session: dict[str, Any], step_id: str, missing: list[str]) -> str | None:
    """Replace generic prompts with sector-aware consultant questions when enough context exists."""
    sector_id = _tree_sector_id(session)
    if sector_id != "bakery":
        return None
    if step_id == "activity_business_model" and "recit_activite" in missing:
        return (
            "Je vais cadrer votre boulangerie comme un consultant : emplacement, flux client, concurrence proche, horaires, équipe et ordre de grandeur de CA. "
            "Décrivez d’abord votre activité réelle : boutique, pâtisserie/snacking, commandes, clients principaux, équipe et zone de chalandise."
        )
    if step_id == "person_and_goals" and "objectifs_racontes" in missing:
        return (
            "Je résume avant de vous demander la suite : on parle d’un commerce de bouche local, avec enjeux de flux, marge, équipe et régularité. "
            "Pour vous, c’est surtout un sujet de rentabilité quotidienne, de patrimoine, d’investissement, de temps libéré, ou de transmission ?"
        )
    if step_id == "operations_week" and "semaine" in missing:
        return (
            "Entrons dans le concret boulangerie : production, achats, invendus, commandes, horaires, équipe, admin ou commercial. "
            "Sur une vraie semaine, où perdez-vous le plus de temps ou de marge ?"
        )
    if step_id == "admin_finance_purchasing" and "admin_racontee" in missing:
        return (
            "Côté pilotage : achats farine/beurre/emballages, factures, impayés, caisse, marge par famille produit et trésorerie. "
            "Quel sujet est le plus flou ou coûteux aujourd’hui ?"
        )
    if step_id == "digital_tools_data" and "outils_racontes" in missing:
        return (
            "Cartographions vos outils : caisse, commandes téléphone/WhatsApp/email, planning production, factures, Google Business, avis et réseaux. "
            "Qu’est-ce qui est déjà outillé, et qu’est-ce qui se ressaisit encore à la main ?"
        )
    if step_id == "risks_limits" and "lignes_rouges" in missing:
        return (
            "Fixons les limites métier : allergènes, prix, commandes événementielles, avis négatifs, hygiène/HACCP et réponses client. "
            "Qu’est-ce qui doit toujours rester validé par vous ou l’équipe ?"
        )
    return None


def _tree_step_required_inputs(step: dict[str, Any]) -> list[str]:
    return [str(item.get("id")) for item in step.get("inputs", []) or [] if isinstance(item, dict) and item.get("required", False) and item.get("id")]


def _tree_input_by_id(step: dict[str, Any], input_id: str) -> dict[str, Any] | None:
    for item in step.get("inputs", []) or []:
        if isinstance(item, dict) and str(item.get("id")) == input_id:
            return item
    return None


def _tree_answer_value_is_missing(value: Any) -> bool:
    if value in (None, "", []):
        return True
    if isinstance(value, str):
        normalized = re.sub(r"\s+", " ", value).strip().casefold()
        return normalized in {"à préciser", "a préciser", "je ne sais pas", "je sais pas", "n'importe quoi", "n’importe quoi"}
    if isinstance(value, list):
        return not [item for item in value if not _tree_answer_value_is_missing(item)]
    return False


def _tree_missing_inputs(session: dict[str, Any], step_id: str) -> list[str]:
    step = _tree_steps_by_id(load_business_tech_tree()).get(step_id) or {}
    answers = ((session.get("state") or {}).get(step_id) or {}).get("answers") or {}
    return [input_id for input_id in _tree_step_required_inputs(step) if _tree_answer_value_is_missing(answers.get(input_id))]


def _tree_step_completion(session: dict[str, Any], step_id: str) -> dict[str, Any]:
    step = _tree_steps_by_id(load_business_tech_tree()).get(step_id) or {}
    required = _tree_step_required_inputs(step)
    missing = _tree_missing_inputs(session, step_id)
    done = len(required) - len(missing)
    return {"step": step_id, "required_inputs": required, "missing_inputs": missing, "ready": not missing, "completion_pct": 100 if not required else round(done * 100 / len(required))}


def _tree_public_research_permissions(session: dict[str, Any]) -> dict[str, bool]:
    answers = ((session.get("state") or {}).get("public_sources_consent") or {}).get("answers") or {}
    raw_consents = answers.get("consents")
    consents = raw_consents if isinstance(raw_consents, dict) else {}
    return {
        "public_web_search": bool(consents.get("public_web_search") or consents.get("web_public") or consents.get("site_web") or consents.get("fiche_google")),
        "legal_registry_lookup": bool(consents.get("legal_registry_lookup") or consents.get("sirene_detail")),
        "social_media_lookup": bool(consents.get("social_media_lookup") or consents.get("reseaux")),
    }


def _tree_public_research_authorized(session: dict[str, Any]) -> bool:
    return any(_tree_public_research_permissions(session).values())


def _tree_public_research_attempted(session: dict[str, Any]) -> bool:
    return bool(session.get("public_research"))


def _tree_public_research_validation_status(session: dict[str, Any]) -> str | None:
    answers = ((session.get("state") or {}).get("public_sources_consent") or {}).get("answers") or {}
    explicit_status = answers.get("public_research_validation_status")
    if explicit_status in {"validated", "ignored", "correction_requested"}:
        return str(explicit_status)
    raw = str(answers.get("public_research_validation") or "").lower()
    if not raw:
        return None
    if "correction" in raw or "corriger" in raw:
        return "correction_requested"
    if "ignor" in raw or "sans" in raw:
        return "ignored"
    return "validated"


def _tree_public_research_validated(session: dict[str, Any]) -> bool:
    return _tree_public_research_validation_status(session) in {"validated", "ignored"}


def _tree_public_research_block(step_id: str, session: dict[str, Any]) -> dict[str, Any] | None:
    if step_id != "public_sources_consent" or not _tree_public_research_authorized(session):
        return None
    if not _tree_public_research_attempted(session):
        completion = _tree_step_completion(session, step_id)
        completion.update({"ready": False, "missing_inputs": ["public_research_validation"], "research_required": True})
        return {
            "ok": False,
            "error": "public_research_required",
            "completion": completion,
            "omar": {
                "schema": "oa.audit-tree.next-question.v1",
                "step": step_id,
                "question": "Vous avez autorisé la recherche publique : je dois d’abord la lancer, vous montrer les faits trouvés, puis vous demander validation avant de continuer.",
                "options": ["Lancer la recherche publique", "Corriger le nom ou l’adresse", "Continuer sans recherche"],
                "actions": [
                    {"id": "run_public_research", "label": "Lancer la recherche publique", "intent": "run_public_research"},
                    {"id": "correct_identity", "label": "Corriger le nom ou l’adresse", "intent": "modify"},
                    {"id": "skip_public_research", "label": "Continuer sans recherche", "intent": "deny"},
                ],
            },
        }
    if not _tree_public_research_validated(session):
        completion = _tree_step_completion(session, step_id)
        completion.update({"ready": False, "missing_inputs": ["public_research_validation"], "research_validation_required": True})
        return {
            "ok": False,
            "error": "public_research_validation_required",
            "completion": completion,
            "omar": {
                "schema": "oa.audit-tree.next-question.v1",
                "step": step_id,
                "question": "J’ai des éléments publics à vous faire valider. Dites-moi s’ils sont corrects, à corriger, ou à ignorer avant que je construise mon analyse.",
                "options": ["Valider les informations", "À corriger", "Ignorer ces sources"],
                "actions": [
                    {"id": "validate_public_facts", "label": "Valider les informations", "intent": "confirm_public_research"},
                    {"id": "correct_public_facts", "label": "À corriger", "intent": "modify"},
                    {"id": "ignore_public_facts", "label": "Ignorer ces sources", "intent": "deny"},
                ],
            },
        }
    return None


def _tree_answer_text(session: dict[str, Any]) -> str:
    parts: list[str] = []
    for step_state in (session.get("state") or {}).values():
        for value in (step_state.get("answers") or {}).values():
            parts.append(" ".join(map(str, value)) if isinstance(value, list) else str(value))
    for msg in session.get("messages", []) or []:
        parts.append(str(msg.get("text") or ""))
    return "\n".join(parts)


def _tree_sector_id(session: dict[str, Any]) -> str:
    state = session.get("state") or {}
    activity_answers = ((state.get("activity_business_model") or {}).get("answers") or {}) if isinstance(state.get("activity_business_model"), dict) else {}
    identity_answers = ((state.get("identity_public_context") or {}).get("answers") or {}) if isinstance(state.get("identity_public_context"), dict) else {}
    activity_text = " ".join(str(activity_answers.get(key) or "") for key in ["recit_activite", "type_clients", "canaux_vente"])
    identity_text = str(identity_answers.get("nom_entreprise") or "")
    detected = detect_sector(" ".join([identity_text, activity_text]).strip()) if (identity_text or activity_text).strip() else "generic_tpe"
    if detected != "generic_tpe":
        return detected
    return str(session.get("sector_id") or detect_sector(_tree_answer_text(session)))


def _tree_sector_pack_relance(session: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    if step_id != "operations_week":
        return None
    step_state = (session.get("state") or {}).get(step_id) or {}
    if int(step_state.get("sector_pack_depth") or 0) >= 1:
        return None
    sector_id = _tree_sector_id(session)
    refs = load_sector_references()
    ref = refs.get(sector_id) or refs.get("generic_tpe") or {}
    block = (ref.get("question_blocks") or {}).get("pain") or (ref.get("question_blocks") or {}).get("operations_week") or []
    question = str(block[0]) if block else "Quel irritant concret revient le plus souvent dans votre semaine ?"
    return {"source": "sector_pack.question_blocks", "sector_id": sector_id, "depth": 1, "max_depth": 1, "question": enforce_vouvoiement_text(question)}


def _tree_skip_rules(session: dict[str, Any]) -> set[str]:
    answers = ((session.get("state") or {}).get("activity_business_model") or {}).get("answers") or {}
    return {"hr_team_organization"} if str(answers.get("taille_equipe") or "").casefold() == "solo" else set()


def _tree_next_step_after(session: dict[str, Any], step_id: str) -> str | None:
    scope = list((session.get("runtime") or {}).get("v0_scope") or [])
    skipped = _tree_skip_rules(session)
    if step_id not in scope:
        return scope[0] if scope else None
    idx = scope.index(step_id) + 1
    while idx < len(scope) and scope[idx] in skipped:
        idx += 1
    return scope[idx] if idx < len(scope) else None


def _tree_output_value(input_id: str, answers: dict[str, Any], *, step_id: str) -> dict[str, Any]:
    return {"schema": "oa.audit-tree.output-field.v1", "source": "client_declared_or_validated", "source_step": step_id, "source_input": input_id, "value": answers}


def _tree_contextual_actions(step_id: str, session: dict[str, Any], *, missing: list[str] | None = None) -> list[dict[str, str]]:
    missing = missing or []
    step_answers = ((session.get("state") or {}).get(step_id) or {}).get("answers") or {}
    if step_id == "operations_week" and step_answers.get("interpreted_intent") == "answer_broad":
        return [
            {"id": "priority_orders", "label": "Commandes / demandes clients", "intent": "prioritize"},
            {"id": "clarify_all", "label": "Je précise", "intent": "clarify"},
            {"id": "explain_priority", "label": "Pourquoi choisir une priorité ?", "intent": "explain"},
        ]
    if step_id == "digital_tools_data" and step_answers.get("interpreted_intent") == "answer_vague":
        return [
            {"id": "tools_messages", "label": "Téléphone / messages", "intent": "choose_tool_family"},
            {"id": "tools_cash", "label": "Caisse / facturation", "intent": "choose_tool_family"},
            {"id": "tools_planning", "label": "Planning / commandes", "intent": "choose_tool_family"},
            {"id": "tools_other", "label": "Je veux expliquer", "intent": "clarify"},
        ]
    if step_id == "public_sources_consent":
        return [
            {"id": "consent_public_sources", "label": "Oui, recherche publique autorisée", "intent": "confirm"},
            {"id": "refuse_public_sources", "label": "Non, on continue sans recherche", "intent": "deny"},
            {"id": "explain_sources", "label": "Quelles sources exactement ?", "intent": "explain"},
        ]
    if step_id == "pacte":
        return [
            {"id": "save", "label": "Se connecter pour sauvegarder", "intent": "save"},
            {"id": "continue_without_account", "label": "Continuer sans compte", "intent": "confirm"},
            {"id": "more_info", "label": "En savoir plus", "intent": "explain"},
        ]
    if missing:
        return [
            {"id": "answer", "label": "Je réponds", "intent": "answer"},
            {"id": "example", "label": "Montrez-moi des exemples", "intent": "help"},
            {"id": "skip", "label": "Je ne sais pas encore", "intent": "unknown"},
        ]
    return [
        {"id": "confirm", "label": "Oui, c'est ça", "intent": "confirm"},
        {"id": "modify", "label": "À corriger", "intent": "modify"},
        {"id": "continue", "label": "Continuer", "intent": "continue"},
    ]


def _tree_interpret_contextual_free_text(step_id: str, text: str) -> dict[str, Any] | None:
    hay = str(text or "").strip().casefold()
    if step_id == "pacte":
        if any(token in hay for token in ["continuer sans compte", "on commence", "ok", "go"]):
            return {"sauvegarde_choix": "Continuer sans compte", "tutoiement": "Restons au vous", "rythme": "Droit au but", "pacte_text": text}
        if any(token in hay for token in ["sauvegarder", "connecter", "compte"]):
            return {"sauvegarde_choix": "Se connecter pour sauvegarder", "tutoiement": "Restons au vous", "rythme": "Droit au but", "pacte_text": text}
    if step_id == "identity_public_context" and hay:
        return {"nom_entreprise": str(text or "").strip()}
    if step_id == "activity_business_model" and hay:
        team = "6-20" if any(token in hay for token in ["6 personnes", "6 pers", "équipe de 6", "equipe de 6"]) else ("2-5" if any(token in hay for token in ["2", "3", "4", "5"]) else ("Solo" if "solo" in hay else "À préciser"))
        customers = "Des pros" if any(token in hay for token in ["professionnels", "pros", "b2b"]) else ("Les deux" if any(token in hay for token in ["les deux", "particuliers et pros"]) else "Des particuliers")
        channel = "Sur place" if any(token in hay for token in ["boutique", "sur place", "quartier"]) else "À préciser"
        return {"recit_activite": text, "type_clients": customers, "taille_equipe": team, "canaux_vente": channel}
    if step_id == "person_and_goals" and hay:
        maturity = "J'ai déjà testé l'IA" if "ia" in hay else ("À l'aise" if any(token in hay for token in ["à l'aise", "a l'aise", "correct"]) else "Ça va")
        return {"objectifs_racontes": text, "niveau_digital": maturity}
    if step_id == "operations_week" and hay:
        if hay in {"tout", "un peu tout", "tout ça", "tout ca"}:
            return {
                "semaine": text,
                "interpreted_intent": "answer_broad",
                "detected_irritants": ["horaires", "disponibilité", "commandes", "allergènes", "prix"],
            }
        return {"semaine": text, "top_caillou": "demandes clients", "detected_irritants": ["commandes", "planning", "caisse", "demandes clients", "factures"]}
    if step_id == "admin_finance_purchasing" and hay:
        return {"admin_racontee": text}
    if step_id == "digital_tools_data" and hay:
        if hay in {"beaucoup", "plein", "plein de choses", "pas mal", "beaucoup de choses"}:
            return {
                "outils_racontes": text,
                "interpreted_intent": "answer_vague",
            }
        return {"outils_racontes": text, "outils_confirm": ["Excel", "caisse", "Google Business", "Instagram"]}
    if step_id == "risks_limits" and hay:
        sensitive = ["secret recette"] if "secret" in hay else ["Rien de sensible"]
        return {"lignes_rouges": text, "donnees_sensibles": sensitive, "validation_humaine": "Je valide tout au début"}
    if step_id == "diagnosis" and hay:
        return {"swot_reaction": text, "matrice_reaction": text}
    if step_id == "recommendations" and hay:
        return {"recos_validees": [text], "priorisation": ["réduire les demandes répétitives"]}
    if step_id == "validation" and hay:
        return {"synthese_finale": text}
    if step_id == "public_sources_consent":
        yes_tokens = {"oui", "ok", "d'accord", "daccord", "vas-y", "go", "autorisé", "autorise", "j'autorise"}
        no_tokens = {"non", "pas maintenant", "continue sans", "sans recherche", "je refuse"}
        if any(token in hay for token in ["valider les informations", "infos valid", "informations valid", "faits valid", "c'est correct", "c’est correct"]):
            return {"public_research_validation": "Faits publics validés par le client", "public_research_validation_status": "validated", "public_research_validation_text": text}
        if any(token in hay for token in ["à corriger", "a corriger", "corriger", "ce n'est pas", "ce n’est pas"]):
            return {"public_research_correction": text, "public_research_validation_status": "correction_requested"}
        if any(token in hay for token in ["ignorer", "sans ces sources", "continuer sans recherche"]):
            return {"consents": {"web_public": False, "sirene_detail": False, "site_web": False, "fiche_google": False, "reseaux": False}, "public_research_validation": "Sources ignorées à la demande du client", "public_research_validation_status": "ignored", "consent_text": text}
        if hay in yes_tokens or any(token in hay for token in ["oui", "autorise", "vas-y", "ok pour chercher"]):
            return {"consents": {"web_public": True, "sirene_detail": True, "site_web": False, "fiche_google": False, "reseaux": False}, "consent_text": text}
        if hay in no_tokens or any(token in hay for token in ["sans recherche", "refuse", "pas maintenant"]):
            return {"consents": {"web_public": False, "sirene_detail": False, "site_web": False, "fiche_google": False, "reseaux": False}, "consent_text": text}
    return None


def _tree_contextual_followup_question(step_id: str, session: dict[str, Any]) -> str | None:
    step_answers = ((session.get("state") or {}).get(step_id) or {}).get("answers") or {}
    if step_id == "operations_week" and step_answers.get("interpreted_intent") == "answer_broad" and not step_answers.get("top_caillou"):
        return "D'accord, donc plusieurs demandes reviennent. Si on commence par une seule priorité, laquelle vous soulagerait le plus en premier ?"
    if step_id == "digital_tools_data" and step_answers.get("interpreted_intent") == "answer_vague" and not step_answers.get("outils_confirm"):
        return "D'accord, il y en a beaucoup. Pour commencer simple dans votre activité : lesquels pèsent le plus aujourd'hui — téléphone/messages, caisse/factures, planning/commandes, réseaux sociaux ?"
    return None


def _persist_tree_outputs(session: dict[str, Any], step_id: str) -> None:
    step = _tree_steps_by_id(load_business_tech_tree()).get(step_id) or {}
    answers = ((session.get("state") or {}).get(step_id) or {}).get("answers") or {}
    outputs = session.setdefault("outputs", {"report": {}, "onboarding": {}, "devis": {}})
    for bucket, fields in (step.get("outputs") or {}).items():
        if bucket not in outputs or not isinstance(outputs[bucket], dict):
            outputs[bucket] = {}
        for field in fields or []:
            outputs[bucket][str(field)] = _tree_output_value(str(field), answers, step_id=step_id)


def _tree_completion(session: dict[str, Any]) -> dict[str, Any]:
    scope = list((session.get("runtime") or {}).get("v0_scope") or [])
    skipped = set((session.get("runtime") or {}).get("skipped_steps") or []) | _tree_skip_rules(session)
    validated = set(session.get("validated_steps") or [])
    required = [step for step in scope if step not in skipped]
    complete_steps = [step for step in required if step in validated]
    return {"required_steps": required, "validated_steps": complete_steps, "skipped_steps": sorted(skipped), "complete": all(step in validated for step in required), "completion_pct": round(100 * len(complete_steps) / max(1, len(required)))}


def _tree_state_answers(session: dict[str, Any], step_id: str) -> dict[str, Any]:
    state = session.get("state") or {}
    value = state.get(step_id) if isinstance(state, dict) else {}
    return ((value or {}).get("answers") or {}) if isinstance(value, dict) else {}


def _compact_value(value: Any, *, max_len: int = 280) -> str:
    if isinstance(value, list):
        text = ", ".join(str(x) for x in value if str(x).strip())
    elif isinstance(value, dict):
        text = "; ".join(f"{k}: {v}" for k, v in value.items() if str(v).strip())
    else:
        text = str(value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _tree_declared_evidence(session: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for step_id in (session.get("runtime") or {}).get("v0_scope", []):
        answers = _tree_state_answers(session, str(step_id))
        for value in answers.values():
            compact = _compact_value(value)
            if compact and compact not in items:
                items.append(compact)
    return items[:16]


def _tree_verified_public_evidence(session: dict[str, Any]) -> list[str]:
    facts: list[str] = []
    for record in session.get("public_research", []) or []:
        if not isinstance(record, dict):
            continue
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        for fact in result.get("facts", []) if isinstance(result.get("facts"), list) else []:
            value = _compact_value(fact.get("value") if isinstance(fact, dict) else fact)
            if value:
                facts.append(value)
    return facts[:12]


def _tree_business_analysis(session: dict[str, Any]) -> dict[str, Any]:
    sector_id = _tree_sector_id(session)
    refs = load_sector_references()
    ref = refs.get(sector_id) or refs.get("generic_tpe") or {}
    activity = _tree_state_answers(session, "activity_business_model")
    person = _tree_state_answers(session, "person_and_goals")
    ops = _tree_state_answers(session, "operations_week")
    admin = _tree_state_answers(session, "admin_finance_purchasing")
    tools = _tree_state_answers(session, "digital_tools_data")
    risks = _tree_state_answers(session, "risks_limits")
    text = "\n".join(_tree_declared_evidence(session)).casefold()
    useful_axes = [str(x) for x in ref.get("important_dimensions", [])[:8]] or ["activité", "clients", "outils", "risques"]
    hypotheses: list[dict[str, str]] = []
    if sector_id == "bakery":
        hypotheses.append({"origin": "omar_hypothesis", "confidence": "medium", "text": "Commerce de bouche local : les priorités utiles dépendent fortement du flux boutique, des pertes, de l’équipe et des questions allergènes."})
    if any(token in text for token in ["whatsapp", "téléphone", "telephone", "appel"]):
        hypotheses.append({"origin": "omar_hypothesis", "confidence": "medium", "text": "Les demandes répétitives client sont probablement une première boucle IA pertinente en dry-run validé."})
    recommendations = [
        {"origin": "omar_hypothesis", "confidence": "medium", "text": "Construire une première boucle agent en brouillon validable, centrée sur l’irritant le plus fréquent."},
        {"origin": "declared_client", "confidence": "high", "text": f"Respecter strictement les lignes rouges déclarées : {_compact_value(risks.get('lignes_rouges'), max_len=180) or 'à préciser'}."},
    ]
    if sector_id == "bakery":
        recommendations.append({"origin": "omar_hypothesis", "confidence": "medium", "text": "Prioriser un cas d’usage boulangerie simple : commandes, disponibilité produits, allergènes, avis ou invendus selon validation client."})
    unknowns: list[str] = []
    for label, value in {
        "objectif dirigeant explicite": person.get("objectifs_racontes"),
        "irritant prioritaire chiffré": ops.get("top_caillou") or ops.get("semaine"),
        "marge / pilotage financier": admin.get("admin_racontee"),
        "outils et ruptures de flux": tools.get("outils_racontes"),
        "validation humaine et données sensibles": risks.get("validation_humaine") or risks.get("lignes_rouges"),
        "zone exacte et concurrence proche": activity.get("recit_activite"),
    }.items():
        if value in (None, "", [], {}):
            unknowns.append(label)
    return {
        "schema": "oa.audit-business-analysis.v1",
        "sector_id": sector_id,
        "sector_label": str(ref.get("label") or sector_id.replace("_", " ")),
        "useful_axes": useful_axes,
        "hypotheses": hypotheses[:6],
        "recommendations": recommendations[:6],
        "unknowns": unknowns or ["sources publiques non vérifiées si le client ne les autorise pas", "priorisation finale à co-valider"],
        "signals": {
            "activity": _compact_value(activity.get("recit_activite")),
            "goals": _compact_value(person.get("objectifs_racontes")),
            "operations": _compact_value(ops.get("semaine")),
            "tools": _compact_value(tools.get("outils_racontes")),
            "risks": _compact_value(risks.get("lignes_rouges")),
        },
    }


def _tree_next_best_question(session: dict[str, Any], step_id: str) -> dict[str, Any]:
    legacy_step = {
        "activity_business_model": "activity",
        "identity_public_context": "activity",
        "public_sources_consent": "research",
        "operations_week": "pain",
        "digital_tools_data": "tools",
        "risks_limits": "risk",
        "recommendations": "opportunities",
        "validation": "validation",
    }.get(step_id, "activity")
    candidates = recommend_micro_questions(session, legacy_step, limit=3)
    if candidates:
        return candidates[0]
    return {"id": "fallback", "facet_id": "general", "question": "Quel détail changerait le plus le diagnostic si Omar le comprenait mieux ?", "why": "Un audit utile doit lever les zones floues avant de recommander.", "options": [], "interaction": "open"}


def build_audit_agent_frame(session: dict[str, Any], step_id: str) -> dict[str, Any]:
    tree = load_business_tech_tree()
    step = _tree_steps_by_id(tree).get(step_id) or {}
    analysis = _tree_business_analysis(session)
    return {
        "schema": "oa.audit-agent-frame.v1",
        "mission": {
            "primary_goal": "Comprendre l’entreprise assez précisément pour produire un diagnostic utile et préparer un agent borné, pas remplir un formulaire.",
            "audit_outputs": ["rapport", "recommandations", "brief agent", "devis justifié si demandé"],
        },
        "step": {"id": step_id, "label": step.get("label"), "acte": step.get("acte"), "objective": step.get("objectif")},
        "evidence": {
            "declared_client": _tree_declared_evidence(session),
            "verified_public": _tree_verified_public_evidence(session),
            "omar_hypotheses": [item["text"] for item in analysis.get("hypotheses", [])],
            "missing_or_unverified": analysis.get("unknowns", []),
        },
        "analysis": analysis,
        "next_best_question": _tree_next_best_question(session, step_id),
        "controls": ["Pourquoi cette question", "Passer cette question", "Enregistrer et reprendre plus tard", "Corriger ce que j’ai compris"],
        "guardrails": {"paid_actions": "none", "external_actions": "none_without_explicit_human_go", "source_mixing": "declared_verified_hypothesis_separated", "tone": "vouvoiement, métier, direct"},
    }


PREMIUM_CONSULTING_REFERENCE_DOC = "docs/research/2026-07-08-audit-business-tech-appomar-deep-search-result.md"

PREMIUM_CONSULTING_DIMENSIONS = [
    {
        "id": "identity_official_context",
        "label": "Identité et contexte officiel",
        "integration_level": "V0",
        "target_indicators": ["raison sociale", "code NAF", "effectifs", "adresse administrative"],
        "step_ids": ["identity_public_context", "public_sources_consent"],
        "implication": "La carte d'identité réduit l'effort de saisie et évite de recommander sur une entreprise mal identifiée.",
        "next_test": "Présenter une carte d'identité D/V/H/F et faire corriger le client si la source publique diverge.",
    },
    {
        "id": "business_model_value_proposition",
        "label": "Modèle économique et proposition de valeur",
        "integration_level": "V0",
        "target_indicators": ["typologie de clientèle", "saisonnalité", "complexité de l'offre", "canaux de vente"],
        "step_ids": ["activity_business_model", "person_and_goals"],
        "implication": "Le diagnostic doit rattacher les recommandations au modèle de revenus réel, pas à une envie générique d'IA.",
        "next_test": "Faire valider l'offre, la clientèle, le flux dominant et l'objectif dirigeant avant toute recommandation.",
    },
    {
        "id": "operations_week_mental_load",
        "label": "Semaine réelle et charge mentale",
        "integration_level": "V0",
        "target_indicators": ["temps perdu", "tâches répétitives", "charge émotionnelle", "processus chronophages"],
        "step_ids": ["operations_week"],
        "implication": "La meilleure première boucle IA doit partir de la friction hebdomadaire vécue, pas d'une matrice théorique.",
        "next_test": "Quantifier une semaine témoin : heures perdues, fréquence, ressaisie et irritant émotionnel.",
    },
    {
        "id": "cyber_hygiene_minimal",
        "label": "Hygiène cyber minimale",
        "integration_level": "V0",
        "target_indicators": ["sauvegarde 3-2-1", "MFA", "coffre-fort de mots de passe", "mises à jour"],
        "step_ids": ["digital_tools_data", "risks_limits"],
        "implication": "Même une TPE doit recevoir un diagnostic cyber pragmatique formulé en continuité d'activité, pas en peur.",
        "next_test": "Demander ce qui se passe si le téléphone ou l'ordinateur principal meurt demain matin.",
    },
    {
        "id": "digital_ai_maturity_subjective",
        "label": "Maturité numérique et IA subjective",
        "integration_level": "V0",
        "target_indicators": ["outils de communication", "logiciels de gestion", "usages IA", "appétence au changement"],
        "step_ids": ["person_and_goals", "digital_tools_data"],
        "implication": "L'acceptabilité de l'agent dépend autant du rapport du dirigeant au digital que de la faisabilité technique.",
        "next_test": "Comparer ce que le dirigeant dit savoir faire et ce que les outils permettent réellement.",
    },
    {
        "id": "customer_acquisition_journey",
        "label": "Parcours client et acquisition",
        "integration_level": "V1",
        "target_indicators": ["fiche Google", "site internet", "formulaires", "avis", "délai de réponse"],
        "step_ids": ["marketing_sales", "public_sources_consent"],
        "implication": "L'audit enrichi doit relier visibilité, demande entrante et conversion, surtout pour les commerces locaux.",
        "next_test": "Rejouer une demande client depuis Google/site/téléphone jusqu'au prochain pas proposé.",
    },
    {
        "id": "admin_finance_e_invoicing",
        "label": "Gestion administrative, finance et facturation électronique",
        "integration_level": "V1",
        "target_indicators": ["devis", "facturation", "relances impayés", "préparation facture électronique 2027"],
        "step_ids": ["admin_finance_purchasing"],
        "implication": "La réforme de facturation électronique 2027 est un levier d'engagement utile si elle reste pédagogique et actionnable.",
        "next_test": "Identifier l'outil de facturation, les relances et l'écart avec une facture électronique compatible.",
    },
    {
        "id": "team_organization",
        "label": "Équipe et organisation RH",
        "integration_level": "V2",
        "target_indicators": ["plannings", "transmission consignes", "accès collaborateurs", "formation"],
        "step_ids": ["hr_team_organization"],
        "implication": "L'organisation d'équipe doit être approfondie quand l'effectif le justifie, sinon l'audit doit éviter la fatigue inutile.",
        "next_test": "Vérifier si le dirigeant est solo ; sinon cartographier planning, transmission et accès partagés.",
    },
    {
        "id": "data_ai_readiness_objective",
        "label": "Maturité Data et IA objective",
        "integration_level": "V2",
        "target_indicators": ["fichiers clients", "historique facturation", "conformité RGPD", "API/connecteurs"],
        "step_ids": ["digital_tools_data", "risks_limits"],
        "implication": "L'agent IA n'est crédible que si les données utiles sont disponibles, propres et autorisées.",
        "next_test": "Lister les données nécessaires à la première boucle IA et classer leur source : D, V, H ou F.",
    },
]

FINAL_REPORT_OUTLINE = [
    "Résumé exécutif", "Déclarations du client (D)", "Sources vérifiées (V)", "Hypothèses d'Omar (H)", "Diagnostic business", "Diagnostic tech/data", "Analyse SWOT", "Risques et lignes rouges", "Matrice d'automatisation (Impact/Effort/Risque)", "Quick wins (7 jours)", "Plan d'action (30 jours)", "Recommandations OA (Omar & Alex)", "Limites d'automatisation", "Prompts et procédures utiles", "Données d'onboarding agent", "Structure de devis justifié", "Prochaines décisions",
]


def _maturity_level(score: int) -> dict[str, Any]:
    if score <= 1:
        return {"level": 1, "label": "initial", "description": "gestion artisanale, dépendante des personnes et peu instrumentée"}
    if score == 2:
        return {"level": 2, "label": "structuré partiel", "description": "signaux utiles présents, mais méthode et continuité encore fragiles"}
    if score == 3:
        return {"level": 3, "label": "structuré", "description": "flux principaux compris et premiers garde-fous exploitables"}
    return {"level": 4, "label": "pilotable", "description": "capacité exploitable pour tests courts, mesure et amélioration continue"}


def _evidence_items(*values: Any, fallback: str = "non documenté dans l’audit") -> list[str]:
    items: list[str] = []
    for value in values:
        if isinstance(value, list):
            for item in value:
                compact = _compact_value(item, max_len=180)
                if compact and compact not in items:
                    items.append(compact)
        else:
            compact = _compact_value(value, max_len=220)
            if compact and compact not in items:
                items.append(compact)
    return items or [fallback]


def _premium_dimension_from_session(dim: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    evidence: list[str] = []
    score = 0
    for step_id in dim.get("step_ids", []):
        answers = _tree_state_answers(session, str(step_id))
        compact = _compact_value(answers, max_len=320)
        if compact:
            evidence.append(compact)
            score += 1
    if dim["id"] == "team_organization" and "hr_team_organization" in (session.get("runtime") or {}).get("skipped_steps", []):
        evidence.append("Étape équipe sautée : profil dirigeant solo ou effectif non pertinent pour le parcours court.")
        score = max(score, 2)
    return {
        "id": dim["id"], "label": dim["label"], "integration_level": dim["integration_level"],
        "target_indicators": list(dim.get("target_indicators", [])),
        "maturity_level": _maturity_level(max(1, min(4, score))),
        "evidence": evidence[:5] or ["Signal à collecter ou à valider dans un approfondissement."],
        "implication": dim["implication"], "next_test": dim["next_test"],
    }


def _score_indices(session: dict[str, Any]) -> dict[str, Any]:
    ops = _tree_state_answers(session, "operations_week")
    tools = _tree_state_answers(session, "digital_tools_data")
    risks = _tree_state_answers(session, "risks_limits")
    person = _tree_state_answers(session, "person_and_goals")
    ops_text = _compact_value(ops).casefold(); tools_text = _compact_value(tools).casefold(); risks_text = _compact_value(risks).casefold()
    cyber_score = 35 + (20 if any(t in risks_text for t in ["validation", "humain", "sensible", "allerg"]) else 0) + (15 if any(t in tools_text for t in ["sauvegarde", "backup", "cloud"]) else 0) + (15 if any(t in tools_text for t in ["coffre", "mfa", "2fa", "double authent"]) else 0)
    friction_score = 30 + (25 if any(t in ops_text for t in ["4 h", "4h", "heures", "temps"]) else 0) + (25 if any(t in tools_text for t in ["recopie", "excel", "whatsapp", "téléphone", "telephone"]) else 0) + (10 if _compact_value(ops.get("detected_irritants")) else 0)
    maturity_score = 25 + (25 if any(t in tools_text for t in ["caisse", "excel", "google", "instagram", "whatsapp"]) else 0) + (20 if "ia" in _compact_value(person).casefold() else 0) + (15 if any(t in tools_text for t in ["api", "crm", "centralis", "connect"]) else 0)
    return {"schema": "oa.audit-scores.explainable.v1", "indices": {
        "cyber_hygiene": {"score": min(100, cyber_score), "why": "Score inspiré ANSSI : sauvegarde, accès, validation humaine et exposition des données sensibles.", "limits": "L'audit conversationnel ne vérifie pas techniquement l'existence d'une sauvegarde restaurable ni la configuration MFA.", "how_to_improve": "Tester une restauration, activer MFA sur la messagerie, utiliser un coffre-fort, documenter les accès critiques."},
        "operational_friction": {"score": min(100, friction_score), "why": "Score orienté impact : temps déclaré, ressaisie, canaux dispersés et irritants répétitifs.", "limits": "Le volume exact doit être confirmé par une semaine témoin avant promesse de ROI.", "how_to_improve": "Mesurer 7 jours de demandes, créer des catégories d'intentions, supprimer une ressaisie prioritaire."},
        "digital_ai_maturity": {"score": min(100, maturity_score), "why": "Score inspiré SME AI readiness : outils existants, données structurées, usage IA et appétence au changement.", "limits": "La maturité subjective du dirigeant peut surestimer la disponibilité réelle des données et connecteurs.", "how_to_improve": "Centraliser contacts/historiques utiles, définir règles IA, démarrer par brouillons validés."},
    }}


def _premium_hypotheses(session: dict[str, Any]) -> list[dict[str, Any]]:
    ops = _tree_state_answers(session, "operations_week"); tools = _tree_state_answers(session, "digital_tools_data"); risks = _tree_state_answers(session, "risks_limits")
    return [
        {"id": "h1_operational_roi", "statement": "La première valeur OA se situe dans la réduction de charge mentale et de ressaisie, avant l'automatisation autonome.", "status": "supported" if ops.get("semaine") else "partial", "evidence": _evidence_items(ops.get("semaine"), fallback="irritant hebdomadaire à préciser"), "falsification_test": "Mesurer une semaine réelle : si le volume est faible, prioriser cyber/facturation plutôt qu'agent client."},
        {"id": "h2_data_fragmentation", "statement": "La dispersion entre téléphone, WhatsApp, caisse, Excel, Google ou réseaux crée une friction de données exploitable par un agent en brouillon.", "status": "supported" if tools.get("outils_racontes") else "unverified", "evidence": _evidence_items(tools.get("outils_racontes"), fallback="outils non cartographiés"), "falsification_test": "Suivre un cas client sur deux canaux et vérifier si le contexte doit être ressaisi."},
        {"id": "h3_human_gate", "statement": "Les garde-fous humains doivent précéder toute automatisation visible client, notamment allergènes, prix, acomptes et avis négatifs.", "status": "supported" if risks.get("lignes_rouges") else "partial", "evidence": _evidence_items(risks.get("lignes_rouges"), risks.get("donnees_sensibles"), fallback="lignes rouges à préciser"), "falsification_test": "Tester allergènes/prix/acompte/avis négatif : le système doit produire un brouillon, pas un envoi autonome."},
    ]


def _premium_traceability(session: dict[str, Any], hypotheses: list[dict[str, Any]]) -> dict[str, Any]:
    analysis = _tree_business_analysis(session)
    return {"schema": "oa.audit-traceability.dvfh.v1", "declared_client": _tree_declared_evidence(session), "verified_public": _tree_verified_public_evidence(session), "hypotheses_omar": [h["statement"] for h in hypotheses], "unknowns_or_future_checks": analysis.get("unknowns", [])}


def _premium_agent_profile(session: dict[str, Any]) -> dict[str, Any]:
    risks = _tree_state_answers(session, "risks_limits")
    ops = _tree_state_answers(session, "operations_week")
    tools = _tree_state_answers(session, "digital_tools_data")
    objective = _compact_value(ops.get("top_caillou") or ops.get("semaine"), max_len=180) or "réduire la friction opérationnelle prioritaire"
    return {
        "status": "draft_pending_human_validation",
        "role": "Assistant IA opérationnel AppOmar",
        "core_objective": objective,
        "mission": {
            "primary": objective,
            "success_criteria": [
                "un gain de temps mesuré sur 7 jours",
                "moins de ressaisie entre outils déclarés",
                "zéro action externe sans validation humaine",
                "une preuve client ou métier attachée à chaque recommandation",
            ],
            "operating_context": _compact_value(tools.get("outils_racontes"), max_len=220) or "outils à préciser pendant l'onboarding",
        },
        "authorized_actions": ["préparer des brouillons", "classer les demandes", "résumer les informations", "signaler les risques"],
        "prohibited_actions": ["envoyer sans validation", "modifier prix/paiement", "traiter allergènes sans source validée", "contacter un tiers", "acheter/provisionner"],
        "human_in_the_loop_gates": [risks.get("validation_humaine") or risks.get("lignes_rouges") or "validation humaine avant action externe"],
    }


def _premium_devis_model(session: dict[str, Any], hypotheses: list[dict[str, Any]]) -> dict[str, Any]:
    ops = _tree_state_answers(session, "operations_week")
    tools = _tree_state_answers(session, "digital_tools_data")
    risks = _tree_state_answers(session, "risks_limits")
    first_hypothesis = hypotheses[0]["id"] if hypotheses else "audit"
    return {
        "non_intrusive": True,
        "principle": "Le devis découle des recommandations validées et de leurs preuves, pas d'un tunnel de vente agressif.",
        "line_items": [
            {
                "reference": "OA-AGENT-DRAFT-01",
                "recommendation_source": first_hypothesis,
                "proof_required": "verbatim client + semaine témoin",
                "benefit_expected": "réduction de charge mentale et de ressaisie",
                "prerequisites": ["valider les cas d'usage", "mesurer 7 jours de demandes", "définir les validations humaines"],
                "limits": "brouillons seulement tant que les preuves et gates ne sont pas validés",
                "human_gate": risks.get("validation_humaine") or "validation client avant envoi externe",
                "status": "optionnel",
            },
            {
                "reference": "OA-DATA-CLEAN-01",
                "recommendation_source": "h2_data_fragmentation",
                "proof_required": _compact_value(tools.get("outils_racontes"), max_len=160) or "cartographie des outils à compléter",
                "benefit_expected": "supprimer une rupture de flux prioritaire",
                "prerequisites": ["lister les sources de données", "classer données D/V/H/F", "exclure données interdites"],
                "limits": "pas d'import client ni connecteur sensible sans GO explicite",
                "human_gate": "validation humaine avant accès aux données",
                "status": "à valider",
            },
            {
                "reference": "OA-7D-SMOKE-01",
                "recommendation_source": first_hypothesis,
                "proof_required": _compact_value(ops.get("semaine"), max_len=160) or "irritant hebdomadaire à préciser",
                "benefit_expected": "preuve courte de valeur avant engagement plus large",
                "prerequisites": ["choisir une boucle", "définir métrique", "bloquer actions payantes/provisioning"],
                "limits": "test limité, sans promesse ROI avant mesure",
                "human_gate": "GO client avant toute mise en production",
                "status": "testable",
            },
        ],
    }


def _premium_executive_narrative(session: dict[str, Any], dimensions: list[dict[str, Any]], scores: dict[str, Any], hypotheses: list[dict[str, Any]]) -> str:
    identity = _tree_state_answers(session, "identity_public_context"); activity = _tree_state_answers(session, "activity_business_model"); person = _tree_state_answers(session, "person_and_goals"); ops = _tree_state_answers(session, "operations_week"); tools = _tree_state_answers(session, "digital_tools_data"); risks = _tree_state_answers(session, "risks_limits")
    company = _compact_value(identity.get("nom_entreprise"), max_len=120) or "l’entreprise auditée"
    activity_text = _compact_value(activity.get("recit_activite"), max_len=260) or "activité à préciser"; goals = _compact_value(person.get("objectifs_racontes"), max_len=260) or "objectif dirigeant à préciser"; operations = _compact_value(ops.get("semaine"), max_len=280) or "semaine réelle à préciser"; tools_text = _compact_value(tools.get("outils_racontes"), max_len=280) or "outils et canaux à préciser"; risk_text = _compact_value(risks.get("lignes_rouges"), max_len=260) or "lignes rouges à préciser"; score_summary = scores["indices"]
    paragraphs = [
        f"## RAPPORT DE DIAGNOSTIC BUSINESS & TECH — {company}\n\nCe diagnostic suit le cadre AppOmar du rapport deep-search du 8 juillet 2026 : hybridation déclaratif/public, référence France Num pour les TPE/PME, orientation impact Bpifrance, hygiène ANSSI et respect CNIL des consentements. Le point de départ déclaré est : {activity_text}.",
        f"## Résumé exécutif\n\nPour {company}, le sujet n’est pas de brancher une IA par principe. L'objectif dirigeant déclaré est : {goals}. La bonne lecture consiste à relier modèle économique, semaine réelle, outils, risques et préparation à la facturation électronique 2027, puis à proposer une trajectoire courte et vérifiable.",
        f"## Déclarations client, hypothèses et limites\n\nLe signal opérationnel déclaré le plus fort est : {operations}. L’hypothèse principale d’Omar est que la première valeur vient d’une réduction de charge mentale et de ressaisie, à confirmer par une semaine témoin. Les faits déclarés, les sources vérifiées, les hypothèses et les inconnues restent séparés pour éviter de transformer une supposition en vérité.",
        f"## Diagnostic tech/data et score explicable\n\nLes outils et canaux déclarés sont : {tools_text}. Les indices calculés donnent cyber {score_summary['cyber_hygiene']['score']}/100, friction opérationnelle {score_summary['operational_friction']['score']}/100 et maturité numérique/IA {score_summary['digital_ai_maturity']['score']}/100. Ces scores ne sont pas des vérités techniques : ils expliquent pourquoi progresser, leurs limites, et le prochain test terrain.",
        f"## Risques et lignes rouges\n\nLes risques déclarés imposent une architecture prudente : {risk_text}. Les allergènes, prix, acomptes, avis négatifs et promesses client doivent rester sous validation humaine. C’est la condition pour respecter la confiance métier, les principes CNIL et la logique ANSSI de continuité d’activité plutôt qu’un discours anxiogène.",
        f"## Trajectoire recommandée\n\nLa trajectoire AppOmar reste non intrusive : quick wins en 7 jours, plan d’action 30 jours, agent_profile en brouillon validé, puis devis justifié uniquement à partir des recommandations co-validées. Le rapport final doit donc produire à la fois une synthèse narrative, une matrice impact/effort/risque, des garde-fous, des prompts utiles et des données d’onboarding agent exploitables.",
    ]
    return "\n\n".join(paragraphs)


PREMIUM_FINAL_SECTION_IDS = [
    "executive_summary",
    "declared_client",
    "verified_public",
    "omar_hypotheses",
    "business_diagnosis",
    "tech_data_diagnosis",
    "swot",
    "risks_guardrails",
    "automation_matrix",
    "quick_wins_7_days",
    "action_plan_30_days",
    "oa_recommendations",
    "automation_limits",
    "prompts_procedures",
    "agent_onboarding_data",
    "justified_devis",
    "next_decisions",
]


def _premium_source_buckets(traceability: dict[str, Any]) -> dict[str, int]:
    return {
        "declared_client": len(traceability.get("declared_client") or []),
        "verified_public": len(traceability.get("verified_public") or []),
        "hypotheses_omar": len(traceability.get("hypotheses_omar") or []),
        "unknowns_or_future_checks": len(traceability.get("unknowns_or_future_checks") or []),
    }


def _premium_final_report_sections(session: dict[str, Any], dimensions: list[dict[str, Any]], scores: dict[str, Any], hypotheses: list[dict[str, Any]], traceability: dict[str, Any], analysis: dict[str, Any]) -> list[dict[str, Any]]:
    identity = _tree_state_answers(session, "identity_public_context")
    activity = _tree_state_answers(session, "activity_business_model")
    person = _tree_state_answers(session, "person_and_goals")
    ops = _tree_state_answers(session, "operations_week")
    admin = _tree_state_answers(session, "admin_finance_purchasing")
    tools = _tree_state_answers(session, "digital_tools_data")
    risks = _tree_state_answers(session, "risks_limits")
    company = _compact_value(identity.get("nom_entreprise"), max_len=120) or "entreprise auditée"
    refs = load_sector_references()
    raw_sector_ref = refs.get(str(analysis.get("sector_id") or "")) or refs.get("generic_tpe") or {}
    sector_ref: dict[str, Any] = raw_sector_ref if isinstance(raw_sector_ref, dict) else {}
    raw_benchmarks = sector_ref.get("benchmarks")
    benchmarks: dict[str, Any] = raw_benchmarks if isinstance(raw_benchmarks, dict) else {}
    raw_first_week_tests = benchmarks.get("first_week_tests")
    first_week_tests: list[Any] = raw_first_week_tests if isinstance(raw_first_week_tests, list) else []
    raw_automation_candidates = benchmarks.get("automation_candidates")
    automation_candidates: list[Any] = raw_automation_candidates if isinstance(raw_automation_candidates, list) else []
    raw_risk_flags = sector_ref.get("risk_flags")
    risk_flags: list[Any] = raw_risk_flags if isinstance(raw_risk_flags, list) else []
    bucket_counts = _premium_source_buckets(traceability)

    def section(idx: int, status: str, content: dict[str, Any], evidence: list[str], limits: str, next_action: str) -> dict[str, Any]:
        return {
            "id": PREMIUM_FINAL_SECTION_IDS[idx],
            "title": FINAL_REPORT_OUTLINE[idx],
            "status": status,
            "source_buckets": bucket_counts,
            "content": content,
            "evidence": evidence or ["preuve à collecter"],
            "limits": limits,
            "next_action": next_action,
        }

    declared = traceability.get("declared_client") or []
    verified = traceability.get("verified_public") or []
    unknowns = traceability.get("unknowns_or_future_checks") or []
    recommendations = analysis.get("recommendations") if isinstance(analysis.get("recommendations"), list) else []
    swot = {
        "forces": ["connaissance métier déclarée", "proximité client", _compact_value(activity.get("canaux_vente")) or "canal de vente à préciser"],
        "faiblesses": ["ressaisie ou dispersion d'outils", "dépendance aux validations humaines", "mesure ROI encore à objectiver"],
        "opportunites": automation_candidates[:3] or [h["statement"] for h in hypotheses[:2]],
        "menaces": risk_flags[:3] or ["source publique non validée", "automatisation trop rapide", "données incomplètes"],
    }
    automation_items = [
        {"candidate": str(candidate), "impact": "moyen à fort", "effort": "faible à moyen", "risk": "validation humaine requise", "source": "sector_pack"}
        for candidate in (automation_candidates[:5] or ["brouillons de réponses", "classement demandes", "checklist hebdomadaire"])
    ]
    quick_wins = [
        {"action": str(item), "proof": "test 7 jours", "owner": "client + Omar", "gate": "aucune action externe sans validation"}
        for item in (first_week_tests[:4] or ["mesurer 20 demandes", "classer les irritants", "préparer 5 brouillons", "tester une checklist"])
    ]
    return [
        section(0, "ready", {"company": company, "sector_id": analysis.get("sector_id"), "thesis": "prioriser une boucle IA courte, mesurée et validée humainement"}, declared[:4], "résumé dépendant des réponses et sources consenties", "valider la synthèse avec le dirigeant"),
        section(1, "ready", {"items": declared}, declared[:5], "déclaratif non vérifié techniquement", "corriger les déclarations ambiguës"),
        section(2, "empty" if not verified else "partial", {"items": verified}, verified or ["aucune source publique confirmée dans cette session"], "ne jamais convertir une source non confirmée en fait", "lancer/valider la recherche publique si consentie"),
        section(3, "ready", {"items": hypotheses}, [h.get("statement", "") for h in hypotheses], "hypothèses falsifiables, pas des faits", "choisir les tests qui invalident chaque hypothèse"),
        section(4, "partial", {"activity": activity, "goals": person, "dimensions": [d for d in dimensions if d["id"] in {"business_model_value_proposition", "customer_acquisition_journey", "admin_finance_e_invoicing"}]}, _evidence_items(activity, person, admin), "CA, marge et concurrence restent souvent à compléter", "compléter modèle économique, prix, marge et acquisition"),
        section(5, "partial", {"tools": tools, "scores": scores.get("indices")}, _evidence_items(tools), "scores conversationnels non audit technique", "tester sauvegarde, accès et rupture de flux"),
        section(6, "draft", swot, declared[:3], "SWOT co-validée nécessaire avant usage commercial", "faire réagir le client item par item"),
        section(7, "ready", {"declared_risks": risks, "sector_risk_flags": risk_flags}, _evidence_items(risks, risk_flags), "les règles finales doivent être validées dans l'onboarding", "bloquer allergènes/prix/paiement/contact tiers sans validation"),
        section(8, "draft", {"items": automation_items}, [item["candidate"] for item in automation_items], "impact/effort à confirmer par mesure terrain", "classer 3 opportunités avec le client"),
        section(9, "testable", {"actions": quick_wins}, [item["action"] for item in quick_wins], "quick wins limités, sans promesse ROI", "exécuter un test 7 jours"),
        section(10, "draft", {"days_0_7": "mesure et preuves", "days_8_14": "brouillons validés", "days_15_30": "stabilisation et décision devis"}, _evidence_items(ops, tools), "le plan dépend de la disponibilité client", "poser une métrique unique de succès"),
        section(11, "draft", {"recommendations": recommendations}, [str(r.get("text") or r) for r in recommendations[:4]] if recommendations else ["recommandations à co-valider"], "pas de recommandation sans preuve liée", "rattacher chaque reco à D/V/H/F"),
        section(12, "ready", {"limits": ["pas d'envoi autonome", "pas de paiement/provisioning", "pas de décision sensible", "pas de source non consentie"]}, _evidence_items(risks), "limites à adapter par métier réglementé", "intégrer les gates dans l'agent_profile"),
        section(13, "draft", {"procedures": ["réponse brouillon", "classement intention", "résumé source", "escalade risque"]}, _evidence_items(tools, risks), "prompts non exécutoires sans validation", "écrire les procédures avec exemples réels"),
        section(14, "ready", {"agent_profile": _premium_agent_profile(session)}, _evidence_items(activity, ops, tools, risks), "profil agent brouillon tant que non testé", "importer dans onboarding après GO client"),
        section(15, "draft", {"devis_model": _premium_devis_model(session, hypotheses)}, _evidence_items(ops, tools), "prix/ligne finale à valider humainement", "générer devis seulement après validation recommandations"),
        section(16, "ready", {"decisions": ["valider/corriger rapport", "choisir quick win", "autoriser dry-run", "demander devis"]}, _evidence_items(person, ops), "le client peut digérer sans suite commerciale", "proposer suite sans pression"),
    ]


def _premium_conversation_depth_contract(session: dict[str, Any]) -> dict[str, Any]:
    tree = load_business_tech_tree()
    steps: list[dict[str, Any]] = []
    for raw_step in tree.get("steps") or []:
        if not isinstance(raw_step, dict):
            continue
        step_id = str(raw_step.get("step_id") or "")
        inputs = raw_step.get("inputs") if isinstance(raw_step.get("inputs"), list) else []
        required_inputs = [str(item.get("id")) for item in inputs if isinstance(item, dict) and item.get("required")]
        outputs = raw_step.get("outputs") if isinstance(raw_step.get("outputs"), dict) else {}
        impact = []
        for bucket, values in outputs.items():
            if isinstance(values, list):
                impact.extend(f"{bucket}.{value}" for value in values)
        steps.append({
            "step_id": step_id,
            "acte": raw_step.get("acte"),
            "goal": raw_step.get("objectif") or raw_step.get("label"),
            "expected_evidence": required_inputs,
            "validation_criteria": raw_step.get("completion") or required_inputs or ["réponse exploitable"],
            "repair_behaviors": ["relancer une fois si trop vague", "proposer exemples métier", "bloquer validation si feedback produit non résolu", "séparer D/V/H/F"],
            "report_impact": impact or ["rapport.limites"],
        })
    return {"schema": "oa.audit-step-depth-contract.v1", "source": "audit_tree.business_tech.v1.yaml", "steps": steps}


def build_premium_consulting_report(session: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic AppOmar deep-search aligned premium consulting output."""
    if not _is_business_tech_tree_session(session):
        raise ValueError("build_premium_consulting_report requires business_tech tree session")
    dimensions = [_premium_dimension_from_session(dim, session) for dim in PREMIUM_CONSULTING_DIMENSIONS]
    scores = _score_indices(session)
    hypotheses = _premium_hypotheses(session)
    traceability = _premium_traceability(session, hypotheses)
    narrative = _premium_executive_narrative(session, dimensions, scores, hypotheses)
    analysis = _tree_business_analysis(session)
    return {
        "schema": "oa.premium-consulting-report.v1",
        "session_id": session.get("id"),
        "sector_id": analysis["sector_id"],
        "method": {
            "reference_doc": PREMIUM_CONSULTING_REFERENCE_DOC,
            "frameworks": ["France Num", "Bpifrance", "ANSSI", "CNIL", "OECD SME AI Readiness", "Diag Data IA"],
            "principles": ["hybrider déclarations client et sources publiques seulement consenties", "traduire les frameworks en questions pratiques sans jargon", "scorer simplement avec pourquoi, limite et progression", "générer rapport, agent_profile et devis justifié non intrusif"],
        },
        "diagnostic_dimensions": dimensions,
        "scores": scores,
        "traceability": traceability,
        "hypotheses": hypotheses,
        "final_report_outline": FINAL_REPORT_OUTLINE,
        "final_report_sections": _premium_final_report_sections(session, dimensions, scores, hypotheses, traceability, analysis),
        "conversation_depth_contract": _premium_conversation_depth_contract(session),
        "agent_profile": _premium_agent_profile(session),
        "devis_model": _premium_devis_model(session, hypotheses),
        "executive_narrative": narrative,
    }


def premium_consulting_markdown(report: dict[str, Any]) -> str:
    lines = [str(report.get("executive_narrative") or "")]
    lines.append("\n## Structure du rapport final\n")
    for idx, title in enumerate(report.get("final_report_outline", []) if isinstance(report.get("final_report_outline"), list) else [], start=1):
        lines.append(f"### {idx}. {title}")
    lines.append("\n## Scores explicables\n")
    indices = ((report.get("scores") or {}).get("indices") or {}) if isinstance(report.get("scores"), dict) else {}
    for key, index in indices.items():
        lines.append(f"### {key} — {index.get('score')}/100")
        lines.append(str(index.get("why") or ""))
        lines.append(f"Limite : {index.get('limits') or 'à préciser'}. Progression : {index.get('how_to_improve') or 'à définir'}.\n")
    lines.append("## Traçabilité D/V/H/F\n")
    trace = report.get("traceability") if isinstance(report.get("traceability"), dict) else {}
    lines.append(f"Déclaré client : {len(trace.get('declared_client', []) or [])} éléments. Sources vérifiées : {len(trace.get('verified_public', []) or [])} éléments. Hypothèses : {len(trace.get('hypotheses_omar', []) or [])}. Inconnues : {len(trace.get('unknowns_or_future_checks', []) or [])}.")
    return "\n".join(lines).strip() + "\n"

def build_agent_brief(session: dict[str, Any]) -> dict[str, Any]:
    analysis = _tree_business_analysis(session)
    identity = _tree_state_answers(session, "identity_public_context")
    activity = _tree_state_answers(session, "activity_business_model")
    person = _tree_state_answers(session, "person_and_goals")
    ops = _tree_state_answers(session, "operations_week")
    tools = _tree_state_answers(session, "digital_tools_data")
    risks = _tree_state_answers(session, "risks_limits")
    sensitive = risks.get("donnees_sensibles") or []
    human_validation = [str(risks.get("lignes_rouges") or "Validation humaine avant action externe sensible")]
    if isinstance(sensitive, list):
        human_validation.extend(str(x) for x in sensitive if str(x).strip())
    return {
        "schema": "oa.omar-agent-brief.v1",
        "session_id": session.get("id"),
        "sector_id": analysis["sector_id"],
        "company_context": {
            "identity": _compact_value(identity.get("nom_entreprise")),
            "activity": _compact_value(activity.get("recit_activite")),
            "customers": _compact_value(activity.get("type_clients")),
            "team_size": _compact_value(activity.get("taille_equipe")),
            "goals": _compact_value(person.get("objectifs_racontes")),
            "operations": _compact_value(ops.get("semaine")),
            "tools": _compact_value(tools.get("outils_racontes")),
        },
        "evidence_contract": {
            "declared_client": _tree_declared_evidence(session),
            "verified_public": _tree_verified_public_evidence(session),
            "omar_hypothesis": [item["text"] for item in analysis.get("hypotheses", [])],
        },
        "analysis": analysis,
        "guardrails": {
            "human_validation_required": [item for item in human_validation if item],
            "forbidden_data": sensitive,
            "paid_actions": "none_without_go",
            "external_contacts": "draft_only_until_client_validation",
        },
        "agent_operating_contract": {
            "mode": "draft_agent_after_audit",
            "allowed_actions": ["préparer des brouillons", "classer les demandes", "résumer les avis/sources autorisées", "proposer des checklists", "signaler les risques"],
            "forbidden_actions": ["envoyer sans validation", "modifier prix/paiement", "répondre aux allergènes sans source validée", "contacter un tiers", "provisionner ou acheter"],
            "success_criteria": ["gain de temps visible", "moins de ressaisie", "réponses plus régulières", "zéro action sensible sans validation"],
        },
    }


def create_business_tech_session(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    tree = load_business_tech_tree()
    now = _tree_now()
    sid = f"audit-session-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
    session: dict[str, Any] = {
        "id": sid,
        "schema": BUSINESS_TECH_SESSION_SCHEMA,
        "tree_id": tree["tree_id"],
        "tree_version": tree["version"],
        "created_at": now,
        "current_step": _tree_v0_scope(tree)[0],
        "status": "running",
        "messages": [],
        "state": {},
        "validated_steps": [],
        "outputs": {"report": {}, "onboarding": {}, "devis": {}},
        "runtime": {"v0_scope": _tree_v0_scope(tree), "allowed_interactions_v0": list((tree.get("v0_scope") or {}).get("interactions") or sorted(TREE_V0_ALLOWED_INTERACTIONS)), "skipped_steps": [], "policy": {"regle_70_30": True, "profondeur_relance_max": 1, "message_max_lignes": int((tree.get("principles") or {}).get("message_max_lignes") or 3)}},
        "safety": {"paid_actions": "none", "provisioning": "none", "no_llm_freeform": True},
    }
    raw_payload_runtime = payload.get("runtime")
    payload_runtime: dict[str, Any] = raw_payload_runtime if isinstance(raw_payload_runtime, dict) else {}
    if payload_runtime.get("tester") or payload_runtime.get("is_tester"):
        session.setdefault("runtime", {})["tester"] = payload_runtime.get("tester") or True
    if payload.get("is_tester"):
        session.setdefault("runtime", {})["is_tester"] = True
    initial = str(payload.get("message") or "")
    if initial:
        session["messages"].append({"role": "client", "text": initial, "at": now})
    q = business_tech_next_question(session)
    append_telemetry_event(session, make_session_created(session))
    append_telemetry_event(session, make_button_displayed(session, q.get("actions") if isinstance(q.get("actions"), list) else []))
    session.setdefault("asked_questions", []).append({"step": q["step"], "question": q["question"], "at": now})
    return {"session": session, "omar": q}


def business_tech_next_question(session: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    tree = load_business_tech_tree()
    steps = _tree_steps_by_id(tree)
    step_id = str(step or session.get("current_step") or _tree_v0_scope(tree)[0])
    if step_id not in steps:
        step_id = _tree_v0_scope(tree)[0]
    step_data = steps[step_id]
    missing = _tree_missing_inputs(session, step_id)
    wanted_input = _tree_input_by_id(step_data, missing[0]) if missing else None
    sector_question = _tree_sector_specific_question(session, step_id, missing) if missing else None
    raw_question = str(sector_question or _tree_contextual_followup_question(step_id, session) or (wanted_input or {}).get("question") or step_data.get("entry_message") or step_data.get("objectif") or "Pouvez-vous préciser ce point ?")
    max_lines = int((session.get("runtime") or {}).get("policy", {}).get("message_max_lignes") or (tree.get("principles") or {}).get("message_max_lignes") or 3)
    interaction = str((wanted_input or {}).get("type") or ((step_data.get("inputs") or [{}])[0] or {}).get("type") or "free_text")
    if interaction not in TREE_V0_ALLOWED_INTERACTIONS:
        interaction = "quick_replies" if interaction in {"checklist", "consent_gate", "slider"} else "free_text"
    options = (wanted_input or {}).get("options") or []
    if not isinstance(options, list):
        options = []
    base_question = {"schema": "oa.audit-tree.next-question.v1", "tree_id": tree["tree_id"], "step": step_id, "label": step_data.get("label"), "acte": step_data.get("acte"), "objective": step_data.get("objectif"), "question": _limit_message_lines(enforce_vouvoiement_text(raw_question), max_lines), "interaction": interaction, "options": [enforce_vouvoiement_text(str(item)) for item in options], "actions": _tree_contextual_actions(step_id, session, missing=missing), "completion": _tree_step_completion(session, step_id), "missing_inputs": missing, "sector_pack_relance": _tree_sector_pack_relance(session, step_id), "allowed_interactions_v0": list((tree.get("v0_scope") or {}).get("interactions") or sorted(TREE_V0_ALLOWED_INTERACTIONS)), "policy": {"regle_70_30": True, "message_max_lignes": max_lines, "profondeur_relance_max": 1, "no_llm_freeform": True}}
    base_question["agent_frame"] = build_audit_agent_frame(session, step_id)
    return base_question


def business_tech_add_message(session: dict[str, Any], text: str) -> dict[str, Any]:
    payload = _coerce_tree_answer_payload(text)
    step_id = str(payload.get("step_id") or session.get("current_step") or "pacte")
    now = _tree_now()
    raw_answers = payload.get("answers")
    answers: dict[str, Any] = raw_answers if isinstance(raw_answers, dict) else {"free_text": text}
    # A plain `/message` payload such as {"message": "Continuer sans compte"}
    # arrives without an explicit `answers` object. It is still contextual free
    # text and must be interpreted against the current step before validation.
    is_plain_free_text = isinstance(answers, dict) and set(answers) == {"free_text"}
    raw_text = str(payload.get("raw_text") or text)
    feedback = _tree_detect_product_feedback(raw_text) if is_plain_free_text else None
    if feedback:
        feedback = {**feedback, "step": step_id, "at": now}
        session.setdefault("feedback", []).append(feedback)
        session.setdefault("messages", []).append({"role": "client", "text": raw_text, "step": step_id, "intent": "product_feedback", "at": now})
        session.setdefault("runtime", {})["last_product_feedback"] = feedback
        missing = _tree_missing_inputs(session, step_id)
        question = _limit_message_lines(_tree_feedback_repair_question(feedback, step_id), int((session.get("runtime") or {}).get("policy", {}).get("message_max_lignes") or 3))
        q = {
            **business_tech_next_question(session, step_id),
            "question": question,
            "interaction": "validation_card",
            "options": ["Reprendre proprement", "Corriger l’identité", "Je formule la vraie réponse"],
            "actions": [
                {"id": "restart_step", "label": "Reprendre proprement", "intent": "repair"},
                {"id": "modify_identity", "label": "Corriger l’identité", "intent": "modify"},
                {"id": "answer_business", "label": "Je formule la vraie réponse", "intent": "answer"},
            ],
            "feedback": feedback,
            "completion": {**_tree_step_completion(session, step_id), "ready": False, "missing_inputs": missing},
            "missing_inputs": missing,
        }
        session.setdefault("asked_questions", []).append({"step": step_id, "question": q["question"], "at": now, "feedback_repair": True})
        return {"session": session, "omar": q}

    actionability = _tree_plain_text_actionability(step_id, raw_text) if is_plain_free_text else {"actionable": True}
    if not actionability.get("actionable"):
        actionability = {**actionability, "step": step_id, "at": now}
        session.setdefault("non_actionable_inputs", []).append(actionability)
        session.setdefault("messages", []).append({"role": "client", "text": raw_text, "step": step_id, "intent": "non_actionable", "at": now})
        session.setdefault("runtime", {})["last_non_actionable_input"] = actionability
        missing = _tree_missing_inputs(session, step_id)
        q = {
            **business_tech_next_question(session, step_id),
            "question": _limit_message_lines(_tree_non_actionable_repair_question(actionability, step_id), int((session.get("runtime") or {}).get("policy", {}).get("message_max_lignes") or 3)),
            "interaction": "validation_card",
            "options": ["Montrez-moi des pistes", "Je réponds concrètement", "Corriger ce que vous avez compris"],
            "actions": [
                {"id": "show_examples", "label": "Montrez-moi des pistes", "intent": "help"},
                {"id": "answer_business", "label": "Je réponds concrètement", "intent": "answer"},
                {"id": "modify", "label": "Corriger ce que vous avez compris", "intent": "modify"},
            ],
            "non_actionable_input": actionability,
            "completion": {**_tree_step_completion(session, step_id), "ready": False, "missing_inputs": missing},
            "missing_inputs": missing,
        }
        session.setdefault("asked_questions", []).append({"step": step_id, "question": q["question"], "at": now, "non_actionable_repair": True})
        return {"session": session, "omar": q}

    contextual = _tree_interpret_contextual_free_text(step_id, raw_text) if is_plain_free_text else None
    if contextual:
        answers = contextual
    state = session.setdefault("state", {}).setdefault(step_id, {"answers": {}, "events": [], "sector_pack_depth": 0})
    state.setdefault("answers", {}).update(answers)
    if step_id == "public_sources_consent" and isinstance(answers.get("consents"), dict):
        permissions = answers["consents"]
        session.setdefault("runtime", {})["source_consent_status"] = "authorized" if any(bool(v) for v in permissions.values()) else "refused"
    if "relance_pack" in answers:
        state["sector_pack_depth"] = min(1, int(state.get("sector_pack_depth") or 0) + 1)
    state.setdefault("events", []).append({"at": now, "event": "answers_recorded", "fields": sorted(answers)})
    session.setdefault("messages", []).append({"role": "client", "text": raw_text, "step": step_id, "at": now})
    session["sector_id"] = _tree_sector_id(session)
    session.setdefault("runtime", {})["skipped_steps"] = sorted(_tree_skip_rules(session))
    q = business_tech_next_question(session, step_id)
    session.setdefault("asked_questions", []).append({"step": q["step"], "question": q["question"], "at": now})
    return {"session": session, "omar": q}


def business_tech_validate_step(session: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    step_id = str(step or session.get("current_step") or "pacte")
    completion = _tree_step_completion(session, step_id)
    if not completion["ready"]:
        return {"ok": False, "error": "step_incomplete", "completion": completion, "omar": business_tech_next_question(session, step_id)}
    blocking_feedback = _tree_latest_feedback_blocks_step(session, step_id)
    if blocking_feedback:
        completion = {**completion, "ready": False, "blocked_by_feedback": True}
        return {"ok": False, "error": "product_feedback_unresolved", "completion": completion, "feedback": blocking_feedback, "omar": {**business_tech_next_question(session, step_id), "question": _tree_feedback_repair_question(blocking_feedback, step_id), "interaction": "validation_card", "feedback": blocking_feedback}}
    research_block = _tree_public_research_block(step_id, session)
    if research_block:
        return research_block
    validated = session.setdefault("validated_steps", [])
    if step_id not in validated:
        validated.append(step_id)
    _persist_tree_outputs(session, step_id)
    next_step = _tree_next_step_after(session, step_id)
    session.setdefault("runtime", {})["skipped_steps"] = sorted(_tree_skip_rules(session))
    if next_step:
        session["current_step"] = next_step
    else:
        session["status"] = "complete"
    session["completion"] = _tree_completion(session)
    if session["completion"]["complete"]:
        session["status"] = "complete"
    next_question = business_tech_next_question(session, str(session.get("current_step") or step_id))
    append_telemetry_event(session, make_button_displayed(session, next_question.get("actions") if isinstance(next_question.get("actions"), list) else []))
    append_telemetry_event(session, make_step_validated(session, step=step_id, next_step=next_step, completion=completion))
    return {"ok": True, "session": session, "completion": completion, "next": next_question}


def build_j1ter_documents(session: dict[str, Any]) -> dict[str, Any]:
    """Generate J1-ter founding documents from the business-tech tree state.

    This is intentionally deterministic: no LLM, no transcript scraping. The tree is
    the declarative source; session.state/outputs are the structured runtime state.
    """
    if not _is_business_tech_tree_session(session):
        raise ValueError("build_j1ter_documents requires business_tech tree session")
    state = session.get("state") or {}

    def answers(step_id: str) -> dict[str, Any]:
        return ((state.get(step_id) or {}).get("answers") or {}) if isinstance(state.get(step_id), dict) else {}

    identity = answers("identity_public_context")
    consent = answers("public_sources_consent")
    activity = answers("activity_business_model")
    person = answers("person_and_goals")
    ops = answers("operations_week")
    admin = answers("admin_finance_purchasing")
    tools = answers("digital_tools_data")
    risks = answers("risks_limits")

    sector_id = _tree_sector_id(session)
    profile = {
        "sector_id": sector_id,
        "company_name": identity.get("nom_entreprise"),
        "activity": activity.get("recit_activite"),
        "customers": activity.get("type_clients"),
        "team_size": activity.get("taille_equipe"),
        "sales_channels": activity.get("canaux_vente"),
        "public_source_consents": consent.get("consents") or {},
    }
    owner_identity = {
        "role": "Dirigeant / gérant",
        "goals": person.get("objectifs_racontes"),
        "digital_maturity": person.get("niveau_digital"),
        "preferred_style": "questions simples, validation claire, sans jargon",
    }
    human_gate = risks.get("validation_humaine") or "Validation humaine avant action externe sensible"
    agent_profile = {
        "role": "assistant IA opérationnel",
        "tone": "simple, concret, prudent",
        "missions": [ops.get("top_caillou") or "réduire les demandes répétitives"],
        "channels": ["AppOmar / Hub", "brouillons validables"],
        "human_gates": [human_gate],
        "forbidden_data": risks.get("donnees_sensibles") or [],
    }
    declared = [
        value for value in [
            profile.get("company_name"),
            profile.get("activity"),
            profile.get("customers"),
            profile.get("sales_channels"),
            person.get("objectifs_racontes"),
            ops.get("semaine"),
            admin.get("admin_racontee"),
            tools.get("outils_racontes"),
            risks.get("lignes_rouges"),
        ] if value
    ]
    unknowns = []
    for label, value in {
        "année de création de l'activité": activity.get("annee_creation"),
        "année de début d'expérience métier": person.get("annee_experience_metier"),
        "formation / apprentissage": person.get("formation_metier"),
        "adresse ou zone précise": activity.get("location"),
    }.items():
        if value in (None, "", []):
            unknowns.append(label)
    structured_audit = {
        "schema": "oa.structured_audit.j1ter.v1",
        "source": "audit_tree.business_tech.v1.yaml",
        "session_id": session.get("id"),
        "profile": profile,
        "owner_identity": owner_identity,
        "business_maturity": {
            "objective": person.get("objectifs_racontes"),
            "pressure_points": ops.get("detected_irritants") or [ops.get("semaine")] if ops.get("semaine") else [],
            "tools": tools.get("outils_confirm") or tools.get("outils_racontes"),
        },
        "risk_and_control": {
            "lines_red": risks.get("lignes_rouges"),
            "sensitive_data": risks.get("donnees_sensibles") or [],
            "human_gates": [human_gate],
        },
        "proof": {
            "declared": declared,
            "verified_public": [],
            "hypotheses": ["Première boucle recommandée : traiter l'irritant prioritaire en dry-run validé."],
            "unknowns": unknowns,
        },
    }
    sector_label = "boulangerie/pâtisserie" if sector_id == "bakery" else sector_id.replace("_", " ")
    manifest_business = "\n".join([
        f"# Manifeste business — {profile.get('company_name') or 'client'}",
        "",
        f"Activité comprise : {profile.get('activity') or sector_label}.",
        f"Clients / canaux : {profile.get('customers') or 'à préciser'} — {profile.get('sales_channels') or 'à préciser'}.",
        f"Objectif dirigeant : {person.get('objectifs_racontes') or 'à préciser'}.",
        f"Ligne rouge : {risks.get('lignes_rouges') or 'à préciser'}.",
    ])
    local_constitution = "\n".join([
        "# Pré-constitution locale",
        "",
        f"Source déclarative : audit_tree.business_tech.v1.yaml / session {session.get('id')}.",
        f"Agent proposé : {agent_profile['role']}.",
        f"Validation humaine : {human_gate}.",
        f"Données/lignes rouges : {risks.get('lignes_rouges') or 'à préciser'}.",
    ])
    premium_report = build_premium_consulting_report(session)
    return {
        "schema": "oa.j1ter.documents.v1",
        "session_id": session.get("id"),
        "structured_audit": structured_audit,
        "premium_consulting_report": premium_report,
        "premium_consulting_markdown": premium_consulting_markdown(premium_report),
        "manifest_business": manifest_business,
        "owner_identity": owner_identity,
        "agent_profile": agent_profile,
        "local_constitution": local_constitution,
        "open_questions": unknowns,
    }


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
    alias_map = {
        "web_public": "public_web_search",
        "site_web": "public_web_search",
        "fiche_google": "public_web_search",
        "sirene_detail": "legal_registry_lookup",
        "siret": "legal_registry_lookup",
        "reseaux": "social_media_lookup",
    }
    normalized_raw = dict(raw)
    for alias, canonical in alias_map.items():
        if raw.get(alias):
            normalized_raw[canonical] = True
    permissions = {key: bool(normalized_raw.get(key, False)) for key in CONSENT_KEYS}
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "schema": "oa_audit_consent.v1",
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
        sources.append({"type": "user_answer", "label": "Réponses conversationnelles du client", "provenance": "declared_by_user", "evidence_origin": "declared_client"})
    docs = payload.get("uploaded_documents") if isinstance(payload.get("uploaded_documents"), list) else []
    if docs:
        sources.append({"type": "uploaded_document", "label": f"{len(docs)} document(s) fourni(s)", "provenance": "user_upload", "evidence_origin": "provided_document"})
    consents = normalize_consents(payload)["permissions"]
    if consents.get("public_web_search"):
        sources.append({"type": "public_web_authorized", "label": "Recherche web publique autorisée, non exécutée en V0 déterministe", "provenance": "consent", "evidence_origin": "verified_public"})
    if consents.get("legal_registry_lookup"):
        sources.append({"type": "legal_registry_authorized", "label": "Données légales publiques autorisées, non exécutées en V0 déterministe", "provenance": "consent", "evidence_origin": "verified_public"})
    if consents.get("social_media_lookup"):
        sources.append({"type": "social_media_authorized", "label": "Réseaux sociaux publics autorisés, non exécutés en V0 déterministe", "provenance": "consent", "evidence_origin": "verified_public"})
    sources.append({"type": "sector_reference", "label": str(payload.get("sector_id") or "generic_tpe"), "provenance": "oa_sector_reference", "evidence_origin": "omar_hypothesis"})
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
            recommendations.append({
                "catalog_id": catalog_id,
                "required": required,
                "reason": reason,
                "recommendation_ref": f"audit.recommendations.{catalog_id}",
                "evidence": "declared_client+omar_hypothesis:user_answers_and_sector_reference",
                "confidence": confidence,
            })
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
        "schema": "oa_devis_source.v1",
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
