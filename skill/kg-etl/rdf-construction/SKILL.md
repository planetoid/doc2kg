---
name: rdf-construction
version: 1
description: >
  Build RDF triples from linked entities, relations, and ontology mappings.
agents: [knowledge_graph_agent]
---

# RDF Construction Skill

## Purpose

Convert intermediate IE results into subject-predicate-object triples.
This is the core transformation step from extracted text data to graph data.

Example output:

```turtle
:NationalTaiwanUniversity rdf:type schema:Organization .
:NationalTaiwanUniversity schema:location :Taipei .
:NationalTaiwanUniversity rdfs:label "國立臺灣大學"@zh-TW .
:NationalTaiwanUniversity rdfs:label "National Taiwan University"@en .
```

## Input

| Source | Fields used |
|--------|-------------|
| `entity-linking` | `canonical_uri`, `label` per entity |
| `relation-analysis` | `subject_id`, `predicate`, `object_id`, `evidence` |
| `ontology-mapping` | `ontology_class`, `ontology_property` per label/predicate |

## Rules

1. Use `canonical_uri` from `entity-linking` as the subject/object IRI.
2. Use `ontology_property` from `ontology-mapping` as the predicate.
3. Add `rdf:type` triple for every entity using its mapped `ontology_class`.
4. Add `rdfs:label` literals in source language and normalized form.
5. Attach literal values (dates, strings) with correct XSD datatype annotations.
6. Do not construct triples without ontology mapping; resolve mapping gaps first.

## Output

Intermediate triple set (in-memory or as `.ttl` draft) passed to `rdf-serialization`.

## Dependencies

- `kg-etl/shared/prompts/rdf-construction.md`
- `kg-etl/shared/schemas/rdf-mapping.json`
