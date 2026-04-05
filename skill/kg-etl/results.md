
 ✓  ReadFile Vocabulary_list.csv                                                                                                                          │
│                                                                                                                                                          │
│ Read lines 1-2000 of 3940 from Vocabulary_list.csv                                                                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
✦ 這是一份包含約 3,940 筆詞彙的 CSV 檔案。我將根據 kg-etl 流程中的 ner 技能，從這份檔案中抽取出具代表性的實體（如人名、地名、語言、組織等），並將其轉換成符合
  entity-schema.json 的 JSON 格式。

  由於資料量較大，我先針對前 100 筆資料進行 NER 處理作為示範。
  
  
'''
           
    1 {
    2   "language": "zh-TW",
    3   "entities": [
    4     {
    5       "entity_id": "e-001",
    6       "text": "陳月美",
    7       "label": "PERSON",
    8       "start": 57,
    9       "end": 60,
   10       "normalized": "Chen Yuemei",
   11       "confidence": 0.98
   12     },
   13     {
   14       "entity_id": "e-002",
   15       "text": "李明華",
   16       "label": "PERSON",
   17       "start": 102,
   18       "end": 105,
   19       "normalized": "Li Minghua",
   20       "confidence": 0.98
   21     },
   22     {
   23       "entity_id": "e-003",
   24       "text": "王開文",
   25       "label": "PERSON",
   26       "start": 144,
   27       "end": 147,
   28       "normalized": "Wang Kaiwen",
   29       "confidence": 0.98
   30     },
   31     {
   32       "entity_id": "e-004",
   33       "text": "臺灣",
   34       "label": "GPE",
   35       "start": 625,
   36       "end": 627,
   37       "normalized": "Taiwan",
   38       "confidence": 0.99
   39     },
   40     {
   41       "entity_id": "e-005",
   42       "text": "日本",
   43       "label": "GPE",
   44       "start": 1284,
   45       "end": 1286,
   46       "normalized": "Japan",
   47       "confidence": 0.99
   48     },
   49     {
   50       "entity_id": "e-006",
   51       "text": "美國",
   52       "label": "GPE",
   53       "start": 1313,
   54       "end": 1315,
   55       "normalized": "USA",
   56       "confidence": 0.99
   57     },
   58     {
   59       "entity_id": "e-007",
   60       "text": "張怡君",
   61       "label": "PERSON",
   62       "start": 1395,
   63       "end": 1398,
   64       "normalized": "Zhang Yijun",
   65       "confidence": 0.98
   66     },
   67     {
   68       "entity_id": "e-008",
   69       "text": "馬安同",
   70       "label": "PERSON",
   71       "start": 1443,
   72       "end": 1446,
   73       "normalized": "Ma Antong",
   74       "confidence": 0.98
   75     },
   76     {
   77       "entity_id": "e-009",
   78       "text": "田中誠一",
   79       "label": "PERSON",
   80       "start": 2132,
   81       "end": 2136,
   82       "normalized": "Tanaka Seiichi",
   83       "confidence": 0.98
   84     },
   85     {
   86       "entity_id": "e-010",
   87       "text": "越南",
   88       "label": "GPE",
   89       "start": 3615,
   90       "end": 3617,
   91       "normalized": "Vietnam",
   92       "confidence": 0.99
   93     }
   94   ]
   95 }


'''
                         
  
                                           