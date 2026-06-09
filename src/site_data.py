VERSION = "V0.2.0"
PUBLISHED = "9 JUIN 2026"
DOMAIN = "app.omar.paris"

OA_START_PACKS = [
    {
        "id": "starter",
        "label": "Starter",
        "provider": "hetzner",
        "server_type": "cax21",
        "fallback_server_type": "cpx21",
        "location": "fsn1",
        "image": "ubuntu-24.04",
        "backups_default": True,
        "monthly_total_eur": 9.0,
        "status": "pending_human_go",
        "note": "Profil coût-efficace ARM si compatibilité validée ; x86 fallback cpx21.",
    },
    {
        "id": "pro",
        "label": "Pro",
        "provider": "hetzner",
        "server_type": "cax31",
        "fallback_server_type": "cpx31",
        "location": "fsn1",
        "image": "ubuntu-24.04",
        "backups_default": True,
        "monthly_total_eur": 18.0,
        "status": "pending_human_go",
        "note": "Profil conseillé pour premier client sérieux avec marge RAM/CPU.",
    },
    {
        "id": "max",
        "label": "Max",
        "provider": "hetzner",
        "server_type": "cax41",
        "fallback_server_type": "cpx41",
        "location": "fsn1",
        "image": "ubuntu-24.04",
        "backups_default": True,
        "monthly_total_eur": 36.0,
        "status": "pending_human_go",
        "note": "Profil confort ; à valider humainement avant coût récurrent.",
    },
]

APPS_L1 = [
    {"slug": "ubuntu", "name": "Ubuntu 24.04", "required": True, "source": "OmarTop L1"},
    {"slug": "ssh", "name": "SSH admin OA", "required": True, "source": "OmarTop L1"},
    {"slug": "ufw", "name": "UFW / firewall", "required": True, "source": "OmarTop L1"},
    {"slug": "tailscale", "name": "Tailscale", "required": True, "source": "OmarTop L1"},
    {"slug": "caddy", "name": "Caddy + TLS", "required": True, "source": "OmarTop L1"},
    {"slug": "hub", "name": "Hub local", "required": True, "source": "OmarTop L1"},
    {"slug": "hermes-agent", "name": "Hermes Agent", "required": True, "source": "OmarTop L1"},
    {"slug": "secrets", "name": "Secrets Vault/Infisical cible", "required": True, "source": "OmarTop L1"},
    {"slug": "backups", "name": "Backups serveur", "required": True, "source": "OmarTop L1"},
    {"slug": "qg-reporting", "name": "QG reporting / health", "required": True, "source": "OmarTop L1"},
]

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
        "summary": "V0.2.0 · 9 juin 2026 · Wizard config + proposition JSON + dry-run Hetzner.",
        "sections": [
            ("V0.2.0", ["Wizard /config réel", "Proposal JSON configuration_proposal", "Dry-run Hetzner pending_human_go", "Apps L1 alignées OmarTop → Hub", "Aucun POST payant automatique"]),
            ("V0.1.0", ["Routes directes créées", "Contrat App aligné", "Onboarding/config/SAV/factures/compte documentés", "No secrets"]),
        ]
    },
}
