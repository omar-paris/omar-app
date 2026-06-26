from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

ROUTES = {
    "/": PUBLIC / "index.html",
    "/onboarding": PUBLIC / "onboarding" / "index.html",
    "/devis": PUBLIC / "buy" / "index.html",  # /buy/ built from site_data, redirected at runtime
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


def test_navigation_links_are_real_direct_urls():
    build_site()
    text = html(PUBLIC / "index.html")
    for route in ["/onboarding/", "/devis/", "/sav/", "/compte/", "/changelog/"]:
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
        "infra_preference",
        "devices",
    ]:
        assert term in text


def test_changelog_exists_and_no_secret_like_literals_are_exposed():
    build_site()
    changelog = html(PUBLIC / "changelog" / "index.html")
    assert "V0.1.0" in changelog
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
