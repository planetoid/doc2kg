---
name: coreference-resolution
version: 1
description: >
  Resolve pronouns, aliases, and abbreviated mentions to their canonical
  entity, enriching NER output before entity-linking.
agents: [knowledge_graph_agent, extraction_agent]
---

# Coreference Resolution Skill

## Purpose

Use this skill to connect all mentions of the same real-world entity within a
document, for example:
- `他` / `該執行長` / `黃仁勳` → same person
- `本研究團隊` / `台大資工所團隊` → same organization
- `該公司` / `OpenAI` → same organization

Must run **after** `ner` and **before** `entity-linking` so that all mention
variants are captured before canonical URI assignment.

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | Source text |
| `entities` | Entity[] | ✅ | Output from `ner` (with `entity_id`) |

## Output Schema

```json
{
  "coreference_clusters": [
    {
      "canonical_entity_id": "e-001",
      "canonical_text": "國立臺灣大學",
      "mentions": [
        { "text": "台大", "start": 42, "end": 44 },
        { "text": "該校", "start": 87, "end": 89 },
        { "text": "NTU",  "start": 103, "end": 106 }
      ]
    }
  ]
}
```

## Rules

1. Use `canonical_entity_id` from `ner` output as the cluster anchor.
2. Only cluster mentions with strong textual or contextual evidence.
3. Do not merge entities from different discourse segments without evidence.
4. Pass updated entity list (with merged mentions) to `entity-linking`.

## Dependencies

- `kg-etl/shared/schemas/entity-schema.json`
