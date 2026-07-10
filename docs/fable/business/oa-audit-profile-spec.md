# Spec profil Hermes `oa-audit` — pour H-Omar

De : Fable 2 (couloir business) — 2026-07-02 — GO Alex donné.
Objet : créer le profil dédié `oa-audit` dans la flotte. En attendant, l'audit
conversationnel tourne sur `oa-commerce` (chaîne de repli automatique).

## Contexte

`app.omar.paris/audit-v2/` est branché sur un agent Hermes via le nouvel endpoint
`POST /api/audit-sessions/{sid}/chat` (`src/proposal_server.py`, marqueur
« Audit conversationnel via agent Hermes »). Mécanisme identique au backend
qgfinance : `hermes chat --profile <p> -q "<prompt>" -Q`, subprocess, timeout 75 s.

Chaîne de profils : variable d'env `OA_AUDIT_PROFILES` (défaut `oa-audit,oa-commerce`).
Dès que `oa-audit` existe, il est utilisé sans redéploiement.

## Ce qui est demandé

1. Créer le profil `oa-audit` sur la stack Codex — recommandation : **gpt-5.5**
   (conversation profonde, pas le mini ; l'audit est notre produit d'appel).
2. System prompt : reprendre `src/oa_audit_prompt.md` (source de vérité, éditable).
   Si le profil porte son propre system prompt, y coller ce fichier ; sinon le
   prompt est déjà injecté à chaque tour par le serveur — un profil « neutre »
   suffit alors (pas de persona commerce qui interfère).
3. Pas d'outils dangereux : le profil n'a besoin d'aucun accès filesystem/shell.
   Lecture web optionnelle (météo, etc.) — à sa discrétion.
4. Vérifier la trace Langfuse (les appels doivent apparaître comme le reste de la flotte).

## Tokens de contrôle attendus dans les réponses

`[STEP_DONE]`, `[CAILLOU: {json}]`, `[CHOICES: a | b | c]`, `[HUMAN_REQUEST]` —
parsés par `parse_audit_agent_reply()` côté serveur, retirés avant affichage client.

## Mesuré en test (2026-07-02, via oa-commerce gpt-5.4-mini)

- Latence : 11-16 s par tour (absorbée par l'indicateur « Omar écrit… » ; à surveiller
  avec gpt-5.5 ; piste d'optimisation : session Hermes persistante au lieu du one-shot).
- Comportement validé : digression météo gérée puis retour au fil ; tutoiement adopté ;
  [CHOICES] et [CAILLOU] émis correctement dès le premier essai ; étapes avancées via
  [STEP_DONE] ; secteur bakery détecté ; scoring caillou cohérent.

## Garde-fous côté serveur (déjà en place, pour info)

- Aucun secret ne peut être écrit en session (SECRET_PATTERNS).
- Fallback automatique : profil suivant de la chaîne, puis mode déterministe côté front.
- 1 appel Hermes par message client, en série (anti-burst respecté).
- Le rapport final passe par le pipeline existant (`/report`, `build_devis_source`).
