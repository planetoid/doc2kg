---
name: ner
version: 1
description: >
  Extract named entities from text and return spans, labels, offsets,
  normalized mentions, entity IDs, and confidence estimates for downstream
  KG ETL tasks.
agents: [knowledge_graph_agent, extraction_agent]
---

# NER Skill

## Purpose

Use this skill when the task requires identifying named entities in text,
including persons, organizations, places, products, dates, quantities, laws,
events, or domain-specific concepts.

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | Raw source text |
| `domain_hint` | string | ☐ | Domain context (e.g., `biomedical`, `legal`, `telecom`) |
| `label_schema` | string[] | ☐ | Custom label set to override defaults |
| `language_hint` | string | ☐ | ISO 639-1 language code (e.g., `zh-TW`, `en`) |

## Output Schema

```json
{
  "language": "zh-TW",
  "entities": [
    {
      "entity_id": "e-001",
      "text": "台北101",
      "label": "LOC",
      "start": 15,
      "end": 20,
      "normalized": "Taipei 101",
      "confidence": 0.96
    }
  ]
}
```

`entity_id` 是必填欄位。下游的 `relation-analysis` 與 `rdf-construction`
透過此 ID 參照特定 mention，避免依賴字串比對造成的歧義。
格式建議：`e-{三位數序號}`，例如 `e-001`、`e-002`。

## Rules

1. Extract exact spans from source text; do not paraphrase or expand.
2. Do not invent entities not present in the text.
3. Keep `text` (source mention) and `normalized` (canonical form) separately.
4. Use domain labels only when supported by the user task.
5. If uncertain, lower `confidence` instead of overcommitting to a label.
6. Prefer a flat entity list unless nested NER is explicitly requested.
7. Assign a unique `entity_id` to every entity in the output.

## Default Labels

| Label | Description |
|-------|-------------|
| `PERSON` | Individual persons |
| `ORG` | Organizations, companies, institutions |
| `GPE` | Geopolitical entities (countries, cities, states) |
| `LOC` | Non-GPE locations (mountains, bodies of water) |
| `DATE` | Absolute or relative dates |
| `TIME` | Times of day |
| `MONEY` | Monetary values |
| `PERCENT` | Percentage expressions |
| `PRODUCT` | Products and services |
| `EVENT` | Named events (conferences, disasters) |
| `LAW` | Laws, regulations, legal documents |
| `WORK_OF_ART` | Titles of books, songs, artworks |
| `EMAIL` | Email addresses |
| `URL` | URLs and URIs |
| `PHONE` | Phone numbers |
| `ID` | Identifier codes (e.g., registration numbers) |

## Dependencies

- `kg-etl/shared/schemas/entity-schema.json`
- `kg-etl/shared/prompts/ner.md`

## Downstream Use

NER output feeds into:
- `coreference-resolution` → resolves pronoun / alias mentions
- `entity-linking` → maps `entity_id` to canonical URIs
- `relation-analysis` → uses `entity_id` as subject/object references
- `ontology-mapping` → maps `label` to ontology classes
- `rdf-construction` → builds triples from entity IDs and normalized forms
