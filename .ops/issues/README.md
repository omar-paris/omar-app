# Omar App issues

Statut : local durable tant que `omar-app` n'a pas de repo GitHub officiel.

## Règle

- Les issues produit/build peuvent être créées ici : `.ops/issues/NNN-slug.md`.
- Quand un repo GitHub officiel existe, migrer ces fichiers en GitHub Issues.
- Ne jamais stocker de secrets dans une issue.
- Les noms de variables secrets peuvent être cités (`OPENROUTER_API_KEY`), mais jamais leurs valeurs.

## Format minimal

```markdown
# Issue NNN — Titre

**Statut** : open | in_progress | done | archived
**Type** : product | build | bug | ops | security
**Priorité** : P0 | P1 | P2 | P3
**Source** :

## Contexte

## Décision / besoin

## Critères d'acceptation

## Preuves attendues
```

## Issue existante

- `001-packaging-couts-reels-options-payantes-oa.md`
