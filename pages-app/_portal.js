// _portal.js — header/nav unifié + helpers, partagé par toutes les pages du portail OA App.
// Injecté en haut de chaque page. Source unique de la navigation.
(function () {
  const NAV = [
    { href: "/devis/", label: "Devis" },
    { href: "/onboarding/", label: "Onboarding" },
    { href: "/sav/", label: "SAV" },
    { href: "/compte/", label: "Compte" },
  ];
  const path = location.pathname.replace(/\/$/, "/") ;
  const links = NAV.map(n => {
    const active = path.startsWith(n.href) ? ' aria-current="page"' : "";
    return `<a href="${n.href}"${active}>${n.label}</a>`;
  }).join("");
  const header = `
  <header class="oa-hd"><div class="oa-bar">
    <a class="oa-brand" href="/">Omar&nbsp;App<span>app.omar.paris</span></a>
    <nav class="oa-nav">${links}</nav>
    <div class="oa-ico">
      <a href="/aide/" title="Aide — quoi faire ?" class="oa-i">?</a>
      <a href="/changelog/" title="Changelog" class="oa-i">⟲</a>
    </div>
  </div></header>`;
  const style = `<style>
  :root{--ink:#0f172a;--muted:#64748b;--line:#e5e7eb;--pri:#2563eb;--bg:#f8fafc}
  *{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,sans-serif;color:var(--ink);background:var(--bg);line-height:1.5}
  a{color:var(--pri);text-decoration:none}
  .oa-hd{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
  .oa-bar{max-width:1100px;margin:auto;padding:12px 20px;display:flex;align-items:center;gap:18px}
  .oa-brand{font-weight:800;letter-spacing:-.03em;color:var(--ink)}.oa-brand span{display:block;font-size:11px;font-weight:500;color:var(--muted)}
  .oa-nav{display:flex;gap:6px;margin-left:8px}
  .oa-nav a{padding:7px 13px;border-radius:999px;font-size:14px;font-weight:600;color:#334155}
  .oa-nav a[aria-current]{background:var(--ink);color:#fff}
  .oa-nav a:hover:not([aria-current]){background:#eef2f7}
  .oa-ico{margin-left:auto;display:flex;gap:6px}
  .oa-i{width:32px;height:32px;display:flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:15px;background:#fff}
  .oa-i:hover{border-color:var(--pri);color:var(--pri)}
  main{max-width:1100px;margin:0 auto;padding:32px 20px 80px}
  .h1{font-size:clamp(28px,4vw,42px);letter-spacing:-.04em;margin:0 0 6px}
  .sub{font-size:17px;color:var(--muted);margin:0 0 22px;max-width:680px}
  .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
  .btn{display:inline-flex;align-items:center;gap:8px;padding:11px 18px;border-radius:11px;font-weight:700;font-size:14px;border:1px solid var(--line);background:#fff;color:var(--ink);cursor:pointer}
  .btn.pri{background:var(--pri);color:#fff;border-color:var(--pri)}
  </style>`;
  document.head.insertAdjacentHTML("beforeend", style);
  document.body.insertAdjacentHTML("afterbegin", header);
})();
