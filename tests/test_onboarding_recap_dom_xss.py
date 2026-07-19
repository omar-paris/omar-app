import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_onboarding_recap_dom_uses_text_nodes_for_audit_prefilled_payloads(tmp_path):
    html = (ROOT / "pages-app" / "onboarding.html").read_text(encoding="utf-8")
    match = re.search(r"<script>(.*?)</script></body></html>", html, flags=re.S)
    assert match, "onboarding script not found"
    script = match.group(1).split("\nrenderBar();\n", 1)[0]
    malicious = '<img src=x onerror="window.__ATHENA_XSS=1"><svg onload="window.__ATHENA_XSS=1"></svg><script>window.__ATHENA_XSS=1</script>'
    harness = tmp_path / "onboarding_recap_harness.mjs"
    harness.write_text(
        """
const values = {
  f_nom: "Prospect Test",
  f_entreprise: PAYLOAD,
  f_activite: PAYLOAD,
  f_email: "safe@example.test",
  f_domaine: "oui",
  f_objectifs_libre: PAYLOAD,
  f_agent_nom: "Omar",
};
class FakeElement {
  constructor(id){ this.id=id; this.value=values[id] || ""; this.checked=false; this.children=[]; this.classList={toggle(){},add(){},remove(){}}; this.style={}; this.dataset={}; }
  appendChild(node){ this.children.push(node); return node; }
  replaceChildren(...nodes){ this.children = nodes; this._html = undefined; }
  querySelector(){ return null; }
  querySelectorAll(){ return []; }
  set textContent(value){ this._text = String(value); }
  get textContent(){ return this._text || ""; }
  set innerHTML(value){
    this._html = String(value);
    if(this.id === "recap" || this.id === "recap_final"){
      if(/<\s*(img|svg|script)\b/i.test(this._html) || /onerror\s*=|onload\s*=/i.test(this._html)){
        window.__ATHENA_XSS = 1;
      }
    }
  }
  get innerHTML(){ return this._html || this.children.map(child => child.textContent || "").join(""); }
}
const elements = {};
function el(id){ return elements[id] ||= new FakeElement(id); }
globalThis.window = { __ATHENA_XSS: 0, scrollTo(){}, location:{search:""} };
globalThis.location = window.location;
globalThis.localStorage = { getItem(){return ""}, setItem(){} };
globalThis.URLSearchParams = URLSearchParams;
globalThis.document = {
  getElementById: el,
  createElement(tag){ const node = new FakeElement(tag); node.tagName = tag.toUpperCase(); return node; },
  createTextNode(text){ const node = new FakeElement("#text"); node.textContent = text; return node; },
  querySelector(){ return null; },
  querySelectorAll(selector){
    if(selector.includes("chips_goals")) return [{value: PAYLOAD, checked:true}];
    if(selector.includes("chips_outils")) return [{value: PAYLOAD, checked:true}];
    if(selector.includes("data-step=\\\"3\\\"")) return [];
    if(selector.includes("data-step=\\\"4\\\"")) return [{value: PAYLOAD, checked:true}];
    return [];
  },
  addEventListener(){},
};
SCRIPT
buildRecap();
const recap = el("recap");
el("recap_final").replaceChildren(...recap.children);
if (window.__ATHENA_XSS !== 0) throw new Error("XSS payload became executable DOM");
if (/<\s*(img|svg|script)\b/i.test(recap.innerHTML)) throw new Error("recap contains executable tags");
if (/<\s*(img|svg|script)\b/i.test(el("recap_final").innerHTML)) throw new Error("recap_final contains executable tags");
""".replace("PAYLOAD", json.dumps(malicious)).replace("SCRIPT", script),
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(harness)], cwd=ROOT, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr + result.stdout
