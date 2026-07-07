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
    "business_activity": [r"\b(boulanger|boulangerie|p[âa]tissier|p[âa]tissi[èe]re|p[âa]tisserie|restaurant|plombier|chauffagiste|rénovation|renovation|électricien|electricien|fleuriste|avocat|patrimoine|marketing|secr[ée]taire|traducteur|traductrice|traduction|freelance|consultant|consultante|coach|formateur|formatrice|commerce|boutique)\b", r"je suis", r"nous sommes", r"mon activité", r"mon métier"],
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
    "time_spent": "Ce caillou revient combien de fois ou vous prend combien de temps par semaine ?",
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
    "business_activity": "Je cherche juste le métier réel, pas une catégorie parfaite. Exemple : pâtissier, salon de coiffure, traducteur freelance, restaurant italien, cabinet d’avocat.",
    "company_size": "Je cherche l’ordre de grandeur de l’équipe qui fait tourner l’activité : solo, 2-5, 6-20, ou plus. Une estimation suffit.",
    "company_age": "Je cherche l’ancienneté approximative, parce qu’une activité lancée cette année n’a pas les mêmes priorités qu’une maison installée depuis 10 ans.",
    "customer_type": "Je veux savoir pour qui vous travaillez vraiment : particuliers, professionnels, ou les deux. Ça change les opportunités utiles.",
    "sales_channel": "Je cherche le chemin d’arrivée des clients : boutique, téléphone, email, site, WhatsApp, recommandations, plateformes. Plusieurs réponses sont possibles.",
    "location": "Je cherche votre zone réelle : adresse, ville, quartier, rayon d’intervention, région, France entière ou à distance. Une adresse complète marche aussi.",
    "repetitive_tasks": "Je cherche ce qui vous mange du temps dans une vraie semaine : devis, relances, messages, planning, factures, recherche d’infos, suivi client.",
    "time_spent": "Je cherche un ordre de grandeur : tous les jours, chaque semaine, 1-2 h, 3-5 h, ou plus. Pas besoin d’être exact.",
}


def classify_user_intent(text: str, expected_field: str | None = None) -> str:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw:
        return "empty"
    if raw in PRECISION_PLACEHOLDERS:
        return "precision"
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
    "business_activity": ["Traducteur freelance", "Artisan bâtiment", "Commerce / boutique", "Restaurant / food", "Conseil / formation", "Autre métier"],
    "company_size": ["Solo", "2-5", "6-20", "20+", "Je précise"],
    "company_age": ["Moins d’un an", "1-3 ans", "4-10 ans", "Plus de 10 ans", "Reprise / transmission"],
    "customer_type": ["Particuliers", "Professionnels", "Les deux", "Je ne sais pas encore"],
    "sales_channel": ["Boutique / lieu physique", "Site ou formulaire", "Téléphone", "Email", "WhatsApp / SMS", "Recommandations", "Plateformes"],
    "location": ["Paris", "Île-de-France", "France entière", "À distance", "Je précise"],
    "repetitive_tasks": ["Devis / propositions", "Relances clients", "Emails / messages", "Factures / administratif", "Planning / rendez-vous", "Recherche d'infos", "Montrez-moi des exemples"],
    "time_spent": ["Tous les jours", "Chaque semaine", "1-2 h/semaine", "3-5 h/semaine", "Plus de 5 h/semaine", "Je ne sais pas"],
}

HELP_QUESTIONS = {
    "business_activity": "Je vous aide. Dites simplement votre métier comme sur une carte de visite. Exemples : traducteur freelance, plombier, boulangerie, cabinet de conseil, boutique en ligne.",
    "company_size": "Pas besoin d'être précis : êtes-vous solo, 2 à 5, 6 à 20, ou plus ?",
    "company_age": "Une approximation suffit : activité lancée récemment, 1-3 ans, 4-10 ans, plus ancien, ou reprise ?",
    "customer_type": "Pensez à vos derniers clients : plutôt particuliers, professionnels, ou les deux ?",
    "sales_channel": "Pensez au dernier client signé : il est venu par recommandation, téléphone, email, boutique, site, plateforme, réseau ?",
    "location": "Indiquez seulement votre zone utile : ville, région, France entière, ou à distance.",
    "repetitive_tasks": "Je vous propose des pistes. La semaine dernière, est-ce que vous avez perdu du temps sur devis/propositions, relances, emails, factures, planning, recherche d'informations, ou suivi client ?",
    "time_spent": "Même à la louche : tous les jours, chaque semaine, 1-2 h, 3-5 h, ou plus de 5 h par semaine ?",
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
    if not raw or classify_user_intent(raw, expected_field) != "answer":
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

def next_question(session: dict[str, Any], step: str | None = None) -> dict[str, Any]:
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
        question = question_for_field(missing[0], session)
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
