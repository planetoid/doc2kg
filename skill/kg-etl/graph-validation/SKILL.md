---
name: graph-validation
version: 1
description: >
  Validate RDF graph shape, URI consistency, and required properties.
  Supports quick-check mode (post-construction) and full shape validation
  mode (post-serialization).
agents: [knowledge_graph_agent]
---

# Graph Validation Skill

## Purpose

Ensure RDF graph quality before ingestion into a triple store or knowledge
base. Validation runs in two distinct modes at different pipeline stages.

## Two Validation Modes

### Mode 1 — Quick Check

**When to run:** After `rdf-construction`, before `rdf-serialization`.

Checks:
- URI format compliance (no blank nodes where IRIs are expected)
- Required `rdf:type` triple present for all entities
- No duplicate triple conflicts
- All `entity_id` references in relation output resolve to a known entity

### Mode 2 — Full Shape Validation

**When to run:** After `rdf-serialization`.

Checks:
- SHACL or ShEx shape conformance
- Datatype correctness on literals (e.g., dates as `xsd:date`)
- Cardinality constraints (e.g., exactly one `rdfs:label` per language)
- Cross-reference integrity

## Output

```
validation-report.md
```

Format:

```markdown
# Graph Validation Report

## Mode: Quick Check | Full Shape Validation
## Timestamp: 2024-01-15T10:00:00Z
## Triple count: 142

### Passed
- URI format compliance ✅
- rdf:type coverage ✅

### Warnings
- 3 entities missing English rdfs:label

### Errors
- e-042: object URI <https://example.org/entity/> is incomplete
```

## Rules

1. Always run Mode 1 before serialization.
2. Always run Mode 2 after serialization, before ingestion.
3. Errors block pipeline progression; warnings are logged but non-blocking.
4. Report must reference `entity_id` for traceability back to source text.
