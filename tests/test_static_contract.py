from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

ROUTES = {
    "/": PUBLIC / "index.html",
    "/onboarding": PUBLIC / "onboarding" / "index.html",
    "/config": PUBLIC / "config" / "index.html",
    "/buy": PUBLIC / "buy" / "index.html",
    "/sav": PUBLIC / "sav" / "index.html",
    "/factures": PUBLIC / "factures" / "index.html",
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
        assert "V0.1.0" in text
        assert "app.omar.paris" in text


def test_navigation_links_are_real_direct_urls():
    build_site()
    text = html(PUBLIC / "index.html")
    for route in ["/onboarding/", "/config/", "/buy/", "/sav/", "/factures/", "/compte/", "/changelog/"]:
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


def test_account_and_security_boundaries_are_visible():
    build_site()
    text = html(PUBLIC / "compte" / "index.html").lower()
    for term in ["multi-tenant", "ne voit que ses données", "rôles", "aucun secret", "infisical", "hermes agent vault"]:
        assert term in text


def test_changelog_exists_and_no_secret_like_literals_are_exposed():
    build_site()
    changelog = html(PUBLIC / "changelog" / "index.html")
    assert "V0.1.0" in changelog
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC.rglob("*.html"))
    forbidden = [r"sk-[A-Za-z0-9]", r"plane_api_[a-f0-9]", r"BEGIN (RSA|OPENSSH) PRIVATE KEY", r"POSTGRES_PASSWORD="]
    for pattern in forbidden:
        assert not re.search(pattern, all_text), pattern
