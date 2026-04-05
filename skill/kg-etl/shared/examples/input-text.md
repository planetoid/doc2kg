# Example Input Text

## Source

以下是用於示範整個 kg-etl pipeline 的範例文本。

---

國立臺灣大學（NTU）位於台北市大安區，由日本殖民政府於1928年創立。
現任校長陳文章自2021年起領導該校，致力於推動與國際頂尖大學的學術合作。
台大資訊工程學系與麻省理工學院（MIT）在人工智慧領域共同發表了多篇研究論文，
其中一篇於2023年11月刊登於《Nature》期刊，研究經費來自科技部補助計畫MOST-112-AI-001。

---

## Expected Entities (after NER)

| entity_id | text | label |
|-----------|------|-------|
| e-001 | 國立臺灣大學 | ORG |
| e-002 | NTU | ORG |
| e-003 | 台北市大安區 | GPE |
| e-004 | 日本殖民政府 | ORG |
| e-005 | 1928年 | DATE |
| e-006 | 陳文章 | PERSON |
| e-007 | 2021年 | DATE |
| e-008 | 台大資訊工程學系 | ORG |
| e-009 | 麻省理工學院 | ORG |
| e-010 | MIT | ORG |
| e-011 | 2023年11月 | DATE |
| e-012 | 《Nature》 | WORK_OF_ART |
| e-013 | 科技部 | ORG |
| e-014 | MOST-112-AI-001 | ID |

## Expected Coreference Clusters

- e-001 ← e-002 (NTU), 該校
- e-009 ← e-010 (MIT)
