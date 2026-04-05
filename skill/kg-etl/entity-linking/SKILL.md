---
name: entity-linking
version: 1
description: >
  Disambiguate entity mentions and align them to canonical URIs or knowledge
  base identifiers for consistent graph identity.
agents: [knowledge_graph_agent]
---

# Entity Linking Skill

## Purpose

Use this skill to resolve ambiguity and assign stable identity to entities,
for example:
- `台大` / `國立臺灣大學` / `NTU` → single canonical URI
- `Apple` → company (`Q312`) or fruit, resolved by context

Runs after `coreference-resolution` to ensure all mention variants are
available before URI assignment.

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entities` | Entity[] | ✅ | From `ner`, enriched by `coreference-resolution` |
| `kb_target` | string | ☐ | Target knowledge base: `wikidata`, `dbpedia`, or domain URI |

## Output Schema

```json
{
  "linked_entities": [
    {
      "entity_id": "e-001",
      "canonical_uri": "https://www.wikidata.org/entity/Q641861",
      "label": "National Taiwan University",
      "kb_source": "wikidata",
      "confidence": 0.97
    }
  ]
}
```

## Rules

1. Prefer an established knowledge base URI over a minted local URI when possible.
2. If no KB match exists, mint a local URI following the project's URI pattern.
3. Record `confidence`; do not silently drop uncertain links.
4. Multiple mentions resolving to the same entity must share one `canonical_uri`.
5. Pass `canonical_uri` downstream to `rdf-construction` as the triple subject/object.

## Dependencies

- `kg-etl/shared/prompts/entity-linking.md`
