
const PACKS = [{"id": "starter", "label": "Starter", "provider": "hetzner", "server_type": "cax21", "fallback_server_type": "cpx21", "location": "fsn1", "image": "ubuntu-24.04", "backups_default": true, "monthly_total_eur": 9.0, "status": "pending_human_go", "note": "Profil coût-efficace ARM si compatibilité validée ; x86 fallback cpx21."}, {"id": "pro", "label": "Pro", "provider": "hetzner", "server_type": "cax31", "fallback_server_type": "cpx31", "location": "fsn1", "image": "ubuntu-24.04", "backups_default": true, "monthly_total_eur": 18.0, "status": "pending_human_go", "note": "Profil conseillé pour premier client sérieux avec marge RAM/CPU."}, {"id": "max", "label": "Max", "provider": "hetzner", "server_type": "cax41", "fallback_server_type": "cpx41", "location": "fsn1", "image": "ubuntu-24.04", "backups_default": true, "monthly_total_eur": 36.0, "status": "pending_human_go", "note": "Profil confort ; à valider humainement avant coût récurrent."}];
const APPS_L1 = [{"slug": "ubuntu", "name": "Ubuntu 24.04", "required": true, "source": "OmarTop L1"}, {"slug": "ssh", "name": "SSH admin OA", "required": true, "source": "OmarTop L1"}, {"slug": "ufw", "name": "UFW / firewall", "required": true, "source": "OmarTop L1"}, {"slug": "tailscale", "name": "Tailscale", "required": true, "source": "OmarTop L1"}, {"slug": "caddy", "name": "Caddy + TLS", "required": true, "source": "OmarTop L1"}, {"slug": "hub", "name": "Hub local", "required": true, "source": "OmarTop L1"}, {"slug": "hermes-agent", "name": "Hermes Agent", "required": true, "source": "OmarTop L1"}, {"slug": "secrets", "name": "Secrets Vault/Infisical cible", "required": true, "source": "OmarTop L1"}, {"slug": "backups", "name": "Backups serveur", "required": true, "source": "OmarTop L1"}, {"slug": "qg-reporting", "name": "QG reporting / health", "required": true, "source": "OmarTop L1"}];

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
