# Revenue/AppOmar — daily sales readiness snapshot — 2026-06-30

Status: done
Agent: oa-builder
Stream: revenue_appomar

## Résumé 3 lignes

- AppOmar a déjà un parcours vendable vérifiable: audit IA, onboarding, devis, checkout test/simulation, timeline provisioning et `agent_spec`.
- Smoke builder local OK: `python3 scripts/build.py && python3 -m pytest -q tests/test_static_contract.py tests/test_proposal_server.py tests/test_auditbiz_schema.py` -> built 10 routes, 32 passed.
- Deux blocages conversion à arbitrer avant trafic froid: CTA public vers `/audit/` protégé OAuth, et prix public landing 80 €/mois vs catalogue AppOmar 49/99 €/mois.

## Preuves consommées

| Source | Preuve utile revenue |
|---|---|
| `/home/omar/23-Offre/actifs/omar-app/APP_CONTRACT.md` | JTBD A→Z: onboarding conversationnel -> devis -> Stripe test/simulation -> provisioning timeline -> `agent_spec`. |
| `/home/omar/23-Offre/actifs/omar-app/catalog.json` | Starter 49 €/mois, Pro 99 €/mois, onboarding 150 € unique, SAV 60 € unique. |
| `/home/omar/23-Offre/actifs/omar-landing/public/tarifs/index.html` | Landing annonce « à partir de 80 €/mois » et CTA vers `https://app.omar.paris/audit/`. |
| Live headers | `/`, `/audit/`, `/devis/`, `/onboarding/` retournent 302 vers `/oauth2/start?...` avant contenu. |

## Offre vendable recommandée maintenant

Nom: Audit IA Omar & Alex -> Devis AppOmar

Promesse: en 15 minutes, produire un diagnostic IA exploitable puis un devis Omar App, sans action payante automatique.

CTA: Démarrer l’audit IA puis composer le devis.

Mode sécurité: `paid_actions=none`, Stripe test/simulation, provisioning `pending_go`.

## Points qui aident Alex à vendre aujourd’hui

1. Montrer un parcours concret au lieu d’une promesse abstraite:
   - Audit IA: qualification et livrables.
   - Onboarding: identité, objectifs, outils, infra, style de l’agent.
   - Devis: formule + modules + prestations, lien reprenable.
   - Provisioning: timeline visible, aucune action automatique.

2. Formulation courte:
   - « On commence par un audit IA guidé. À la fin, tu as un devis clair et un agent_spec exploitable pour installer ton assistant. Rien n’est dépensé sans validation humaine. »

3. Qualification prospect minimale:
   - Métier / secteur.
   - Douleur immédiate: messages, devis/documents, relances, organisation, SAV.
   - Outils actuels: Google, Microsoft, Infomaniak, OVH, Drive/OneDrive, agenda, CRM, facturation.
   - Préférence infra: VPS managé, PC accompagné, hybride, ou « je ne sais pas ».
   - Niveau d’autonomie souhaité.

## Conversion blockers

### HIGH — CTA public protégé OAuth

Constat: `https://app.omar.paris/audit/` redirige vers `/oauth2/start?rd=https://app.omar.paris/audit/`.

Impact: un prospect froid peut cliquer « Démarrer » depuis la landing et ne jamais voir l’audit.

Décision à prendre: soit garder AppOmar privé et créer un pré-audit public côté landing, soit exposer une route `/audit-public/` sans données sensibles, soit documenter explicitement « accès sur invitation ».

### MEDIUM — prix canonique non aligné

Constat: landing tarifs annonce « à partir de 80 €/mois », AppOmar `catalog.json` expose Starter 49 €/mois et Pro 99 €/mois.

Impact: friction commerciale / devis perçu incohérent.

Décision à prendre: choisir la vérité prix unique avant patch Builder.

## Handoff demandé

Agent: oa-commerce

Demande: arbitrer le prix public canonique AppOmar et fournir le wording commercial correspondant:
- option A: landing reste 80 €/mois minimum;
- option B: catalogue AppOmar reste Starter 49 / Pro 99;
- option C: nouvelle grille simple avec setup/onboarding séparé.

Sortie attendue: 1 prix/pack canonique + CTA + 3 objections/réponses, pour que `oa-builder` aligne landing + catalog + devis.

## KPI

```yaml
status: done
kpis:
  cards_completed: 1
  artifacts_verified: 2
  handoffs_created: 1
  blocked_items: 2
done_today:
  - "/home/omar/23-Offre/actifs/omar-app/docs/revenue/revenue_appomar_2026-06-30.md"
  - "/home/omar/23-Offre/actifs/omar-app/docs/revenue/revenue_appomar_2026-06-30.json"
needs_from_other_agents:
  - from: oa-commerce
    ask: "Arbitrer prix public AppOmar et livrer wording CTA + objections avant alignement Builder."
next_action:
  owner: oa-commerce
  action: "Choisir l'offre/prix canonique AppOmar."
```
