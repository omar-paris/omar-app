#!/usr/bin/env python3
from __future__ import annotations

from html import escape
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from site_data import APPS_L1, DOMAIN, NAV, OA_START_PACKS, PAGES, PUBLISHED, VERSION  # noqa: E402

PUBLIC = ROOT / "public"

CSS = """
:root{--bg:#f8fafc;--surface:#ffffff;--ink:#0f172a;--muted:#475569;--line:#cbd5e1;--primary:#0f766e;--primary-ink:#ffffff;--accent:#1d4ed8;--soft:#ecfeff;--warn:#fff7ed;--radius:18px}*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:linear-gradient(135deg,#f8fafc,#eef2ff);color:var(--ink);line-height:1.55}a{color:var(--accent)}header{position:sticky;top:0;background:rgba(255,255,255,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);z-index:2}.bar{max-width:1180px;margin:auto;padding:16px 20px;display:flex;gap:18px;align-items:center;justify-content:space-between}.brand{font-weight:900;letter-spacing:-.04em}.meta{font-size:12px;color:var(--muted);font-weight:700}.nav{display:flex;gap:8px;flex-wrap:wrap}.nav a{padding:8px 11px;border:1px solid var(--line);border-radius:999px;text-decoration:none;background:#fff;color:#0f172a;font-size:13px;font-weight:750}.nav a.active{background:var(--ink);color:#fff;border-color:var(--ink)}main{max-width:1180px;margin:0 auto;padding:42px 20px 80px}.hero{display:grid;grid-template-columns:1.25fr .75fr;gap:24px;align-items:stretch}.card,.hero-main{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:0 20px 50px rgba(15,23,42,.08)}.hero-main{padding:38px}.eyebrow{color:var(--primary);font-weight:900;text-transform:uppercase;font-size:13px;letter-spacing:.08em}.h1{font-size:clamp(34px,5vw,64px);line-height:.98;margin:12px 0;letter-spacing:-.06em}.summary{font-size:20px;color:#334155;max-width:760px}.actions{margin-top:28px;display:flex;gap:12px;flex-wrap:wrap}.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:900;border:1px solid var(--line);background:#fff;color:var(--ink)}.btn.primary{background:var(--primary);color:var(--primary-ink);border-color:var(--primary)}.side{padding:24px}.status{display:grid;gap:12px}.pill{padding:12px;border-radius:14px;border:1px solid var(--line);background:#f8fafc}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:22px}.card{padding:24px}.card h2{margin:0 0 12px;letter-spacing:-.03em}.card ul{margin:0;padding-left:20px;color:#334155}.route-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:24px}.route{padding:14px;border:1px solid var(--line);border-radius:14px;background:#fff;text-decoration:none;color:var(--ink)}.route strong{display:block}.route span{color:var(--muted);font-size:13px}.footer{border-top:1px solid var(--line);padding:24px 20px;color:var(--muted);font-size:13px;text-align:center}@media(max-width:820px){.hero{grid-template-columns:1fr}.bar{align-items:flex-start;flex-direction:column}.grid{grid-template-columns:1fr}.hero-main{padding:24px}.nav a{font-size:12px}}
"""

CSS += """
.wizard-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:18px}.wizard-form fieldset{border:1px solid var(--line);border-radius:16px;padding:18px;background:#f8fafc}.wizard-form legend{font-weight:900;color:var(--primary);padding:0 6px}.wizard-form label{display:block;margin-top:10px;font-weight:800;color:#334155}.wizard-form input,.wizard-form select,.wizard-form textarea{width:100%;margin-top:6px;padding:11px 12px;border:1px solid var(--line);border-radius:12px;background:#fff;color:var(--ink);font:inherit}.wizard-form textarea{min-height:86px;resize:vertical}.wizard-form .check{display:flex;gap:10px;align-items:flex-start}.wizard-form .check input{width:auto;margin-top:4px}.apps-l1 li{display:flex;justify-content:space-between;gap:14px;border-bottom:1px solid #e2e8f0;padding:8px 0}.apps-l1 span{color:var(--muted);font-size:13px}.proposal-output{max-height:520px;overflow:auto;padding:16px;border-radius:14px;background:#0f172a;color:#e2e8f0;font-size:13px;line-height:1.45}@media(max-width:980px){.wizard-form{grid-template-columns:1fr}.apps-l1 li{display:block}}
"""

CSS += """
.plan-board{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:24px}.plan-col{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 12px 30px rgba(15,23,42,.06)}.plan-col h2{margin:0 0 12px;font-size:17px;letter-spacing:-.02em;display:flex;align-items:center;gap:8px}.plan-action{border:1px solid var(--line);border-radius:12px;padding:11px 12px;margin-bottom:10px;background:#fbfdff}.plan-action .t{font-weight:800;font-size:14px}.plan-action .d{color:var(--muted);font-size:12.5px;margin-top:3px}.plan-status{display:inline-block;margin-top:8px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:2px 9px;border-radius:999px}.st-fait{background:#dcfce7;color:#166534}.st-encours{background:#fef9c3;color:#854d0e}.st-afaire{background:#e2e8f0;color:#334155}.st-gate{background:#fee2e2;color:#991b1b}@media(max-width:980px){.plan-board{grid-template-columns:1fr}}
"""

APP_JS = r"""
const PACKS = __PACKS__;
const APPS_L1 = __APPS_L1__;

function value(id) {
  const node = document.getElementById(id);
  if (!node) return "";
  if (node.type === "checkbox") return node.checked;
  return node.value.trim();
}

function selectedPack() {
  const packId = value("pack") || "starter";
  return PACKS.find((pack) => pack.id === packId) || PACKS[0];
}

function buildProposal() {
  const pack = selectedPack();
  const backups = value("backups");
  const tenant = (value("company_name") || "client-demo").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "client-demo";
  const proposal = {
    schema: "configuration_proposal.v0",
    type: "configuration_proposal",
    status: "pending_human_go",
    generated_by: "app.omar.paris/config V0.3.0",
    client_profile: {
      company_name: value("company_name"),
      activity: value("activity"),
      contact_email: value("contact_email"),
      domain_status: value("domain_status"),
      primary_goal: value("primary_goal"),
      urgency: value("urgency"),
      budget: value("budget"),
      existing_tools: value("existing_tools")
    },
    pack: {
      id: pack.id,
      label: pack.label,
      provider: pack.provider,
      monthly_total_eur: pack.monthly_total_eur,
      note: pack.note
    },
    hetzner_payload: {
      mode: "dry_run_no_paid_resource",
      status: "pending_human_go",
      create_server_payload: {
        name: `oa-client-${tenant}-01`,
        server_type: pack.server_type,
        fallback_server_type: pack.fallback_server_type,
        image: pack.image,
        location: value("location") || pack.location,
        backups,
        labels: {
          oa: "client",
          oa_client: tenant,
          oa_pack: pack.id,
          managed_by: "hermes"
        },
        user_data: "#cloud-config\\npackage_update: true\\n"
      }
    },
    apps_l1: APPS_L1.map((app) => ({...app, install_state: "expected"})),
    hub_target: {
      expected_domain: `${tenant}.hub.omar.paris`,
      expected_endpoints: ["/api/vps-context.json", "/api/apps.json"],
      qg_reporting: "pending"
    },
    safety: {
      paid_actions: "none",
      human_go_required_before: ["hcloud_create_server_api", "enable_backup", "DNS cutover", "client data import"]
    }
  };
  return proposal;
}

function renderProposal() {
  const proposal = buildProposal();
  const output = document.getElementById("proposal_output");
  const download = document.getElementById("proposal_download");
  if (!output || !download) return;
  const text = JSON.stringify(proposal, null, 2);
  output.textContent = text;
  const blob = new Blob([text], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  download.href = url;
  download.download = `${proposal.hetzner_payload.create_server_payload.name}-configuration-proposal.json`;
}

async function saveProposal() {
  const status = document.getElementById("proposal_status");
  if (status) status.textContent = "Enregistrement en cours…";
  try {
    const response = await fetch("/api/proposals", {
      method: "POST",
      headers: {"content-type": "application/json"},
      body: JSON.stringify(buildProposal())
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    if (status) status.textContent = `Proposition enregistrée : ${data.proposal.id}`;
  } catch (error) {
    if (status) status.textContent = `Stockage indisponible : ${error.message}`;
  }
}

async function loadPricing() {
  const status = document.getElementById("pricing_status");
  if (!status) return;
  try {
    const response = await fetch("/api/hetzner/pricing", {headers: {"accept": "application/json"}});
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    status.textContent = `Pricing Hetzner : ${data.mode}, ${data.packs.length} packs, paid_actions=${data.paid_actions}`;
  } catch (error) {
    status.textContent = `Pricing Hetzner indisponible : ${error.message}`;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("#config_wizard input, #config_wizard select, #config_wizard textarea").forEach((node) => {
    node.addEventListener("input", renderProposal);
    node.addEventListener("change", renderProposal);
  });
  document.getElementById("proposal_save")?.addEventListener("click", saveProposal);
  renderProposal();
  loadPricing();
});
"""


def route_to_file(route: str) -> Path:
    if route == "/":
        return PUBLIC / "index.html"
    return PUBLIC / route.strip("/") / "index.html"


def render_config_wizard() -> str:
    pack_options = "".join(
        f'<option value="{escape(pack["id"])}">{escape(pack["label"])} · {escape(pack["server_type"])} · ~{pack["monthly_total_eur"]:.0f}€/mois</option>'
        for pack in OA_START_PACKS
    )
    apps = "".join(
        f'<li><strong>{escape(app["name"])}</strong><span>{escape(app["slug"])} · expected · {escape(app["source"])}</span></li>'
        for app in APPS_L1
    )
    return f"""
  <section class="card wizard" id="configuration_proposal" style="margin-top:22px">
    <h2>Wizard config V0.3 — Pack OA Start</h2>
    <p>Ce wizard prépare une proposition exploitable. Il ne crée aucun VPS : statut <strong>pending_human_go</strong> avant tout coût Hetzner.</p>
    <form id="config_wizard" class="wizard-form">
      <fieldset><legend>1. Entreprise</legend>
        <label for="company_name">Entreprise</label><input id="company_name" name="company_name" value="Client Démo" required>
        <label for="activity">Activité</label><input id="activity" name="activity" value="Artisan / TPE">
        <label for="contact_email">Email contact</label><input id="contact_email" name="contact_email" type="email" value="client@example.com">
        <label for="domain_status">Domaine</label><select id="domain_status" name="domain_status"><option>à acheter</option><option>existant à connecter</option><option>à décider</option></select>
      </fieldset>
      <fieldset><legend>2. Besoin</legend>
        <label for="primary_goal">Objectif principal</label><input id="primary_goal" name="primary_goal" value="gagner du temps et mieux répondre aux clients">
        <label for="urgency">Urgence</label><select id="urgency" name="urgency"><option>cette semaine</option><option>ce mois-ci</option><option>exploration</option></select>
        <label for="budget">Budget indicatif</label><select id="budget" name="budget"><option>Starter</option><option>Pro</option><option>Max</option></select>
        <label for="existing_tools">Outils existants</label><textarea id="existing_tools" name="existing_tools">Email, domaine, documents, factures</textarea>
      </fieldset>
      <fieldset><legend>3. VPS Hetzner dry-run</legend>
        <label for="pack">Pack</label><select id="pack" name="pack">{pack_options}</select>
        <label for="location">Région</label><select id="location" name="location"><option value="fsn1">fsn1</option><option value="nbg1">nbg1</option><option value="hel1">hel1</option></select>
        <label class="check" for="backups"><input id="backups" name="backups" type="checkbox" checked> Backups Hetzner inclus dans l’estimation</label>
      </fieldset>
    </form>
  </section>
  <section class="card" id="apps_l1" style="margin-top:22px">
    <h2>Apps L1 attendues</h2>
    <ul class="apps-l1">{apps}</ul>
  </section>
  <section class="card" style="margin-top:22px">
    <h2>Sortie opérateur</h2>
    <p><strong>hetzner_payload</strong> contient un <strong>create_server_payload</strong> dry-run. Validation humaine obligatoire avant POST /servers.</p>
    <div class="actions"><a class="btn primary" id="proposal_download" href="#">Télécharger la proposition JSON</a><button class="btn" id="proposal_save" type="button">Enregistrer la proposition</button></div>
    <p id="pricing_status" class="meta">Pricing Hetzner : chargement /api/hetzner/pricing…</p>
    <p id="proposal_status" class="meta">Stockage serveur prêt via /api/proposals.</p>
    <pre id="proposal_output" class="proposal-output" aria-label="configuration_proposal JSON"></pre>
  </section>
"""


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
    extra = render_config_wizard() if route == "/config/" else ""
    script = '<script src="/assets/app.js" defer></script>' if route == "/config/" else ""
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
{extra}
  <section class="card" style="margin-top:22px"><h2>Routes</h2><div class="route-list">{route_cards}</div></section>
</main>
<footer class="footer">Omar App · {DOMAIN} · {VERSION} · Changelog disponible · Aucun secret client dans cette V0.</footer>
{script}
</body>
</html>"""


_STATUS_META = {
    "fait": ("st-fait", "fait"),
    "en cours": ("st-encours", "en cours"),
    "a_faire": ("st-afaire", "à faire"),
    "gate": ("st-gate", "gaté"),
}


def render_jab_plan() -> str | None:
    """Page /jab : 4 colonnes (Omar/Edilia/JA/Alex) alimentées par data/plan-jab.yaml."""
    data_file = ROOT / "data" / "plan-jab.yaml"
    if not data_file.exists():
        print("WARN: data/plan-jab.yaml absent — page /jab non générée")
        return None
    try:
        import yaml  # PyYAML
        data = yaml.safe_load(data_file.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: lecture plan-jab.yaml échouée ({exc}) — page /jab non générée")
        return None

    meta = data.get("meta", {})
    route = "/jab/"
    nav_html = "".join(
        f'<a class="{"active" if href == route else ""}" href="{href}">{escape(label)}</a>' for href, label in NAV
    )
    cols_html = ""
    for col in data.get("colonnes", []):
        actions_html = ""
        for act in col.get("actions", []):
            cls, lbl = _STATUS_META.get(act.get("statut", "a_faire"), ("st-afaire", "à faire"))
            detail = act.get("detail", "")
            actions_html += (
                "<div class='plan-action'>"
                f"<div class='t'>{escape(act.get('titre',''))}</div>"
                + (f"<div class='d'>{escape(detail)}</div>" if detail else "")
                + f"<span class='plan-status {cls}'>{escape(lbl)}</span></div>"
            )
        cols_html += (
            "<div class='plan-col'>"
            f"<h2>{escape(col.get('icon',''))} {escape(col.get('label',''))}</h2>"
            f"{actions_html}</div>"
        )
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(meta.get('title','Plan JAB'))} · Omar App</title>
  <meta name="description" content="{escape(meta.get('summary',''))}">
  <link rel="stylesheet" href="/assets/styles.css">
</head>
<body>
<header><div class="bar"><div><div class="brand">Omar App · {DOMAIN}</div><div class="meta">{VERSION} · {PUBLISHED} · CORE OA</div></div><nav class="nav" aria-label="Navigation principale">{nav_html}</nav></div></header>
<main>
  <div class="hero">
    <section class="hero-main">
      <div class="eyebrow">{escape(meta.get('eyebrow',''))}</div>
      <h1 class="h1">{escape(meta.get('title','Plan JAB'))}</h1>
      <p class="summary">{escape(meta.get('summary',''))}</p>
      <div class="meta">Mis à jour : {escape(meta.get('updated',''))} · source éditable : data/plan-jab.yaml</div>
    </section>
    <aside class="card side" aria-label="Légende">
      <h2>Légende</h2>
      <div class="status">
        <div class="pill"><span class="plan-status st-fait">fait</span> livré et vérifié</div>
        <div class="pill"><span class="plan-status st-encours">en cours</span> démarré</div>
        <div class="pill"><span class="plan-status st-afaire">à faire</span> planifié</div>
        <div class="pill"><span class="plan-status st-gate">gaté</span> attend une décision/clé</div>
      </div>
    </aside>
  </div>
  <div class="plan-board">{cols_html}</div>
</main>
<footer class="footer">Omar App · {DOMAIN} · {VERSION} · Plan d'actions JAB · données dans data/plan-jab.yaml.</footer>
</body>
</html>"""


def write_api_assets() -> None:
    api = PUBLIC / "api"
    api.mkdir(parents=True, exist_ok=True)
    packs_payload = {
        "schema": "oa_start_packs.v0",
        "status": "pending_human_go",
        "provider": "hetzner",
        "packs": OA_START_PACKS,
        "safety": "No paid resource creation without explicit human GO.",
    }
    apps_payload = {
        "schema": "apps_l1.v0",
        "source": "OmarTop L1 draft → AppOmar → Hub",
        "install_state_default": "expected",
        "apps": APPS_L1,
    }
    (api / "oa-start-packs.json").write_text(json.dumps(packs_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (api / "apps-l1.json").write_text(json.dumps(apps_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    app_js = APP_JS.replace("__PACKS__", json.dumps(OA_START_PACKS, ensure_ascii=False)).replace(
        "__APPS_L1__", json.dumps(APPS_L1, ensure_ascii=False)
    )
    (PUBLIC / "assets" / "app.js").write_text(app_js, encoding="utf-8")


def main() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "assets").mkdir(parents=True)
    (PUBLIC / "assets" / "styles.css").write_text(CSS, encoding="utf-8")
    write_api_assets()
    for route, page in PAGES.items():
        out = route_to_file(route)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_page(route, page), encoding="utf-8")
    jab_html = render_jab_plan()
    if jab_html:
        jab_out = PUBLIC / "jab" / "index.html"
        jab_out.parent.mkdir(parents=True, exist_ok=True)
        jab_out.write_text(jab_html, encoding="utf-8")
        print("built /jab/ from data/plan-jab.yaml")
    print(f"built {len(PAGES)} routes into {PUBLIC}")


if __name__ == "__main__":
    main()
