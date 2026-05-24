# 系統模組與套件說明


## 📥 資料收集與清洗模組

### `1_html2json_v2.ipynb`
程式功能主要處理html類型文本成為JSON格式，使用以下套件程式:
- **BeautifulSoup（bs4）**：負責解析 HTML 結構，提供節點搜尋與屬性操作等功能。
- **re**：使用正則表達式清理不必要的空白與特殊符號。
- **json**：將轉換後的資料儲存為標準 JSON 格式。
- **os**：處理路徑與檔案讀取操作。

### `1_pdf2json_v2.ipynb`
程式功能主要處理pdf類型文本成為JSON格式，使用以下套件程式:
- **pdfplumber**：從 PDF 抽取文字內容、位置與版面資訊，適合處理結構化或表格型 PDF。
- **re**：同上。
- **json**：同上。
- **os**：同上。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/8AjIgCkaq3g/0.jpg)](https://www.youtube.com/watch?v=8AjIgCkaq3g)

### `2_get_metadata_v4.ipynb`
程式功能主要處理文本中的metadat詮釋資料成為JSON格式，使用以下套件程式:
- **json**：處理 JSON 檔案的讀取與解析。
- **pandas**：將處理後的資料轉為 DataFrame，並可儲存為 CSV。
- **os**：處理檔案與目錄操作。
- **re**：透過正則表達式處理與格式化欄位內容。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/FvUpK4WQx9o/0.jpg)](https://www.youtube.com/watch?v=FvUpK4WQx9o)

---

## 🧠 文本語意分析模組

### `3_cot_NER_llama_v3.ipynb`
程式功能是使用大語言模型處理文本的NER/RE任務，使用以下套件程式:
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
程式功能是使用大語言模型處理文本的GCR任務，使用以下套件程式:
- 同上，並額外提供 **廣義指稱解決（GCR）** 功能。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/i5Mibz3iuCE/0.jpg)](https://www.youtube.com/watch?v=i5Mibz3iuCE)

---

## ✅ 審閱與修訂模組

### `4_human_review.ipynb`
程式功能是會將NER/RE/GCR結果產生審查報表，使用以下套件程式:
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
程式功能主要是將文本中的實體與外部KG(wikidata/dbpidia)進行對其，補充額外的外部資訊至JSON檔案中，使用以下套件程式:
- **wikipedia / requests**：查詢實體描述與可能對應條目。
- **sparqlwrapper**：執行 SPARQL 查詢並與 RDF 平台互動。

- 上述程式執行影片
- [![影片標題](https://img.youtube.com/vi/ti5nHp6jvhM/0.jpg)](https://www.youtube.com/watch?v=ti5nHp6jvhM)

---

## 📄 知識圖譜管理模組

### `6_RDF_meta_event.ipynb`
程式功能主要是收集完整文本處理JSON資訊轉換成為RDF格式，使用以下套件程式:
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

### `my_virtdb.tar.gz`
使用docker-compose 建置triple store ，包含RDF (.ttl) 檔案。

### `7_SPARQL_QA_JSON_v1.ipynb`

### `7_sparql_nli_v3.ipynb`
程式功能主要是會以自然語言轉換成Sparql語言與triple store 溝通，返回對應的資料內容，並且提供視覺化界面(cytoscap)，用來檢視檔案的SPO資料結構，使用以下套件程式:
- **dash，dash_cytoscape，requests，threading，webbrowser**
- [![影片標題](https://img.youtube.com/vi/zcjdOQdmt0Y/0.jpg)](https://www.youtube.com/watch?v=zcjdOQdmt0Y)
