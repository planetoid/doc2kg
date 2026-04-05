---
name: kg-etl
version: 1
description: >
  Transform unstructured or semi-structured content into knowledge-graph-ready
  structured data and RDF artifacts through entity extraction, relation analysis,
  ontology mapping, and serialization.
agents: [main_agent, extraction_agent, knowledge_graph_agent]
---

# KG-ETL Skill

## Purpose

Use this skill when the user wants to:
- 將文本、文件、網頁、表格轉成知識圖譜資料。
- 從非結構化資料抽取實體、關係與事件。
- 轉換成 RDF / Turtle / JSON-LD。
- 建立可匯入圖資料庫或三元組庫的資料。

## Subskills

This skill may route work to:
- `ner`
- `coreference-resolution`
- `entity-linking`
- `relation-analysis`
- `ontology-mapping`
- `rdf-construction`
- `rdf-serialization`
- `graph-validation`
- `provenance`

## Workflow

1. Inspect input type and domain.
2. Extract entities from text using `ner`.
3. Resolve pronouns and aliases to canonical mentions using `coreference-resolution`.
   *(Must run before `entity-linking` so that all mention variants are captured.)*
4. Normalize mentions and map them to canonical resources using `entity-linking`.
5. Detect relations and events using `relation-analysis`.
   *(Receives both the source text and the entity list from `ner` + `entity-linking`.)*
6. Map entities and relations to ontology classes and properties using `ontology-mapping`.
   *(Input: combined output of `ner` labels + `relation-analysis` predicate labels.)*
7. Build RDF triples using `rdf-construction`.
8. Serialize graph as Turtle, N-Triples, or JSON-LD using `rdf-serialization`.
   Run **quick-check mode** of `graph-validation` at this point (URI format, required triples).
9. Run **full shape validation** (SHACL / ShEx) using `graph-validation`.
10. Attach provenance metadata using `provenance`.

## Outputs

| File | Description |
|------|-------------|
| `entities.json` | Extracted entities with IDs and normalized forms |
| `relations.json` | Extracted relations referencing entity IDs |
| `triples.ttl` | RDF graph in Turtle format |
| `graph.jsonld` | RDF graph in JSON-LD format |
| `validation-report.md` | Shape and consistency validation report |

## Shared Resources

All subskills MAY reference shared artifacts under `kg-etl/shared/`:

```
kg-etl/shared/
├── schemas/
│   ├── entity-schema.json
│   ├── relation-schema.json
│   ├── rdf-mapping.json
│   └── jsonld-context.json
├── prompts/
│   ├── ner.md
│   ├── relation-extraction.md
│   ├── entity-linking.md
│   └── rdf-construction.md
└── examples/
    ├── input-text.md
    ├── entities.json
    ├── triples.ttl
    └── graph.jsonld
```

Each subskill's `SKILL.md` lists which shared files it depends on under `## Dependencies`.

## Pipeline Order

```
1. ner                    → 抽出實體，產生 entity_id
2. coreference-resolution → 把代詞、別名對回主實體
3. entity-linking         → 做 canonical URI identity
4. relation-analysis      → 接 entity_id，抽出關係
5. ontology-mapping       → 接 NER labels + relation predicates，映射 class/property
6. rdf-construction       → 建 triples
7. provenance             → 附來源與證據
8. rdf-serialization      → 輸出 .ttl / .jsonld
9. graph-validation       → quick-check（序列化前）+ full shape（序列化後）
```
