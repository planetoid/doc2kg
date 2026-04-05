---
name: provenance
version: 1
description: >
  Attach provenance metadata to RDF graphs, recording source documents,
  extraction methods, timestamps, and confidence scores.
agents: [knowledge_graph_agent]
---

# Provenance Skill

## Purpose

Ensure every triple can be traced back to its source text, extraction method,
and timestamp. Particularly important for research, government, and enterprise
knowledge graph deployments.

Uses PROV-O (W3C Provenance Ontology) as the vocabulary base.

## Input

- Triple set from `rdf-construction`
- Evidence snippets from `relation-analysis`
- Confidence scores from `ner` and `relation-analysis`

## Output Schema (PROV-O aligned)

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

## Turtle Representation

```turtle
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix ex:   <https://example.org/> .

ex:triple-001 a prov:Entity ;
    prov:wasDerivedFrom ex:doc-2024-report ;
    prov:wasGeneratedBy ex:extraction-run-001 ;
    prov:generatedAtTime "2024-01-15T09:30:00Z"^^xsd:dateTime .

ex:extraction-run-001 a prov:Activity ;
    prov:used ex:relation-analysis-v1 .
```

## Rules

1. Every triple in the final graph must have at least one provenance record.
2. `source_span` must be a verbatim excerpt from the source document.
3. `extraction_method` must include version (e.g., `ner@v1`).
4. Store provenance as a named graph or as reified triples, not inline.
