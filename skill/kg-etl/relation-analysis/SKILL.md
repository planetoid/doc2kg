---
name: relation-analysis
version: 1
description: >
  Identify semantic relations, roles, and event links between extracted entities
  for downstream triple construction.
agents: [knowledge_graph_agent, extraction_agent]
---

# Relation Analysis Skill

## Purpose

Use this skill to detect binary relations between entities, such as:

`worksFor` · `locatedIn` · `partOf` · `foundedBy` · `publishedOn` ·
`regulates` · `cites` · `collaboratesWith` · `usesMethod` · `belongsToProject`

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | Source text |
| `entities` | Entity[] | ✅ | Output from `ner` + `entity-linking` (must include `entity_id`) |

## Output Schema

```json
{
  "relations": [
    {
      "subject_id": "e-001",
      "subject_text": "國立臺灣大學",
      "predicate": "locatedIn",
      "object_id": "e-007",
      "object_text": "台北市",
      "evidence": "國立臺灣大學位於台北市",
      "confidence": 0.92
    }
  ]
}
```

`subject_id` / `object_id` 必須對應到 `ner` 輸出的 `entity_id`，
不可僅使用字串。如 subject 或 object 在 NER 中未出現，
應補發新的 `entity_id` 並附帶說明。

## Rules

1. Only emit relations supported by textual evidence.
2. Populate `subject_id` and `object_id` by referencing `entity_id` from NER output.
3. Keep `evidence` snippets for traceability and provenance.
4. Use canonical predicate names; do not use raw natural language strings as predicates.
5. Separate factual relations from speculative or hypothetical statements.

## Default Predicates

| Predicate | Description |
|-----------|-------------|
| `worksFor` | Person works for organization |
| `locatedIn` | Entity located in place |
| `partOf` | Entity is part of another |
| `foundedBy` | Organization founded by person |
| `publishedOn` | Work published on date |
| `regulates` | Entity regulates another |
| `cites` | Document cites another |
| `collaboratesWith` | Entity collaborates with another |
| `usesMethod` | Research uses a method |
| `belongsToProject` | Entity belongs to project |

## Dependencies

- `kg-etl/shared/schemas/relation-schema.json`
- `kg-etl/shared/prompts/relation-extraction.md`
