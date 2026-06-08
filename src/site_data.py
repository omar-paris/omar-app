VERSION = "V0.1.0"
PUBLISHED = "8 JUIN 2026"
DOMAIN = "app.omar.paris"

NAV = [
    ("/", "Accueil"),
    ("/onboarding/", "Onboarding"),
    ("/config/", "Config"),
    ("/buy/", "Buy"),
    ("/sav/", "SAV"),
    ("/factures/", "Factures"),
    ("/compte/", "Compte"),
    ("/changelog/", "Changelog"),
]

PAGES = {
    "/": {
        "title": "Omar App — portail client OA",
        "eyebrow": "CORE OA · Portail client/prospect",
        "summary": "Transformer un prospect en configuration OA exploitable : onboarding, config, buy, SAV, factures et compte Omar.",
        "sections": [
            ("Parcours V0", ["1. Comprendre le besoin", "2. Proposer une configuration OA Start", "3. Préparer installation et support", "4. Suivre le client dans QG/Lab"]),
            ("Statut", ["Skeleton V0 local-first", "Pas encore de paiement réel", "Pas encore d’OAuth réel", "Nango reste L2 pour le moment"]),
        ],
    },
    "/onboarding/": {
        "title": "Onboarding — formulaire + conversation",
        "eyebrow": "Qualifier le besoin client",
        "summary": "L’onboarding combine formulaire structuré et conversation chatbot pour définir entreprise, objectifs, livrables, outils existants, domaine, préférences et ressources.",
        "sections": [
            ("Questions entreprise", ["Nom et activité de l’entreprise", "Interlocuteurs", "Domaine existant ou domaine à acheter", "Contraintes métier ou légales"]),
            ("Objectifs et livrables", ["Objectifs prioritaires", "Livrables attendus", "Ressources disponibles", "Préférences de communication et souveraineté"]),
            ("Outils existants", ["Google Workspace", "Microsoft 365", "Infomaniak", "OVH", "Orange / SFR / Laposte", "CRM, facturation, téléphone pro"]),
        ],
    },
    "/config/": {
        "title": "Config — wizard OA Start",
        "eyebrow": "Transformer le besoin en configuration",
        "summary": "Le wizard /config utilise l’onboarding pour proposer un Pack OA Start actionnable : VPS Hetzner, email/domaine Infomaniak, compte Omar, Hub, agent Hermes OA et support.",
        "sections": [
            ("Pack OA Start", ["VPS Hetzner", "Email et domaine Infomaniak si nécessaire", "Hub local", "Agent Hermes OA", "Support/SAV via App"]),
            ("Connexions", ["Modèle connection_intent", "OAuth possible plus tard", "Nango = L2 pour le moment", "Infisical pour secrets machine/client"]),
            ("Sortie attendue", ["Configuration recommandée", "Coûts estimés", "Informations manquantes", "Prochaines actions internes"]),
        ],
    },
    "/buy/": {
        "title": "Buy — démarrer OA",
        "eyebrow": "Pré-commande / devis",
        "summary": "Page placeholder pour transformer la configuration en demande de démarrage, devis ou paiement futur.",
        "sections": [("V0", ["Pas de paiement réel", "Demande de démarrage", "Récapitulatif de configuration", "Validation humaine OA"])]
    },
    "/sav/": {
        "title": "SAV — support client",
        "eyebrow": "Bugs, demandes, incidents, questions",
        "summary": "Le SAV reçoit les demandes client et les transforme en tickets exploitables : bug, request, incident ou question.",
        "sections": [("Types", ["bug", "request", "incident", "question"]), ("Statuts", ["nouveau", "en analyse", "en cours", "résolu", "bloqué"])]
    },
    "/factures/": {
        "title": "Factures — abonnement et documents",
        "eyebrow": "Placeholder facturation",
        "summary": "Espace futur pour factures, abonnement et paiements. V0 documente le besoin sans traitement financier réel.",
        "sections": [("V0", ["Factures placeholder", "Statut abonnement futur", "Aucun paiement réel dans le skeleton"])]
    },
    "/compte/": {
        "title": "Compte Omar — multi-tenant",
        "eyebrow": "Identité client et frontières sécurité",
        "summary": "Chaque client possède un compte Omar multi-tenant : il ne voit que ses données, ses rôles, ses connexions et ses demandes.",
        "sections": [
            ("Frontières", ["Chaque client ne voit que ses données", "Rôles et membres", "Aucun secret en clair", "Pas de données inter-tenant"]),
            ("Secrets", ["Infisical pour secrets machine/client", "Hermes Agent Vault distinct pour runtime agents", "Bitwarden humain-only hors agents"]),
        ],
    },
    "/changelog/": {
        "title": "Changelog",
        "eyebrow": "Historique Omar App",
        "summary": "V0.1.0 · 8 juin 2026 · Skeleton local-first de app.omar.paris.",
        "sections": [("V0.1.0", ["Routes directes créées", "Contrat App aligné", "Onboarding/config/SAV/factures/compte documentés", "No secrets"])]
    },
}
