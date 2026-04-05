---
name: rdf-serialization
version: 1
description: >
  Serialize RDF graphs into Turtle, N-Triples, RDF/XML, or JSON-LD for
  downstream storage and interoperability.
agents: [knowledge_graph_agent]
---

# RDF Serialization Skill

## Purpose

Convert in-memory RDF triples into one or more serialization formats for
storage, inspection, or system integration.

## Supported Formats

| Format | Extension | Best for |
|--------|-----------|----------|
| Turtle | `.ttl` | Human inspection, debugging, knowledge engineering |
| N-Triples | `.nt` | Bulk loading pipelines (Virtuoso, GraphDB, Fuseki) |
| JSON-LD | `.jsonld` | Web integration and JSON-based systems |
| RDF/XML | `.rdf` | Legacy system compatibility |

## Guidance

- Prefer **Turtle** for human inspection and debugging.
- Prefer **JSON-LD** for web integration and JSON-based systems.
  JSON-LD is a W3C standard for expressing Linked Data in JSON form.
- Prefer **N-Triples** for bulk loading pipelines.
- Always include a `@context` block (JSON-LD) or `PREFIX` declarations (Turtle).

## Turtle Template

```turtle
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <https://schema.org/> .
@prefix :       <https://example.org/entity/> .

:NationalTaiwanUniversity
    rdf:type schema:Organization ;
    rdfs:label "國立臺灣大學"@zh-TW ;
    rdfs:label "National Taiwan University"@en ;
    schema:location :Taipei .
```

## JSON-LD Template

```json
{
  "@context": {
    "schema": "https://schema.org/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
  },
  "@id": "https://example.org/entity/NationalTaiwanUniversity",
  "@type": "schema:Organization",
  "rdfs:label": [
    { "@value": "國立臺灣大學", "@language": "zh-TW" },
    { "@value": "National Taiwan University", "@language": "en" }
  ],
  "schema:location": { "@id": "https://example.org/entity/Taipei" }
}
```

## Dependencies

- `kg-etl/shared/schemas/jsonld-context.json`
