# kg-etl Skill Suite

---

## 父 Skill：kg-etl

```yaml
name: kg-etl
version: 1
description: >
  Transform unstructured or semi-structured content into knowledge-graph-ready
  structured data and RDF artifacts through entity extraction, relation analysis,
  ontology mapping, and serialization.
agents: [main_agent, extraction_agent, knowledge_graph_agent]
```

### Purpose

Use this skill when the user wants to:
- 將文本、文件、網頁、表格轉成知識圖譜資料。
- 從非結構化資料抽取實體、關係與事件。
- 轉換成 RDF / Turtle / JSON-LD。
- 建立可匯入圖資料庫或三元組庫的資料。

### Subskills

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

### Workflow

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
   - Run **quick-check mode** of `graph-validation` here (URI format, required triples).
9. Run **full shape validation** (SHACL / ShEx) using `graph-validation`.
10. Attach provenance metadata using `provenance`.

### Outputs

| File | Description |
|------|-------------|
| `entities.json` | Extracted entities with IDs and normalized forms |
| `relations.json` | Extracted relations referencing entity IDs |
| `triples.ttl` | RDF graph in Turtle format |
| `graph.jsonld` | RDF graph in JSON-LD format |
| `validation-report.md` | Shape and consistency validation report |

### Shared Resources

All subskills MAY reference shared artifacts under `kg-etl/shared/`:

```
kg-etl/shared/
├── schemas/
│   ├── entity-schema.json       # Entity output schema
│   ├── relation-schema.json     # Relation output schema
│   ├── rdf-mapping.json         # Ontology mapping rules
│   └── jsonld-context.json      # JSON-LD @context
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

---

## 子 Skill：ner

```yaml
name: ner
version: 1
description: >
  Extract named entities from text and return spans, labels, offsets,
  normalized mentions, entity IDs, and confidence estimates for downstream
  KG ETL tasks.
agents: [knowledge_graph_agent, extraction_agent]
```

### Purpose

Use this skill when the task requires identifying named entities in text,
including persons, organizations, places, products, dates, quantities, laws,
events, or domain-specific concepts.

### Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | Raw source text |
| `domain_hint` | string | ☐ | Domain context (e.g., `biomedical`, `legal`, `telecom`) |
| `label_schema` | string[] | ☐ | Custom label set to override defaults |
| `language_hint` | string | ☐ | ISO 639-1 language code (e.g., `zh-TW`, `en`) |

### Output Schema

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

> **`entity_id`** は必須欄位。下游的 `relation-analysis` 與 `rdf-construction`
> 透過此 ID 參照特定 mention，避免依賴字串比對造成的歧義。
> 格式建議：`e-{三位數序號}`，例如 `e-001`、`e-002`。

### Rules

1. Extract exact spans from source text; do not paraphrase or expand.
2. Do not invent entities not present in the text.
3. Keep `text` (source mention) and `normalized` (canonical form) separately.
4. Use domain labels only when supported by the user task.
5. If uncertain, lower `confidence` instead of overcommitting to a label.
6. Prefer a flat entity list unless nested NER is explicitly requested.
7. Assign a unique `entity_id` to every entity in the output.

### Default Labels

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

### Dependencies

- `kg-etl/shared/schemas/entity-schema.json`
- `kg-etl/shared/prompts/ner.md`

### Downstream Use

NER output feeds into:
- `coreference-resolution` → resolves pronoun / alias mentions
- `entity-linking` → maps `entity_id` to canonical URIs
- `relation-analysis` → uses `entity_id` as subject/object references
- `ontology-mapping` → maps `label` to ontology classes
- `rdf-construction` → builds triples from entity IDs and normalized forms

---

## 子 Skill：relation-analysis

```yaml
name: relation-analysis
version: 1
description: >
  Identify semantic relations, roles, and event links between extracted entities
  for downstream triple construction.
agents: [knowledge_graph_agent, extraction_agent]
```

### Purpose

Use this skill to detect binary relations between entities, such as:

`worksFor` · `locatedIn` · `partOf` · `foundedBy` · `publishedOn` ·
`regulates` · `cites` · `collaboratesWith` · `usesMethod` · `belongsToProject`

### Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | Source text |
| `entities` | Entity[] | ✅ | Output from `ner` (including `entity_id`) |

### Output Schema

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

> **`subject_id` / `object_id`** 必須對應到 `ner` 輸出的 `entity_id`，
> 不可僅使用字串。如 subject 或 object 在 NER 中未出現，
> 應補發新的 `entity_id` 並附帶說明。

### Rules

1. Only emit relations supported by textual evidence.
2. Populate `subject_id` and `object_id` by referencing `entity_id` from NER output.
3. Keep `evidence` snippets for traceability and provenance.
4. Use canonical predicate names; do not use raw natural language strings as predicates.
5. Separate factual relations from speculative or hypothetical statements.

### Dependencies

- `kg-etl/shared/schemas/relation-schema.json`
- `kg-etl/shared/prompts/relation-extraction.md`

---

## 子 Skill：entity-linking

```yaml
name: entity-linking
version: 1
description: >
  Disambiguate entity mentions and align them to canonical URIs or knowledge
  base identifiers for consistent graph identity.
agents: [knowledge_graph_agent]
```

### Purpose

Use this skill to resolve ambiguity and assign stable identity to entities, for example:
- `台大` / `國立臺灣大學` / `NTU` → single canonical URI
- `Apple` → company or fruit, resolved by context

### Input

- Entity list from `ner` (including `entity_id` and `normalized` fields)
- Optional: target knowledge base (Wikidata, DBpedia, domain ontology)

### Output Schema

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

### Rules

1. Prefer an established knowledge base URI over a minted local URI when possible.
2. If no KB match exists, mint a local URI following the project's URI pattern.
3. Record `confidence`; do not silently drop uncertain links.
4. Multiple mentions that resolve to the same entity must share the same `canonical_uri`.

### Dependencies

- `kg-etl/shared/prompts/entity-linking.md`

---

## 子 Skill：ontology-mapping

```yaml
name: ontology-mapping
version: 1
description: >
  Map extracted entity labels and relation predicates to ontology classes and
  properties for RDF-compliant graph construction.
agents: [knowledge_graph_agent]
```

### Purpose

Use this skill to translate NER labels and relation-analysis predicates into
stable ontology vocabulary, for example:
- `ORG` → `foaf:Organization` or `schema:Organization`
- `locatedIn` → `schema:location` or a project-local property

### Input

| Source | Fields used |
|--------|-------------|
| `ner` output | `label` per entity |
| `relation-analysis` output | `predicate` per relation |

> Both inputs are required. Do not run ontology-mapping on NER output alone
> before relation-analysis has completed.

### Output Schema

```json
{
  "entity_mappings": [
    { "ner_label": "ORG", "ontology_class": "schema:Organization", "prefix": "schema" }
  ],
  "relation_mappings": [
    { "predicate": "locatedIn", "ontology_property": "schema:location", "prefix": "schema" }
  ]
}
```

### Dependencies

- `kg-etl/shared/schemas/rdf-mapping.json`

---

## 子 Skill：rdf-construction

```yaml
name: rdf-construction
version: 1
description: >
  Build RDF triples from linked entities, relations, and ontology mappings.
agents: [knowledge_graph_agent]
```

### Purpose

Convert intermediate IE results into subject-predicate-object triples, for example:

```
:NationalTaiwanUniversity rdf:type schema:Organization .
:NationalTaiwanUniversity schema:location :Taipei .
```

### Input

- Linked entity list from `entity-linking` (canonical URIs)
- Relation list from `relation-analysis` (with `subject_id`, `object_id`)
- Ontology mappings from `ontology-mapping`

### Rules

1. Use `canonical_uri` from `entity-linking` as the subject/object IRI.
2. Use `ontology_property` from `ontology-mapping` as the predicate.
3. Add `rdf:type` triple for every entity using its mapped `ontology_class`.
4. Attach literal values (dates, strings) with correct datatype annotations.

### Dependencies

- `kg-etl/shared/prompts/rdf-construction.md`
- `kg-etl/shared/schemas/rdf-mapping.json`

---

## 子 Skill：rdf-serialization

```yaml
name: rdf-serialization
version: 1
description: >
  Serialize RDF graphs into Turtle, N-Triples, RDF/XML, or JSON-LD for
  downstream storage and interoperability.
agents: [knowledge_graph_agent]
```

### Supported Formats

| Format | Best for |
|--------|----------|
| Turtle (`.ttl`) | Human inspection, debugging, knowledge engineering |
| N-Triples (`.nt`) | Bulk loading pipelines (Virtuoso, GraphDB) |
| JSON-LD (`.jsonld`) | Web integration and JSON-based systems |
| RDF/XML (`.rdf`) | Legacy system compatibility |

### Guidance

- Prefer **Turtle** for human inspection and debugging.
- Prefer **JSON-LD** for web integration and JSON-based systems.
  JSON-LD is a W3C standard for expressing Linked Data in JSON form.
- Prefer **N-Triples** for bulk loading pipelines.
- Always include a `@context` or `PREFIX` block for namespace clarity.

### Dependencies

- `kg-etl/shared/schemas/jsonld-context.json`

---

## 子 Skill：graph-validation

```yaml
name: graph-validation
version: 1
description: >
  Validate RDF graph shape, URI consistency, and required properties.
  Supports quick-check mode (post-construction) and full shape validation
  mode (post-serialization).
agents: [knowledge_graph_agent]
```

### Two Validation Modes

#### Mode 1 — Quick Check (run after `rdf-construction`, before serialization)

Check for:
- URI format compliance (no blank nodes where IRIs are expected)
- Required `rdf:type` triples present for all entities
- No duplicate triple conflicts

#### Mode 2 — Full Shape Validation (run after `rdf-serialization`)

Check for:
- SHACL or ShEx shape conformance
- Datatype correctness on literals
- Cardinality constraints
- Cross-reference integrity (all `entity_id` references resolve)

### Output

```
validation-report.md
```

---

## 子 Skill：provenance

```yaml
name: provenance
version: 1
description: >
  Attach provenance metadata to RDF graphs, recording source documents,
  extraction methods, timestamps, and confidence scores.
agents: [knowledge_graph_agent]
```

### Purpose

Ensure every triple can be traced back to its source text, extraction method,
and timestamp. Particularly important for research, government, and enterprise
knowledge graph deployments.

### Output Schema (PROV-O aligned)

```json
{
  "provenance": [
    {
      "triple_subject": "https://example.org/entity/NationalTaiwanUniversity",
      "triple_predicate": "schema:location",
      "triple_object": "https://example.org/entity/Taipei",
      "source_document": "doc-2024-report.pdf",
      "source_span": "國立臺灣大學位於台北市",
      "extraction_method": "relation-analysis@v1",
      "timestamp": "2024-01-15T09:30:00Z",
      "confidence": 0.92
    }
  ]
}
```

---

## 建議目錄結構

```
kg-etl/
├── SKILL.md                          ← 父 skill（orchestration）
├── ner/SKILL.md
├── coreference-resolution/SKILL.md
├── entity-linking/SKILL.md
├── relation-analysis/SKILL.md
├── ontology-mapping/SKILL.md
├── rdf-construction/SKILL.md
├── rdf-serialization/SKILL.md
├── graph-validation/SKILL.md
├── provenance/SKILL.md
└── shared/
    ├── schemas/
    │   ├── entity-schema.json        ← 含 entity_id 欄位定義
    │   ├── relation-schema.json      ← subject_id / object_id 欄位
    │   ├── rdf-mapping.json          ← NER label → ontology class 對照表
    │   └── jsonld-context.json       ← 可直接掛進 JSON-LD 的 @context
    ├── prompts/
    │   ├── ner.md
    │   ├── relation-extraction.md
    │   ├── entity-linking.md
    │   └── rdf-construction.md
    └── examples/
        ├── input-text.md             ← 台大 NTU 範例文本
        ├── entities.json             ← 對應的 NER 輸出
        ├── triples.ttl               ← Turtle 格式 RDF
        └── graph.jsonld              ← JSON-LD 格式 RDF
```

---

## 完整 Pipeline 順序

```
1. ner                    → 抽出實體，產生 entity_id
2. coreference-resolution → 把代詞、別名對回主實體
3. entity-linking         → 做 canonical URI identity
4. relation-analysis      → 接 entity_id，抽出關係
5. ontology-mapping       → 接 NER labels + relation predicates，映射 class/property
6. rdf-construction       → 建 triples
7. provenance             → 附來源與證據
8. rdf-serialization      → 輸出 .ttl / .jsonld
9. graph-validation       → quick-check（序列化前） + full shape（序列化後）
```

---

