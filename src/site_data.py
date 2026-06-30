VERSION = "V0.5.0"
PUBLISHED = "26 JUIN 2026"
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

CONNECTOR_READINESS = [
    {
        "capability": "Nango par VPS/tenant client",
        "classification": "potential",
        "proof": "Handover Catalogue: cible tenant définie; export Catalogue Nango hits=0.",
        "gap": "Recette publique et smoke VPS tenant manquants.",
        "owner": "oa-vps-operator",
    },
    {
        "capability": "Nango master Tailnet dogfood",
        "classification": "proven",
        "proof": "Handover Catalogue: TCP443/HTTPS/session validation/logs lus pour le master.",
        "gap": "Ne pas vendre comme production client; master = dogfood interne.",
        "owner": "h-Omar",
    },
    {
        "capability": "OA-CRM JAB Nango Connect session creation",
        "classification": "blocked",
        "proof": "Décision t_d76b3974: tenant-local Nango JAB absent/non prouvé; ancienne preuve master OA non recevable comme preuve client.",
        "gap": "Installer/prouver Nango JAB dédié avant toute session Connect client ou promesse vendable.",
        "owner": "oa-vps-operator",
    },
    {
        "capability": "Google Workspace / Gmail JAB",
        "classification": "blocked",
        "proof": "NO-GO t_d76b3974: nango_jab.exists=false; callback/vhosts JAB absents; aucun consent_ref/check/runbook_ref complet.",
        "gap": "Garder non disponible jusqu'à preuve DNS/TLS/backend/callback/provider/Connect sur tenant Nango JAB.",
        "owner": "h-Omar",
    },
    {
        "capability": "Secrets client: Infisical/Vault refs",
        "classification": "potential",
        "proof": "RECIPE-SPEC mentionne les refs Infisical; export public Infisical hits=0.",
        "gap": "Recette secrets-client et frontière support manquantes.",
        "owner": "oa-builder",
    },
    {
        "capability": "Supervision client",
        "classification": "potential",
        "proof": "Catalogue public supervision hits=0; skill s6 interne seulement.",
        "gap": "Définir checks N1, health endpoints, owner et smoke.",
        "owner": "oa-vps-operator",
    },
    {
        "capability": "Catalogue export contract",
        "classification": "proven",
        "proof": "Tests Catalogue: 9 passed in 4.76s.",
        "gap": "Consommation AppOmar/Hub à maintenir avec le vocabulaire readiness.",
        "owner": "oa-catalogue",
    },
    {
        "capability": "VPS installed inventory aggregation",
        "classification": "potential",
        "proof": "HUB-INTEGRATION documente inventory.yaml par VPS; non smoké dans ce run.",
        "gap": "Smoke oa-vps-operator requis sur VPS client.",
        "owner": "oa-vps-operator",
    },
]

NAV = [
    ("/", "Accueil"),
    ("/audit/", "Audit IA"),
    ("/onboarding/", "Onboarding"),
    ("/devis/", "Devis"),
    ("/sav/", "SAV"),
    ("/compte/", "Compte"),
    ("/aide/", "Aide"),
    ("/changelog/", "Changelog"),
]

PAGES = {
    "/": {
        "title": "Omar App — portail client OA",
        "eyebrow": "CORE OA · Portail client/prospect",
        "summary": "Transformer un prospect en configuration OA exploitable : onboarding, devis, paiement test, SAV et compte Omar.",
        "sections": [
            ("Parcours V0", ["1. Comprendre le besoin", "2. Proposer une configuration OA Start", "3. Préparer installation et support", "4. Suivre le client dans QG/Lab"]),
            ("Statut", ["Skeleton V0 local-first", "Pas encore de paiement réel", "Pas encore d’OAuth réel", "Nango reste L2 pour le moment"]),
        ],
    },
    "/audit/": {
        "title": "Audit IA — explorer mon activité avec Omar",
        "eyebrow": "Facile · profond · adaptatif · utile",
        "summary": "Réalisez votre audit en discutant avec Omar : besoins, outils actuels, tâches répétitives, contraintes, urgences et objectifs deviennent un rapport personnalisé.",
        "sections": [
            ("Promesse", ["Question centrale : vrais enjeux et limites actuelles de l’IA pour votre activité en 2026", "Conversation simple sur mobile ou ordinateur", "Questions adaptées au niveau IA, à l’activité et aux contraintes"]),
            ("Rapport attendu", ["Diagnostic de situation et opportunités", "Tutoriel pour lancer une première boucle en autonomie", "Prompts utiles, commandes éventuelles et décisions à prendre", "Plan 24h / 7 jours / 30 jours"]),
            ("Garde-fous", ["Aucun paiement pendant l’audit", "Aucun provisioning automatique", "Secrets et données sensibles à ne jamais coller dans l’outil", "Validation humaine avant suite commerciale"]),
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
    "/devis/": {
        "title": "Devis — composer l'offre OA",
        "eyebrow": "Pré-commande / paiement test",
        "summary": "Le devis transforme l'onboarding en sélection de formules et options. Paiement réel désactivé tant que Stripe n'est pas configuré ; le 1er mois devra être payé avant activation réelle.",
        "sections": [
            ("Flux", ["Sélection produits catalogue", "Création devis JSON", "Checkout Stripe test ou message explicite", "paid_actions=none tant que non configuré"]),
            ("Offre", ["Prix à partir de", "Coupons/bons/remises pilotes", "Option PC accompagnée", "VPS ou hybride selon profil"]),
        ],
    },
    "/aide/": {
        "title": "Aide — comprendre le parcours OA",
        "eyebrow": "FAQ et prochaines étapes",
        "summary": "Aide courte pour prospects et clients : onboarding, devis, paiement du premier mois, option PC, SAV et compte.",
        "sections": [
            ("Questions fréquentes", ["Que se passe-t-il après l'onboarding ?", "Quand paie-t-on le premier mois ?", "Comment fonctionne l'option PC ?", "Que veut dire paiement test ?"]),
            ("Support", ["SAV depuis /sav/", "Compte client isolé", "Validation humaine avant actions risquées"]),
        ],
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
        "summary": "V0.5.0 · 26 juin 2026 · Tunnel A→Z onboarding → devis → agent + option PC smoke.",
        "sections": [
            ("V0.5.0", ["Onboarding conversationnel 6 étapes", "Routes canoniques /onboarding/, /devis/, /sav/, /compte/", "Agent profile exploitable par Hermes", "Option PC alignée OmarTop pc-smoke-check", "paid_actions=none tant que non configuré"]),
            ("V0.4.0", ["Sécurité anti-énumération PII", "Statuts onboarding/SAV isolés par client", "Forward-auth requis pour endpoints multi-tenant", "Catalogue et pricing exposés en read-only"]),
            ("V0.3.0", ["POST /api/proposals pour stocker les propositions", "GET /api/proposals/<id> pour relecture opérateur", "GET /api/hetzner/pricing read-only", "Fallback statique si token Hetzner non disponible", "Toujours aucun coût sans GO humain"]),
            ("V0.2.0", ["Wizard /config réel", "Proposal JSON configuration_proposal", "Dry-run Hetzner pending_human_go", "Apps L1 alignées OmarTop → Hub", "Aucun POST payant automatique"]),
            ("V0.1.0", ["Routes directes créées", "Contrat App aligné", "Onboarding/config/SAV/factures/compte documentés", "No secrets"]),
        ]
    },
}
