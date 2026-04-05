---
name: ontology-mapping
version: 1
description: >
  Map extracted entity labels and relation predicates to ontology classes and
  properties for RDF-compliant graph construction.
agents: [knowledge_graph_agent]
---

# Ontology Mapping Skill

## Purpose

Use this skill to translate NER labels and relation-analysis predicates into
stable ontology vocabulary, for example:
- `ORG` → `schema:Organization` or `foaf:Organization`
- `locatedIn` → `schema:location`
- `worksFor` → `org:memberOf`

## Input

> Both inputs are required. Do not run ontology-mapping on NER output alone
> before `relation-analysis` has completed.

| Source | Fields used |
|--------|-------------|
| `ner` output | `label` per entity |
| `relation-analysis` output | `predicate` per relation |

## Output Schema

```json
{
  "entity_mappings": [
    {
      "ner_label": "ORG",
      "ontology_class": "schema:Organization",
      "prefix": "schema",
      "uri": "https://schema.org/Organization"
    }
  ],
  "relation_mappings": [
    {
      "predicate": "locatedIn",
      "ontology_property": "schema:location",
      "prefix": "schema",
      "uri": "https://schema.org/location"
    }
  ]
}
```

## Default Namespace Prefixes

```turtle
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:    <http://www.w3.org/2002/07/owl#> .
@prefix schema: <https://schema.org/> .
@prefix foaf:   <http://xmlns.com/foaf/0.1/> .
@prefix org:    <http://www.w3.org/ns/org#> .
@prefix prov:   <http://www.w3.org/ns/prov#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .
```

## Rules

1. Use well-known vocabularies (schema.org, foaf, org) before defining custom properties.
2. If no standard property fits, define a project-local property in the project namespace.
3. Record the full URI alongside the prefixed form for clarity.
4. All mappings must be stored in `kg-etl/shared/schemas/rdf-mapping.json` for reuse.

## Dependencies

- `kg-etl/shared/schemas/rdf-mapping.json`
