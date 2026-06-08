#!/usr/bin/env python3
from __future__ import annotations

from html import escape
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from site_data import DOMAIN, NAV, PAGES, PUBLISHED, VERSION  # noqa: E402

PUBLIC = ROOT / "public"

CSS = """
:root{--bg:#f8fafc;--surface:#ffffff;--ink:#0f172a;--muted:#475569;--line:#cbd5e1;--primary:#0f766e;--primary-ink:#ffffff;--accent:#1d4ed8;--soft:#ecfeff;--warn:#fff7ed;--radius:18px}*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:linear-gradient(135deg,#f8fafc,#eef2ff);color:var(--ink);line-height:1.55}a{color:var(--accent)}header{position:sticky;top:0;background:rgba(255,255,255,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);z-index:2}.bar{max-width:1180px;margin:auto;padding:16px 20px;display:flex;gap:18px;align-items:center;justify-content:space-between}.brand{font-weight:900;letter-spacing:-.04em}.meta{font-size:12px;color:var(--muted);font-weight:700}.nav{display:flex;gap:8px;flex-wrap:wrap}.nav a{padding:8px 11px;border:1px solid var(--line);border-radius:999px;text-decoration:none;background:#fff;color:#0f172a;font-size:13px;font-weight:750}.nav a.active{background:var(--ink);color:#fff;border-color:var(--ink)}main{max-width:1180px;margin:0 auto;padding:42px 20px 80px}.hero{display:grid;grid-template-columns:1.25fr .75fr;gap:24px;align-items:stretch}.card,.hero-main{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:0 20px 50px rgba(15,23,42,.08)}.hero-main{padding:38px}.eyebrow{color:var(--primary);font-weight:900;text-transform:uppercase;font-size:13px;letter-spacing:.08em}.h1{font-size:clamp(34px,5vw,64px);line-height:.98;margin:12px 0;letter-spacing:-.06em}.summary{font-size:20px;color:#334155;max-width:760px}.actions{margin-top:28px;display:flex;gap:12px;flex-wrap:wrap}.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:900;border:1px solid var(--line);background:#fff;color:var(--ink)}.btn.primary{background:var(--primary);color:var(--primary-ink);border-color:var(--primary)}.side{padding:24px}.status{display:grid;gap:12px}.pill{padding:12px;border-radius:14px;border:1px solid var(--line);background:#f8fafc}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:22px}.card{padding:24px}.card h2{margin:0 0 12px;letter-spacing:-.03em}.card ul{margin:0;padding-left:20px;color:#334155}.route-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:24px}.route{padding:14px;border:1px solid var(--line);border-radius:14px;background:#fff;text-decoration:none;color:var(--ink)}.route strong{display:block}.route span{color:var(--muted);font-size:13px}.footer{border-top:1px solid var(--line);padding:24px 20px;color:var(--muted);font-size:13px;text-align:center}@media(max-width:820px){.hero{grid-template-columns:1fr}.bar{align-items:flex-start;flex-direction:column}.grid{grid-template-columns:1fr}.hero-main{padding:24px}.nav a{font-size:12px}}
"""


def route_to_file(route: str) -> Path:
    if route == "/":
        return PUBLIC / "index.html"
    return PUBLIC / route.strip("/") / "index.html"


def render_page(route: str, page: dict) -> str:
    nav_html = "".join(
        f'<a class="{"active" if href == route else ""}" href="{href}">{escape(label)}</a>' for href, label in NAV
    )
    route_cards = "".join(
        f'<a class="route" href="{href}"><strong>{escape(label)}</strong><span>{escape(href)}</span></a>'
        for href, label in NAV if href != route
    )
    sections = "".join(
        "<section class='card'><h2>" + escape(title) + "</h2><ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul></section>"
        for title, items in page["sections"]
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(page['title'])} · Omar App</title>
  <meta name="description" content="{escape(page['summary'])}">
  <link rel="stylesheet" href="/assets/styles.css">
</head>
<body>
<header><div class="bar"><div><div class="brand">Omar App · {DOMAIN}</div><div class="meta">{VERSION} · {PUBLISHED} · CORE OA</div></div><nav class="nav" aria-label="Navigation principale">{nav_html}</nav></div></header>
<main>
  <div class="hero">
    <section class="hero-main">
      <div class="eyebrow">{escape(page['eyebrow'])}</div>
      <h1 class="h1">{escape(page['title'])}</h1>
      <p class="summary">{escape(page['summary'])}</p>
      <div class="actions"><a class="btn primary" href="/onboarding/">Démarrer l’onboarding</a><a class="btn" href="/config/">Voir le wizard config</a></div>
    </section>
    <aside class="card side" aria-label="Statut V0">
      <h2>Statut V0</h2>
      <div class="status">
        <div class="pill"><strong>Portail client</strong><br>Skeleton local-first, routes directes.</div>
        <div class="pill"><strong>Sécurité</strong><br>Multi-tenant cible, aucun secret exposé.</div>
        <div class="pill"><strong>Prochaine étape</strong><br>Brancher données, assistant, puis QG registry.</div>
      </div>
    </aside>
  </div>
  <div class="grid">{sections}</div>
  <section class="card" style="margin-top:22px"><h2>Routes</h2><div class="route-list">{route_cards}</div></section>
</main>
<footer class="footer">Omar App · {DOMAIN} · {VERSION} · Changelog disponible · Aucun secret client dans cette V0.</footer>
</body>
</html>"""


def main() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "assets").mkdir(parents=True)
    (PUBLIC / "assets" / "styles.css").write_text(CSS, encoding="utf-8")
    for route, page in PAGES.items():
        out = route_to_file(route)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_page(route, page), encoding="utf-8")
    print(f"built {len(PAGES)} routes into {PUBLIC}")


if __name__ == "__main__":
    main()
