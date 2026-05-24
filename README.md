# 知識圖譜 ETL Pipeline + Streamlit 查詢介面

以下為各模組的功能說明與使用套件。

> 本專案使用的第三方套件及其授權條款詳見 [`THIRD_PARTY_LICENSES`](./THIRD_PARTY_LICENSES)。

---

## 🚀 Streamlit 查詢介面

### `app.py`
將原本 `7_sparql_nli_v3.ipynb`（Dash + Cytoscape）改寫為 **Streamlit** 版本，提供：

| 功能 | 說明 |
|------|------|
| 💬 自然語言查詢 | 輸入中文問題，透過 LangChain + Groq (LLaMA 3.3) 自動轉換成 SPARQL |
| ⌨️ SPARQL 直接查詢 | 貼上任意 SPARQL 語句執行，附常用範例 |
| 🕸️ 圖形視覺化 | 互動式知識圖譜（pyvis），支援拖曳 / 縮放 |
| 📊 資料表 | 查詢結果以表格顯示，可下載 CSV |
| ⚙️ 側邊欄設定 | SPARQL Endpoint、Groq API Key、圖形參數 |

**啟動方式：**

```bash
pip install -r requirements.txt
streamlit run app.py
```

**環境變數（可選）：**

```bash
GROQ_API_KEY=gsk_...                       # Groq API 金鑰
SPARQL_ENDPOINT=http://localhost:8890/sparql  # Virtuoso SPARQL endpoint
```

**主要套件：**
- **streamlit**：Web 介面框架
- **pyvis**：互動式圖形視覺化
- **langchain-openai**：LLM Agent（自然語言 → SPARQL）
- **requests / SPARQLWrapper**：SPARQL endpoint 查詢

---

## 🗄️ Virtuoso Triple Store（本機 Docker）

### `my_virtdb.tar.gz`
包含 Virtuoso RDF triple store 的完整備份（Docker Compose + 資料庫檔案 + TTL 原始資料）。

**資料規模：** 82,646 筆三元組，涵蓋 200+ 份歷史檔案主題

**Named Graph：** `http://example.org/graph`

### 首次啟動

```bash
# 1. 解壓縮到 home 目錄
tar -xzf my_virtdb.tar.gz -C ~/

# 2. 啟動 Virtuoso 容器
cd ~/my_virtdb
docker compose up -d

# 3. 確認服務正常（應回傳 JSON）
curl "http://localhost:8890/sparql?query=SELECT+%3Fg+WHERE+%7BGRAPH+%3Fg+%7B%3Fs+%3Fp+%3Fo%7D%7D+LIMIT+5"
```

**連線資訊：**
| 項目 | 值 |
|------|----|
| SPARQL Endpoint | `http://localhost:8890/sparql` |
| 管理介面 | `http://localhost:8890/conductor` |
| DBA 密碼 | `admin` |
| ISQL Port | `1111` |

### 重新啟動（每次開機後）

```bash
cd ~/my_virtdb && docker compose up -d
```

### 故障排除

**問題：Transaction log 版本衝突（版本升級後）**
```bash
docker stop virtuoso
rm ~/my_virtdb/database/virtuoso.trx
rm ~/my_virtdb/database/virtuoso.lck
docker compose up -d
```

**問題：容器啟動後查無資料**  
確認查詢使用的 Graph URI 是否正確：
```sparql
SELECT DISTINCT ?g (COUNT(*) AS ?cnt)
WHERE { GRAPH ?g { ?s ?p ?o } }
GROUP BY ?g ORDER BY DESC(?cnt)
```

---

## 📥 資料收集與清洗模組

### `1_html2json_v2.ipynb`
程式功能主要處理 HTML 類型文本成為 JSON 格式，使用以下套件程式：
- **BeautifulSoup（bs4）**：負責解析 HTML 結構，提供節點搜尋與屬性操作等功能。
- **re**：使用正則表達式清理不必要的空白與特殊符號。
- **json**：將轉換後的資料儲存為標準 JSON 格式。
- **os**：處理路徑與檔案讀取操作。

### `1_pdf2json_v2.ipynb`
程式功能主要處理 PDF 類型文本成為 JSON 格式，使用以下套件程式：
- **pdfplumber**：從 PDF 抽取文字內容、位置與版面資訊，適合處理結構化或表格型 PDF。
- **re**：同上。
- **json**：同上。
- **os**：同上。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/8AjIgCkaq3g/0.jpg)](https://www.youtube.com/watch?v=8AjIgCkaq3g)

### `2_get_metadata_v4.ipynb`
程式功能主要處理文本中的 metadata 詮釋資料成為 JSON 格式，使用以下套件程式：
- **json**：處理 JSON 檔案的讀取與解析。
- **pandas**：將處理後的資料轉為 DataFrame，並可儲存為 CSV。
- **os**：處理檔案與目錄操作。
- **re**：透過正則表達式處理與格式化欄位內容。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/FvUpK4WQx9o/0.jpg)](https://www.youtube.com/watch?v=FvUpK4WQx9o)

---

## 🧠 文本語意分析模組

### `3_cot_NER_llama_v3.ipynb`
程式功能是使用大語言模型處理文本的 NER/RE 任務，使用以下套件程式：
- **langchain_openai**：支援 OpenAI 模型（如 llama-3.3-70b-versatile）。
- **langchain**：用於建立 PromptTemplate 與 LLMChain。
- 提供命名實體辨識（NER）與關係識別功能。
- **re**：清理 JSON 輸出中的 Markdown 標記。
- **json**：處理 JSON 資料解析與序列化。
- **os**：處理環境變數與檔案操作。
- **shutil**：檔案搬移用途。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/l0cxE4vyG6M/0.jpg)](https://www.youtube.com/watch?v=l0cxE4vyG6M)

### `3_resolution_NER_llama_v8.ipynb`
程式功能是使用大語言模型處理文本的 GCR 任務，使用以下套件程式：
- 同上，並額外提供 **廣義指稱解決（GCR）** 功能。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/i5Mibz3iuCE/0.jpg)](https://www.youtube.com/watch?v=i5Mibz3iuCE)

---

## ✅ 審閱與修訂模組

### `4_human_review.ipynb`
程式功能是會將 NER/RE/GCR 結果產生審查報表，使用以下套件程式：
- **os**：列出資料夾中的檔案與組合路徑。
- **json**：讀取 JSON 檔案並處理字典轉換。
- **csv**：將資料寫入 CSV。
- **shutil**：移動已處理檔案至 done/ 資料夾。
- **pandas**：處理與分析 CSV 結構化資料。
- **tabulate**：格式化並輸出表格數據至終端機。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/xmQt_hyY8gw/0.jpg)](https://www.youtube.com/watch?v=xmQt_hyY8gw)

---

## 🔗 實體連結模組

### `5_wiki1_v5.ipynb`
程式功能主要是將文本中的實體與外部 KG（Wikidata / DBpedia）進行對齊，補充額外的外部資訊至 JSON 檔案中，使用以下套件程式：
- **wikipedia / requests**：查詢實體描述與可能對應條目。
- **sparqlwrapper**：執行 SPARQL 查詢並與 RDF 平台互動。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/ti5nHp6jvhM/0.jpg)](https://www.youtube.com/watch?v=ti5nHp6jvhM)

---

## 📄 知識圖譜管理模組

### `6_RDF_meta_event.ipynb`
程式功能主要是收集完整文本處理 JSON 資訊轉換成為 RDF 格式，使用以下套件程式：
- **os**：處理檔案與目錄操作。
- **json**：解析 JSON 格式資料。
- **requests**：從 Wikidata 或 DBpedia 擷取資料。
- **rdflib**：
  - `Graph`, `URIRef`, `Literal`, `RDF`, `Namespace`, `BNode`
  - 命名空間：`XSD`, `RDFS`, `OWL`

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/XeaQlD2x_d0/0.jpg)](https://www.youtube.com/watch?v=XeaQlD2x_d0)

---

## 💬 KG 應用程式

### `7_SPARQL_QA_JSON_v1.ipynb`

### `7_sparql_nli_v3.ipynb`
程式功能主要是會以自然語言轉換成 SPARQL 語言與 triple store 溝通，返回對應的資料內容，並且提供視覺化界面（Cytoscape），用來檢視檔案的 SPO 資料結構，使用以下套件程式：
- **dash，dash_cytoscape，requests，threading，webbrowser**
- [![影片標題](https://img.youtube.com/vi/zcjdOQdmt0Y/0.jpg)](https://www.youtube.com/watch?v=zcjdOQdmt0Y)

> **注意：** 此 notebook 版本（Dash + Cytoscape）已改寫為 `app.py`（Streamlit 版本），請優先使用 `app.py`。
