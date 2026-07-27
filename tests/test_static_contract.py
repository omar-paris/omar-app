from pathlib import Path
import json
import re
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

ROUTES = {
    "/": PUBLIC / "index.html",
    "/audit": PUBLIC / "audit" / "index.html",
    "/onboarding": PUBLIC / "onboarding" / "index.html",
    "/devis": PUBLIC / "devis" / "index.html",
    "/aide": PUBLIC / "aide" / "index.html",
    "/sav": PUBLIC / "sav" / "index.html",
    "/compte": PUBLIC / "compte" / "index.html",
    "/changelog": PUBLIC / "changelog" / "index.html",
}


def build_site():
    subprocess.run(["python3", "scripts/build.py"], cwd=ROOT, check=True)


def html(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_build_generates_all_direct_routes():
    build_site()
    for route, path in ROUTES.items():
        assert path.exists(), f"Missing route {route}: {path}"
        text = html(path)
        assert "Omar App" in text
        assert "V0.5.0" in text
        assert "app.omar.paris" in text


def test_public_artifacts_are_reproducible_from_the_committed_checkout():
    """A clean committed checkout must stay clean after rebuilding public assets."""
    with tempfile.TemporaryDirectory(prefix="omar-app-build-contract-") as temp_dir:
        checkout = Path(temp_dir) / "checkout"
        checkout.mkdir()
        archive_path = Path(temp_dir) / "head.tar"
        with archive_path.open("wb") as archive:
            subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"],
                cwd=ROOT,
                check=True,
                stdout=archive,
            )
        with tarfile.open(archive_path) as archive:
            archive.extractall(checkout, filter="data")
        subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
        subprocess.run(["git", "add", "-A"], cwd=checkout, check=True)
        subprocess.run(
            ["git", "-c", "user.name=contract", "-c", "user.email=contract@example.invalid", "commit", "-qm", "baseline"],
            cwd=checkout,
            check=True,
        )
        subprocess.run(["python3", "scripts/build.py"], cwd=checkout, check=True)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=checkout,
            check=True,
            text=True,
            capture_output=True,
        )
        assert status.stdout == "", status.stdout


def test_navigation_links_are_real_direct_urls():
    build_site()
    text = html(PUBLIC / "index.html")
    for route in ["/audit/", "/onboarding/", "/devis/", "/sav/", "/compte/", "/changelog/"]:
        assert f'href="{route}"' in text
    assert 'href="#"' not in text


def test_onboarding_page_collects_required_client_context():
    build_site()
    text = html(PUBLIC / "onboarding" / "index.html").lower()
    required_terms = [
        "entreprise",
        "objectifs",
        "livrables",
        "outils existants",
        "domaine",
        "préférences",
        "ressources",
        "conversation",
    ]
    for term in required_terms:
        assert term in text


def test_audit_page_is_v4_minimal_conversation_not_cockpit_or_static_form():
    build_site()
    raw = html(PUBLIC / "audit" / "index.html")
    text = raw.lower()
    for term in [
        "conversation avec omar",
        "progression",
        "on fait connaissance",
        "on entre dans le concret",
        "votre diagnostic",
        "audit_business_tech_tree_v1",
        "audit business & tech actif",
        "noyau déclaratif yaml",
        "bonjour, moi c’est omar",
        "à travers plusieurs questions",
        "diagnostic business & tech complet",
        "plusieurs documents",
        "ce qu’omar a compris",
        "ce qu’il ne faut pas automatiser",
        "continuer sans compte",
        "se connecter pour sauvegarder",
        "recevoir ce rapport",
        "le devis est volontairement réservé aux personnes enregistrées",
        "height:100dvh",
        "grid-template-columns:minmax(190px,230px) minmax(0,1fr)",
        "/api/audit-sessions",
        "/documents",
        "aucune action payante",
    ]:
        assert term in text
    for forbidden_intro in [
        "répondez librement. vous pouvez faire l’audit sans compte",
        "sauvegarde optionnelle",
        "obligatoire seulement pour accéder au devis",
        "style v4",
        "aucune carte bancaire",
        "rencontre. plongée. livraison.",
    ]:
        assert forbidden_intro not in text
    for step in ["démarrage", "identité", "sources publiques", "activité", "dirigeant & objectifs", "semaine réelle", "marketing & ventes", "admin & finances", "équipe & organisation", "outils", "lignes rouges", "diagnostic", "priorités", "synthèse finale"]:
        assert step in text
    for act in ["on fait connaissance", "on entre dans le concret", "votre diagnostic"]:
        assert act in text
    assert "linear-gradient" not in text
    assert "radial-gradient" not in text
    assert "cockpit conversationnel" not in text
    assert "valider cette étape" not in text
    assert "préparer recherches" not in text
    assert "<form id=\"audit-form\"" not in text


def test_audit_page_final_step_matches_business_tech_runtime_validation_not_legacy_report():
    build_site()
    raw = html(PUBLIC / "audit" / "index.html")
    compact = re.sub(r"\s+", "", raw)

    assert "{id:'livraison',label:'Votrediagnostic',steps:['diagnosis','recommendations','validation']}" in compact
    assert "{id:'validation',label:'Synthèsefinale'" in compact
    assert "session.status==='complete'" in raw
    assert "completion.complete" in raw
    assert "current_step)==='report'" not in raw
    assert "final_synthesis" not in raw
    assert "audit_fable_tree_v0" not in raw


def test_audit_page_buttons_expose_action_metadata_without_label_as_id():
    build_site()
    raw = html(PUBLIC / "audit" / "index.html")

    assert "data-action-id" in raw
    assert "data-rank" in raw
    assert "button_clicked" in raw
    assert "/telemetry" in raw
    assert "telemetryActionId" in raw
    assert "data-action-id=\"${esc(a.label)}\"" not in raw


def test_devis_page_declares_registered_payment_blocked_target():
    build_site()
    text = html(PUBLIC / "devis" / "index.html").lower()
    for term in [
        "accès devis réservé aux personnes enregistrées",
        "paiement sécurisé non configuré",
        "continuer vers le paiement sécurisé",
        "aucun provisioning sans validation humaine",
        "paiement sécurisé en attente de configuration",
        "paiement en attente",
    ]:
        assert term in text


def test_config_page_defines_actionable_oa_start_wizard():
    build_site()
    text = html(PUBLIC / "config" / "index.html").lower()
    for term in ["pack oa start", "hetzner", "infomaniak", "vps", "email", "connection_intent", "nango", "l2"]:
        assert term in text


def test_config_wizard_generates_human_go_proposal_contract():
    build_site()
    text = html(PUBLIC / "config" / "index.html")
    expected_fields = [
        'id="company_name"',
        'id="activity"',
        'id="contact_email"',
        'id="domain_status"',
        'id="primary_goal"',
        'id="urgency"',
        'id="budget"',
        'id="pack"',
        'id="location"',
        'id="backups"',
    ]
    for field in expected_fields:
        assert field in text
    for marker in [
        "configuration_proposal",
        "pending_human_go",
        "hetzner_payload",
        "apps_l1",
        "Télécharger la proposition JSON",
        "Enregistrer la proposition",
        "/api/proposals",
        "/api/hetzner/pricing",
    ]:
        assert marker in text
    assert 'src="/assets/app.js"' in text


def test_build_exports_packs_and_l1_apps_json_for_hub_top_chain():
    build_site()
    packs_path = PUBLIC / "api" / "oa-start-packs.json"
    apps_path = PUBLIC / "api" / "apps-l1.json"
    assert packs_path.exists()
    assert apps_path.exists()
    packs = packs_path.read_text(encoding="utf-8").lower()
    apps = apps_path.read_text(encoding="utf-8").lower()
    for term in ["starter", "pro", "max", "hetzner", "monthly_total_eur", "pending_human_go"]:
        assert term in packs
    for app in ["ubuntu", "ssh", "ufw", "tailscale", "caddy", "hub", "hermes-agent", "secrets", "backups", "qg-reporting"]:
        assert app in apps


def test_appomar_lifecycle_and_shared_system_contracts_are_public_safe():
    build_site()
    lifecycle_path = PUBLIC / "api" / "appomar-lifecycle.json"
    system_path = PUBLIC / "api" / "oa-system-contracts.json"
    assert lifecycle_path.exists()
    assert system_path.exists()
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    system = json.loads(system_path.read_text(encoding="utf-8"))
    assert lifecycle["schema"] == "oa.appomar-lifecycle/v1"
    assert lifecycle["commercial_policy"]["payment_copy_changed"] is False
    assert lifecycle["commercial_policy"]["payment_provider_changed"] is False
    steps = [item["id"] for item in lifecycle["lifecycle"]]
    assert steps == [
        "promise",
        "audit_conversationnel",
        "report_proposals",
        "quote_validation",
        "onboarding",
        "hub_client_bootstrap",
        "sav",
    ]
    assert lifecycle["interfaces"]["qg"]["allowed_states"] == ["audit_started", "report_ready", "devis_draft", "onboarding_ready", "hub_pending", "sav_open"]
    assert all(action["status"] == "gated" for action in lifecycle["actions"] if action["mode"] == "apply")
    assert system["schema"] == "oa.system-contracts/v1"
    page_ids = {item["id"] for item in system["page_contracts"]["items"]}
    assert "appomar.lifecycle" in page_ids
    serialized = lifecycle_path.read_text(encoding="utf-8") + system_path.read_text(encoding="utf-8")
    for forbidden in ["BEGIN OPENSSH", "ghp_", "sk-proj-", "-----BEGIN", "Authorization:"]:
        assert forbidden not in serialized


def test_config_javascript_builds_proposal_without_paid_autoprovisioning():
    build_site()
    js = (PUBLIC / "assets" / "app.js").read_text(encoding="utf-8")
    for term in [
        "configuration_proposal",
        "pending_human_go",
        "hetzner_payload",
        "create_server_payload",
        "apps_l1",
        "monthly_total_eur",
        "/api/proposals",
        "/api/hetzner/pricing",
        "proposal_status",
    ]:
        assert term in js
    forbidden = ["fetch('https://api.hetzner.cloud", 'fetch("https://api.hetzner.cloud', "POST /servers"]
    for term in forbidden:
        assert term not in js


def test_account_and_security_boundaries_are_visible():
    build_site()
    text = html(PUBLIC / "compte" / "index.html").lower()
    for term in ["multi-tenant", "ne voit que ses données", "rôles", "aucun secret", "infisical", "hermes agent vault"]:
        assert term in text


def test_onboarding_pc_option_has_reproducible_smoke_contract():
    text = (ROOT / "pages-app" / "onboarding.html").read_text(encoding="utf-8")
    for term in [
        'value="pc"',
        'value="hybride"',
        "Option PC promise",
        "pcSmokeStatus",
        "pc_smoke",
        "pc_smoke_checklist",
        "droits_admin",
        "tailscale_ou_reseau",
        "docker_ou_runner_local",
        "infra: d.infra",
        "infra_preference",
        "deviceObjects",
        "device_labels",
        "state: \"inconnu\"",
        "devices",
    ]:
        assert term in text


def test_connector_readiness_json_and_account_surface_expose_catalogue_statuses():
    build_site()
    api_path = PUBLIC / "api" / "connector-readiness.json"
    assert api_path.exists()
    data = __import__("json").loads(api_path.read_text(encoding="utf-8"))
    assert data["schema"] == "appomar.connector_readiness.v1"
    assert data["status_vocabulary"] == ["potential", "configured", "proven", "unknown"]
    assert data["safety"]["secrets_exposed"] is False
    assert data["safety"]["client_details_exposed"] is False
    assert data["safety"]["internal_responsibles_exposed"] is False
    assert data["safety"]["infra_state_exposed"] is False
    assert data["safety"]["public_payload_anonymized"] is True
    assert data["safety"]["proven_requires_measured_or_read_proof"] is True
    assert len(data["items"]) >= 6
    seen = {item["classification"] for item in data["items"]}
    assert {"potential", "configured", "unknown"}.issubset(seen)
    for item in data["items"]:
        assert set(item) == {"capability", "classification", "proof", "gap"}
        assert item["classification"] in data["status_vocabulary"]
        assert item["proof"]
        assert item["gap"]
    public_text = api_path.read_text(encoding="utf-8").lower()
    for forbidden in ["jab", "t_d76b3974", "vhost", "callback absent", "nango_jab", "oa-vps-operator", "h-omar", "owner", "blocked"]:
        assert forbidden not in public_text
    compte = html(PUBLIC / "compte" / "index.html").lower()
    for term in [
        "readiness connecteurs",
        "potential",
        "configured",
        "unknown",
        "preuve publique",
        "next action",
        "/api/connector-readiness.json",
        "public anonymisé",
    ]:
        assert term in compte
    for forbidden in ["jab", "t_d76b3974", "vhost", "callback absent", "nango_jab", "oa-vps-operator", "h-omar", "owner", "blocked"]:
        assert forbidden not in compte


def test_jab_plan_is_not_part_of_public_build():
    build_site()
    assert not (PUBLIC / "jab" / "index.html").exists()
    all_public_html = "\n".join(path.read_text(encoding="utf-8").lower() for path in PUBLIC.rglob("*.html"))
    for forbidden in ["cabinet bouboutou", "jab", "t_d76b3974"]:
        assert forbidden not in all_public_html


def test_fable_business_docs_do_not_reintroduce_pilot_client_details():
    business_docs = ROOT / "docs" / "fable" / "business"
    assert business_docs.exists()
    forbidden_files = [
        business_docs / "maryse-audit-script.md",
        business_docs / "maryse-cailloux-hypotheses.md",
        business_docs / "maryse-readiness-questions.md",
    ]
    for path in forbidden_files:
        assert not path.exists(), f"pilot-client doc must stay out of repo: {path}"

    scoped_files = [
        business_docs / "agent-secretaire-profile.md",
        business_docs / "local-pc-vps-checklist.md",
        business_docs / "onboarding-after-audit.md",
        business_docs / "audit-output-schema.json",
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in scoped_files)
    forbidden_patterns = {
        "pilot-person-name": r"\bmaryse\b",
        "pilot-client-label": r"client[- ]pilote",
        "pilot-business-profile": r"consultante\s+boulangerie|consultante\s+aupr[eè]s\s+de\s+boulangeries",
        "pilot-machine-profile": r"maryse-pc|h-maryse|clients/maryse|omar-top/profiles/",
        "operational-client-tooling": r"rustdesk|pc windows",
    }
    for label, pattern in forbidden_patterns.items():
        assert not re.search(pattern, text), label


def test_onboarding_frontend_exposes_resume_autosave_and_simulation_console():
    text = (ROOT / "pages-app" / "onboarding.html").read_text(encoding="utf-8")
    for term in [
        "record_id",
        "resume_url",
        "completed_sections",
        "autosaveOnboarding",
        "loadOnboardingRecord",
        "simulateConfiguration",
        "normalizeInfraTarget",
        "vps_managé\":\"vps",
        "inconnu:\"vps",
        "/api/onboarding/",
        "/simulate",
        "Simuler la configuration",
        "Reprise activée",
        "paid_actions",
        "none",
    ]:
        assert term in text


def test_changelog_contract_is_internal_not_public_for_now():
    build_site()
    contract = (ROOT / "APP_CONTRACT.md").read_text(encoding="utf-8").lower()
    assert "changelog" in contract
    assert "non public" in contract
    assert "accès interne/authentifié" in contract


def test_no_secret_like_literals_are_exposed():
    build_site()
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC.rglob("*.html"))
    forbidden = [r"sk-[A-Za-z0-9]", r"plane_api_[a-f0-9]", r"BEGIN (RSA|OPENSSH) PRIVATE KEY", r"POSTGRES_PASSWORD="]
    for pattern in forbidden:
        assert not re.search(pattern, all_text), pattern


def test_caddy_protects_multitenant_api_before_generic_api_bypass():
    """Les endpoints qui consomment X-Auth-Request-Email doivent passer par
    forward_auth avant le handle générique /api/*, sinon le header est forgeable.
    """
    caddy = (ROOT / "deploy" / "app.omar.paris.caddy").read_text(encoding="utf-8")
    generic_pos = caddy.index("handle /api/*")
    for route in ("/api/onboarding/status", "/api/sav/status"):
        block_start = caddy.index(f"handle {route}")
        assert block_start < generic_pos
        block = caddy[block_start:generic_pos]
        assert "forward_auth 127.0.0.1:4180" in block
        assert "copy_headers X-Auth-Request-User X-Auth-Request-Email" in block


def test_caddy_keeps_audit_public_but_devis_and_changelog_authenticated():
    caddy = (ROOT / "deploy" / "app.omar.paris.caddy").read_text(encoding="utf-8")
    assert "handle /audit*" in caddy
    audit_block = caddy[caddy.index("handle /audit*"):caddy.index("handle /onboarding*")]
    assert "forward_auth" not in audit_block
    assert "Tout le portail (/, /devis/, /onboarding/, /sav/, /compte/, /aide/, /changelog/, /admin/…)" in caddy
    assert "handle /devis*" not in caddy
    assert "handle /changelog*" not in caddy


def test_devis_page_does_not_claim_payment_validated_when_provider_unconfigured():
    build_site()
    text = html(PUBLIC / "devis" / "index.html").lower()
    assert "paiement validé" not in text
    assert "continuer vers paypal" not in text
    assert "paypal cible" not in text


def test_public_payment_copy_does_not_publish_specific_provider_target():
    build_site()
    public_paths = [
        PUBLIC / "index.html",
        PUBLIC / "audit" / "index.html",
        PUBLIC / "devis" / "index.html",
        PUBLIC / "aide" / "index.html",
        PUBLIC / "compte" / "index.html",
        PUBLIC / "onboarding" / "index.html",
        PUBLIC / "api" / "appomar-lifecycle.json",
    ]
    joined = "\n".join(p.read_text(encoding="utf-8").lower() for p in public_paths)
    assert "paypal" not in joined
    assert "stripe test" not in joined
    assert "paiement test" not in joined
    assert "paid_test" not in joined
    assert "paiement validé" not in joined
    assert "portail client stripe" not in joined

def test_audit_tree_validator_contract_passes():
    result = subprocess.run(
        ["python3", "scripts/audit_tree_validator.py"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "pass"
    assert not report["failures"]


def test_audit_page_requires_omar_mini_story_validation_after_public_research():
    build_site()
    raw = html(PUBLIC / "audit" / "index.html")
    compact = re.sub(r"\s+", "", raw)

    assert "function buildOmarMiniStory" in raw
    assert "confirm_omar_story" in raw
    assert "Récit Omar à valider" in raw
    assert "Valider le récit Omar" in raw
    assert "buildOmarMiniStory(result)" in compact
    assert "intent==='confirm_omar_story'" in compact
