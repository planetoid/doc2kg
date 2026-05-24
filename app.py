"""
SPARQL 知識圖譜查詢與視覺化 — Streamlit 版本
原始版本：7_sparql_nli_v3.ipynb (Dash + Cytoscape)
改寫為：Streamlit + pyvis
"""

import os
import re
import json
import tempfile
import requests
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
from pyvis.network import Network

# ── 可選：pdfplumber（PDF 解析）
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# ── 可選：LangChain（若 API key 存在才載入）
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import initialize_agent, AgentType, Tool
    from langchain_core.messages import SystemMessage
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# ═══════════════════════════════════════════════════════
# 頁面設定
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="KG 知識圖譜查詢",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════
# 工具函式（定義在 UI 之前）
# ═══════════════════════════════════════════════════════

# ── PDF 文字清洗
def pdf_word_filter(text: str) -> str:
    """清理 PDF 擷取文字中的雜訊。"""
    text = text.replace("\r", "").strip()
    text = re.sub(r'^\d+/\d+/\d+|\d+/\d+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^檔案樂活情報|回頁首|-|LOHAS|Archives\d+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s{3,}', '\n', text)
    return text.strip()


# ── NER Prompt（與 3_cot_NER_llama_v3.ipynb 相同）
_NER_TEMPLATE = """
這是一個命名實體識別（NER）任務，你需要將文本中的實體分類為以下類別：
### **命名實體分類方式：**
- 人物（Person）：包括個人姓名、稱號、官職、別名等。
- 時間（Date/Time）：歷史年代、具體年份、月份、日期、時刻等。
- 地點（Location）：城市、國家、地區、建築物等。
- 組織（Organization）：政府機構、學術機構、軍事組織、社會團體、企業等。
- 事件（Event）：戰爭、革命、條約、政策變遷、災難、運動等。
- 專有名詞（Proper Noun）：包含特定歷史文件、法律條文、計畫名稱等。
- 數量（Quantity）：具體數字、統計數據、人口數、傷亡數等。
- 貨幣（Money）：歷史貨幣單位及金額。
- 比例（Percentage/Ratio）：百分比、比率、分數等。

直接輸出 **JSON** 格式，請勿包含其他文字或 Markdown 標記（例如 ```json）。

### **輸出格式範例：**
{{
    "人物": ["愛因斯坦"],
    "時間": ["20世紀", "1933年10月"],
    "地點": ["美國", "普林斯頓"],
    "組織": ["普林斯頓高等研究院"],
    "事件": ["創立相對論與量子力學"],
    "專有名詞": ["相對論", "量子力學", "現代物理學之父"],
    "數量": [],
    "貨幣": [],
    "比例": []
}}
### **範例到此結束。**

將以下文本提取成命名實體：
{text}
"""

# ── 關係識別 Prompt（與 3_cot_NER_llama_v3.ipynb 相同）
_RE_TEMPLATE = """
請分析以下實體，推理它們之間的關係，使用逐步推理（Chain-of-Thought, CoT）方式。
基於 Wikidata 常見屬性（P31 instance of、P50 作者、P108 任職、P585 時間點、P361 part of 等）建立關係結構。

輸出標準 JSON 格式，不包含其他文字。格式如下：
[
  {{
    "主體": "實體名稱|類別",
    "關係": "關係描述|Wikidata屬性",
    "客體": "實體名稱|類別"
  }},
  ...
]

輸入實體：
{entities}
"""


def clean_json_output(raw: str) -> str:
    """移除 LLM 輸出中的 Markdown 標記。"""
    cleaned = re.sub(r"```json\s*([\s\S]*?)\s*```", r"\1", raw).strip()
    cleaned = re.sub(r"```\s*([\s\S]*?)\s*```", r"\1", cleaned).strip()
    return cleaned


@st.cache_resource(show_spinner=False)
def get_llm(api_key: str, model: str):
    """建立 LLM 實例（以參數快取）。"""
    if not LANGCHAIN_AVAILABLE:
        return None
    return ChatOpenAI(
        openai_api_base="https://api.groq.com/openai/v1",
        openai_api_key=api_key,
        model_name=model,
        temperature=0.0,
    )


def simplify_uri(uri: str) -> str:
    """將 URI 縮短成可讀標籤。"""
    if not uri or not uri.startswith("http"):
        return uri
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


def run_sparql(query: str, endpoint: str):
    """執行 SPARQL 查詢，回傳 JSON 結果或錯誤字串。"""
    headers = {"Accept": "application/sparql-results+json"}
    try:
        resp = requests.get(endpoint, params={"query": query}, headers=headers, timeout=15)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "html" in content_type:
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.find_all("tr")[1:]
            out = []
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    out.append({
                        "s": {"value": cols[0].get_text(strip=True), "type": "uri"},
                        "p": {"value": cols[1].get_text(strip=True), "type": "uri"},
                        "o": {"value": cols[2].get_text(strip=True), "type": "literal"},
                    })
            return {"results": {"bindings": out}}
        return resp.json()
    except Exception as e:
        return f"❌ 查詢失敗：{e}"


def bindings_to_dataframe(bindings: list) -> pd.DataFrame:
    """將 SPARQL bindings 轉為 DataFrame。"""
    rows = []
    for b in bindings:
        if isinstance(b, dict) and any(isinstance(v, dict) for v in b.values()):
            row = {k: v.get("value", "") for k, v in b.items()}
        else:
            row = b
        rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def build_graph_html(bindings: list, height: int, max_n: int, physics: bool):
    """用 pyvis 建立互動式知識圖譜，回傳 (html_str, node_count, edge_count)。

    配色設計原則（WCAG AA，對比度 ≥ 4.5:1）：
      主體節點（S）  ── 深藍  #1D4ED8，白字，對比度 8.6:1
      客體節點（O）  ── 深紫  #6D28D9，白字，對比度 7.2:1
      文字值（Lit）  ── 深琥珀 #B45309，白字，對比度 5.1:1
      邊              ── 中灰  #4B5563，白底可見
      邊標籤          ── 深灰  #1F2937
    藍 / 紫 / 琥珀三色在常見色盲類型（紅色盲、綠色盲）下仍可區分。
    """
    # ── 語義色票
    C_BG        = "#FFFFFF"   # 白底，最高對比基準
    C_SUBJECT   = "#1D4ED8"   # 藍-700  Subject URI
    C_OBJECT    = "#6D28D9"   # 紫-700  Object URI
    C_LITERAL   = "#B45309"   # 琥珀-700 Literal 文字值
    C_EDGE      = "#4B5563"   # 灰-600  邊
    C_FONT_DARK = "#1F2937"   # 灰-800  邊標籤、網路預設字色
    C_FONT_W    = "#FFFFFF"   # 白      節點標籤

    net = Network(
        height=f"{height}px",
        width="100%",
        directed=True,
        bgcolor=C_BG,
        font_color=C_FONT_DARK,
    )
    if physics:
        net.force_atlas_2based(
            gravity=-50, central_gravity=0.01,
            spring_length=120, spring_strength=0.08,
            damping=0.4, overlap=0,
        )
    else:
        net.toggle_physics(False)

    node_ids: set = set()
    edge_count = 0

    for b in bindings:
        if len(node_ids) >= max_n:
            break

        if isinstance(b, dict) and any(isinstance(v, dict) for v in b.values()):
            s_raw = b.get("s", {}).get("value", "")
            p_raw = b.get("p", {}).get("value", "")
            o_raw = b.get("o", {}).get("value", "")
            o_type = b.get("o", {}).get("type", "uri")
        else:
            s_raw = str(b.get("s", ""))
            p_raw = str(b.get("p", ""))
            o_raw = str(b.get("o", ""))
            o_type = "literal" if not o_raw.startswith("http") else "uri"

        if not s_raw or not p_raw or not o_raw:
            continue

        s_label = simplify_uri(s_raw)
        p_label = simplify_uri(p_raw)
        o_label = simplify_uri(o_raw) if o_type == "uri" else o_raw[:60]

        if s_raw not in node_ids:
            net.add_node(s_raw, label=s_label, title=s_raw,
                         color={"background": C_SUBJECT, "border": "#1E3A8A",
                                "highlight": {"background": "#2563EB", "border": "#1E3A8A"}},
                         shape="ellipse",
                         font={"size": 13, "color": C_FONT_W, "bold": True})
            node_ids.add(s_raw)

        if o_raw not in node_ids and len(node_ids) < max_n:
            if o_type == "literal":
                fill, border, hi = C_LITERAL, "#78350F", "#D97706"
            else:
                fill, border, hi = C_OBJECT, "#4C1D95", "#7C3AED"
            shape = "box" if o_type == "literal" else "ellipse"
            net.add_node(o_raw, label=o_label, title=o_raw,
                         color={"background": fill, "border": border,
                                "highlight": {"background": hi, "border": border}},
                         shape=shape,
                         font={"size": 13, "color": C_FONT_W})
            node_ids.add(o_raw)

        if s_raw in node_ids and o_raw in node_ids:
            net.add_edge(s_raw, o_raw, label=p_label,
                         title=p_raw,
                         color={"color": C_EDGE, "highlight": "#111827"},
                         font={"size": 11, "color": C_FONT_DARK,
                               "background": "#F9FAFB", "strokeWidth": 0})
            edge_count += 1

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w",
                                     encoding="utf-8") as f:
        net.save_graph(f.name)
        tmp_path = f.name

    with open(tmp_path, "r", encoding="utf-8") as f:
        html_str = f.read()

    os.unlink(tmp_path)
    return html_str, len(node_ids), edge_count


def show_results(bindings: list, height: int, max_n: int, physics: bool):
    """顯示 DataFrame 表格 + 圖形視覺化（內嵌 tabs）。"""
    df = bindings_to_dataframe(bindings)
    total = len(bindings)

    rtab1, rtab2 = st.tabs([f"📊 資料表（{total} 筆）", "🕸️ 圖形視覺化"])

    with rtab1:
        display_df = df.copy()
        for col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda v: simplify_uri(str(v)) if str(v).startswith("http") else v
            )
        st.dataframe(display_df, use_container_width=True, height=400)
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 下載 CSV", data=csv_bytes,
                           file_name="sparql_results.csv", mime="text/csv")

    with rtab2:
        cols = list(df.columns)
        if not all(c in cols for c in ["s", "p", "o"]):
            st.info(
                "ℹ️ 圖形視覺化需要查詢結果包含 `?s ?p ?o` 三個變數。\n\n"
                "請使用 `SELECT ?s ?p ?o WHERE { ?s ?p ?o ... }` 格式的 SPARQL。"
            )
        else:
            with st.spinner("建立圖形中…"):
                html_str, node_cnt, edge_cnt = build_graph_html(
                    bindings, height, max_n, physics
                )
            st.caption(f"🔵 主體節點（深藍）　🟣 客體節點 URI（深紫）　🟠 文字值（琥珀）  |  "
                       f"節點：{node_cnt}　邊：{edge_cnt}　（最多 {max_n} 節點）")
            components.html(html_str, height=height + 30, scrolling=False)


@st.cache_resource(show_spinner=False)
def get_agent(api_key: str, model: str, endpoint: str):
    """建立 LangChain agent（以參數快取）。"""
    if not LANGCHAIN_AVAILABLE:
        return None, "❌ 需要安裝 langchain_openai：`pip install langchain-openai`"
    if not api_key or not api_key.startswith("gsk_"):
        return None, "⚠️ 請在側邊欄填入有效的 Groq API Key（gsk_ 開頭）。"

    _ep = endpoint  # closure 捕捉

    def _query_kg(sparql_query: str) -> str:
        result = run_sparql(sparql_query, _ep)
        if isinstance(result, str):
            return result
        bindings = result.get("results", {}).get("bindings", [])
        if not bindings:
            return "查無資料，請確認查詢條件。"
        st.session_state["_last_sparql_query"] = sparql_query
        st.session_state["_last_bindings"] = bindings
        rows = []
        for b in bindings[:25]:
            if isinstance(b, dict) and any(isinstance(v, dict) for v in b.values()):
                row = {k: v.get("value", "") for k, v in b.items()}
            else:
                row = b
            rows.append(str(row))
        return "\n".join(rows)

    tools = [
        Tool(
            name="query_kg_tool",
            func=_query_kg,
            description=(
                "查詢本地 Virtuoso SPARQL endpoint，並回傳查詢結果摘要。"
                "輸入為標準 SPARQL 1.1 語句（不支援 Wikibase 特有語法）。"
            ),
        )
    ]

    llm = ChatOpenAI(
        openai_api_base="https://api.groq.com/openai/v1",
        openai_api_key=api_key,
        model_name=model,
        temperature=0.0,
    )

    system_msg = (
        "你是一個智慧型知識查詢助理，所有問題都必須透過 query_kg_tool 工具查詢 RDF 知識圖譜。\n"
        "將自然語言問題轉換成正確的 SPARQL 查詢後，使用 query_kg_tool 查詢。\n"
        "注意：\n"
        "- SPARQL endpoint 是本地 Virtuoso，不支援 Wikidata SERVICE wikibase:label 語法。\n"
        "- 使用標準 SPARQL 1.1。\n"
        "- 查詢以 Dublin Core (dc:) 等標準 prefix 標注，圖 URI: <http://example.org/graph>。\n"
        "- 中文名稱使用 rdfs:label 加 FILTER(lang(?label) = \"zh\")。\n"
        "- 以繁體中文摘要回答查詢結果重點。"
    )

    agent = initialize_agent(
        tools, llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,
        handle_parsing_errors=True,
        agent_kwargs={"system_message": SystemMessage(content=system_msg)},
    )
    return agent, None


# ═══════════════════════════════════════════════════════
# 側邊欄設定
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ 設定")
    st.divider()

    sparql_endpoint = st.text_input(
        "SPARQL Endpoint",
        value=st.session_state.get(
            "sparql_endpoint",
            os.environ.get("SPARQL_ENDPOINT", "http://localhost:8890/sparql"),
        ),
        placeholder="http://host:8890/sparql",
        help="Virtuoso SPARQL endpoint URL",
    )
    st.session_state["sparql_endpoint"] = sparql_endpoint

    st.divider()
    st.subheader("🤖 LLM 設定（NL 查詢用）")

    groq_api_key = st.text_input(
        "Groq API Key",
        value=st.session_state.get(
            "groq_api_key",
            os.environ.get("GROQ_API_KEY", ""),
        ),
        type="password",
        placeholder="gsk_...",
    )
    st.session_state["groq_api_key"] = groq_api_key

    model_name = st.selectbox(
        "LLM 模型",
        options=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "deepseek-r1-distill-llama-70b",
        ],
        index=0,
    )

    st.divider()
    st.subheader("🎨 圖形視覺化設定")
    graph_height = st.slider("圖形高度 (px)", 400, 900, 600, 50)
    max_nodes = st.slider("最多顯示節點數", 20, 300, 100, 10)
    physics_enabled = st.checkbox("啟用物理模擬", value=True)

    st.divider()
    st.caption("📂 資料來源：本地 Virtuoso RDF Store")

# ═══════════════════════════════════════════════════════
# 主介面
# ═══════════════════════════════════════════════════════
st.title("🕸️ SPARQL 知識圖譜查詢與視覺化")
st.caption("檔案管理局歷史檔案知識圖譜 · Virtuoso RDF Store")

tab_nl, tab_sparql, tab_pdf, tab_ner, tab_about = st.tabs(
    ["💬 自然語言查詢", "⌨️ SPARQL 直接查詢", "📄 PDF 解析", "🔍 文字 NER", "ℹ️ 關於"]
)

# ───────────────────────────────────────────────────────
# Tab 1：自然語言查詢
# ───────────────────────────────────────────────────────
with tab_nl:
    st.subheader("💬 自然語言查詢")
    st.caption("輸入問題，系統自動轉換為 SPARQL 並查詢知識圖譜。")

    nl_examples = [
        "查詢與228事件相關的文件",
        "有關電影的歷史檔案有哪些？",
        "有關萬華的資料",
        "列出海洋相關的文件",
        "金馬獎相關的歷史紀錄",
    ]

    col_q, col_ex = st.columns([3, 1])
    with col_q:
        nl_question = st.text_input(
            "輸入問題",
            placeholder="例如：查詢與228事件相關的文件",
            label_visibility="collapsed",
        )
    with col_ex:
        example_choice = st.selectbox(
            "範例", ["（選擇範例）"] + nl_examples,
            label_visibility="collapsed",
        )
        if example_choice != "（選擇範例）":
            nl_question = example_choice

    nl_submit = st.button("🔍 查詢", key="nl_submit",
                          use_container_width=True, type="primary")

    if nl_submit and nl_question:
        if not LANGCHAIN_AVAILABLE:
            st.error("❌ 需要安裝 langchain-openai：`pip install langchain-openai`")
        else:
            agent, err = get_agent(
                st.session_state.get("groq_api_key", ""),
                model_name,
                sparql_endpoint,
            )
            if err:
                st.error(err)
            else:
                with st.spinner("LLM 轉換查詢語句中，請稍候…"):
                    try:
                        answer = agent.run(nl_question)
                        st.session_state["nl_answer"] = answer
                    except Exception as e:
                        st.error(f"Agent 執行錯誤：{e}")

    if "nl_answer" in st.session_state:
        st.divider()
        st.markdown("### 🤖 回覆")
        st.info(st.session_state["nl_answer"])

        last_q = st.session_state.get("_last_sparql_query", "")
        if last_q:
            with st.expander("📋 LLM 產生的 SPARQL", expanded=False):
                st.code(last_q, language="sparql")

        bindings = st.session_state.get("_last_bindings", [])
        if bindings:
            st.divider()
            show_results(bindings, graph_height, max_nodes, physics_enabled)

# ───────────────────────────────────────────────────────
# Tab 2：SPARQL 直接查詢
# ───────────────────────────────────────────────────────
with tab_sparql:
    st.subheader("⌨️ 直接輸入 SPARQL 查詢")

    default_sparql = (
        "PREFIX dc: <http://purl.org/dc/elements/1.1/>\n"
        "SELECT DISTINCT ?title ?date ?creator\n"
        "WHERE {\n"
        "  GRAPH <http://example.org/graph> {\n"
        "    ?doc dc:title ?title .\n"
        "    OPTIONAL { ?doc dc:date ?date . }\n"
        "    OPTIONAL { ?doc dc:creator ?creator . }\n"
        "    FILTER (regex(str(?title), '電影', 'i'))\n"
        "  }\n"
        "}\n"
        "ORDER BY ?date\n"
        "LIMIT 30"
    )

    sparql_input = st.text_area(
        "SPARQL 查詢",
        value=st.session_state.get("sparql_draft", default_sparql),
        height=220,
        label_visibility="collapsed",
    )
    st.session_state["sparql_draft"] = sparql_input

    with st.expander("📋 常用查詢範例"):
        examples = {
            "列出所有 Named Graphs":
                "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 20",

            "電影相關文件（Dublin Core）": (
                "PREFIX dc: <http://purl.org/dc/elements/1.1/>\n"
                "SELECT DISTINCT ?title ?date ?creator\n"
                "WHERE {\n"
                "  ?doc dc:title ?title .\n"
                "  OPTIONAL { ?doc dc:date ?date . }\n"
                "  OPTIONAL { ?doc dc:creator ?creator . }\n"
                "  FILTER (regex(str(?title), '電影', 'i'))\n"
                "} LIMIT 20"
            ),

            "SPO 三元組（適合畫圖）": (
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
                "SELECT ?s ?p ?o\n"
                "WHERE { ?s ?p ?o . FILTER (regex(str(?s), '228事件')) }\n"
                "LIMIT 50"
            ),

            "統計各 creator 文件數": (
                "PREFIX dc: <http://purl.org/dc/elements/1.1/>\n"
                "SELECT ?creator (COUNT(?doc) AS ?count)\n"
                "WHERE { ?doc dc:creator ?creator . }\n"
                "GROUP BY ?creator\n"
                "ORDER BY DESC(?count)\n"
                "LIMIT 20"
            ),

            "228 相關所有屬性": (
                "PREFIX dc: <http://purl.org/dc/elements/1.1/>\n"
                "SELECT ?s ?p ?o\n"
                "WHERE {\n"
                "  ?s ?p ?o .\n"
                "  FILTER (regex(str(?s), '228') || regex(str(?o), '228', 'i'))\n"
                "} LIMIT 80"
            ),
        }
        for label, q in examples.items():
            if st.button(f"📌 {label}", key=f"ex_{label}"):
                st.session_state["sparql_draft"] = q
                st.rerun()

    sparql_submit = st.button(
        "▶️ 執行查詢", key="sparql_submit",
        use_container_width=True, type="primary"
    )

    if sparql_submit and sparql_input.strip():
        with st.spinner("查詢中…"):
            result = run_sparql(sparql_input, sparql_endpoint)

        if isinstance(result, str):
            st.error(result)
        else:
            bindings = result.get("results", {}).get("bindings", [])
            if not bindings:
                st.warning("⚠️ 查無資料，請確認查詢條件或資料庫內容。")
            else:
                st.session_state["sparql_bindings"] = bindings

    if "sparql_bindings" in st.session_state:
        st.divider()
        show_results(
            st.session_state["sparql_bindings"],
            graph_height, max_nodes, physics_enabled,
        )

# ───────────────────────────────────────────────────────
# Tab 3：PDF 解析
# ───────────────────────────────────────────────────────
with tab_pdf:
    st.subheader("📄 PDF 上傳解析")
    st.caption("上傳 PDF 檔案，自動擷取文字內容，可直接送往 NER 分析。")

    if not PDFPLUMBER_AVAILABLE:
        st.error("❌ 需要安裝 pdfplumber：`pip install pdfplumber`")
    else:
        uploaded_pdf = st.file_uploader(
            "選擇 PDF 檔案", type=["pdf"], key="pdf_uploader"
        )

        if uploaded_pdf:
            with st.spinner("解析 PDF 中…"):
                try:
                    pages_data = []
                    with pdfplumber.open(uploaded_pdf) as pdf:
                        total_pages = len(pdf.pages)
                        for i, page in enumerate(pdf.pages):
                            raw = page.extract_text() or ""
                            cleaned = pdf_word_filter(raw)
                            if cleaned:
                                pages_data.append({"page": i + 1, "text": cleaned})

                    full_text = "\n\n".join(p["text"] for p in pages_data)
                    st.session_state["pdf_full_text"] = full_text
                    st.session_state["pdf_pages"] = pages_data

                except Exception as e:
                    st.error(f"❌ 解析失敗：{e}")
                    pages_data = []
                    full_text = ""

            if pages_data:
                st.success(
                    f"✅ 解析完成｜共 {total_pages} 頁，"
                    f"擷取 {sum(len(p['text']) for p in pages_data):,} 字元"
                )

                # 頁面瀏覽
                with st.expander(f"📄 查看擷取文字（{len(pages_data)} 頁）", expanded=True):
                    page_sel = st.selectbox(
                        "選擇頁面",
                        options=[f"第 {p['page']} 頁" for p in pages_data],
                        key="pdf_page_sel",
                    )
                    sel_idx = int(page_sel.replace("第 ", "").replace(" 頁", "")) - 1
                    # Find matching page
                    sel_page = next(
                        (p for p in pages_data if p["page"] == sel_idx + 1), pages_data[0]
                    )
                    st.text_area(
                        "文字內容",
                        value=sel_page["text"],
                        height=300,
                        key="pdf_page_preview",
                        label_visibility="collapsed",
                    )

                # 全文預覽與下載
                col_dl1, col_dl2, col_send = st.columns([1, 1, 2])
                with col_dl1:
                    st.download_button(
                        "⬇️ 下載全文 .txt",
                        data=full_text.encode("utf-8"),
                        file_name=f"{uploaded_pdf.name.replace('.pdf','')}.txt",
                        mime="text/plain",
                    )
                with col_dl2:
                    import json as _json
                    pages_json = _json.dumps(pages_data, ensure_ascii=False, indent=2)
                    st.download_button(
                        "⬇️ 下載 JSON",
                        data=pages_json.encode("utf-8"),
                        file_name=f"{uploaded_pdf.name.replace('.pdf','')}.json",
                        mime="application/json",
                    )
                with col_send:
                    if st.button(
                        "▶️ 送往 NER 分析",
                        use_container_width=True,
                        type="primary",
                        key="pdf_to_ner",
                    ):
                        st.session_state["ner_prefill"] = full_text[:4000]  # LLM token 限制
                        st.success("✅ 已送往「🔍 文字 NER」頁籤，請切換頁籤執行分析。")


# ───────────────────────────────────────────────────────
# Tab 4：文字 NER
# ───────────────────────────────────────────────────────
with tab_ner:
    st.subheader("🔍 命名實體辨識（NER）+ 關係識別")
    st.caption("貼入歷史文字，透過 Groq LLaMA 進行 NER 與關係識別（RE）。")

    # 若有從 PDF tab 傳入文字，自動填入
    ner_default = st.session_state.pop("ner_prefill", "")
    if not ner_default:
        ner_default = st.session_state.get("ner_text_draft", "")

    ner_input = st.text_area(
        "輸入文字",
        value=ner_default,
        height=220,
        placeholder="例如：光復之初，民眾表現出對國民政府熱烈的歡迎與支持…",
        key="ner_input",
        label_visibility="collapsed",
    )
    st.session_state["ner_text_draft"] = ner_input

    col_ner1, col_ner2 = st.columns(2)
    with col_ner1:
        btn_ner_only = st.button(
            "🔍 僅執行 NER", use_container_width=True, type="primary", key="btn_ner"
        )
    with col_ner2:
        btn_ner_re = st.button(
            "🔗 NER + 關係識別", use_container_width=True, key="btn_ner_re"
        )

    if (btn_ner_only or btn_ner_re) and ner_input.strip():
        if not LANGCHAIN_AVAILABLE:
            st.error("❌ 需要安裝 langchain-openai：`pip install langchain-openai`")
        else:
            api_key = st.session_state.get("groq_api_key", "")
            if not api_key or not api_key.startswith("gsk_"):
                st.error("⚠️ 請在側邊欄填入有效的 Groq API Key（gsk_ 開頭）。")
            else:
                llm = get_llm(api_key, model_name)

                # ── NER
                ner_prompt_obj = PromptTemplate(
                    input_variables=["text"], template=_NER_TEMPLATE
                )
                ner_chain = LLMChain(prompt=ner_prompt_obj, llm=llm)

                with st.spinner("NER 分析中（Groq LLaMA）…"):
                    try:
                        ner_raw = ner_chain.invoke({"text": ner_input})
                        ner_text_out = ner_raw.get("text", "") if isinstance(ner_raw, dict) else str(ner_raw)
                        ner_cleaned = clean_json_output(ner_text_out)
                        try:
                            ner_result = json.loads(ner_cleaned)
                        except json.JSONDecodeError:
                            ner_result = {"raw": ner_text_out}
                        st.session_state["ner_result"] = ner_result
                    except Exception as e:
                        st.error(f"NER 執行錯誤：{e}")
                        ner_result = None

                # ── RE（可選）
                if btn_ner_re and ner_result:
                    re_prompt_obj = PromptTemplate(
                        input_variables=["entities"], template=_RE_TEMPLATE
                    )
                    re_chain = LLMChain(prompt=re_prompt_obj, llm=llm)

                    with st.spinner("關係識別中…"):
                        try:
                            re_raw = re_chain.invoke(
                                {"entities": json.dumps(ner_result, ensure_ascii=False)}
                            )
                            re_text_out = re_raw.get("text", "") if isinstance(re_raw, dict) else str(re_raw)
                            re_cleaned = clean_json_output(re_text_out)
                            try:
                                re_result = json.loads(re_cleaned)
                            except json.JSONDecodeError:
                                re_result = [{"raw": re_text_out}]
                            st.session_state["re_result"] = re_result
                        except Exception as e:
                            st.error(f"關係識別執行錯誤：{e}")

    # ── 顯示結果
    if "ner_result" in st.session_state:
        st.divider()
        ner_res = st.session_state["ner_result"]

        rtab_ner, rtab_table, rtab_re = st.tabs(
            ["📋 NER JSON", "📊 實體表格", "🔗 關係識別"]
        )

        with rtab_ner:
            st.json(ner_res)
            st.download_button(
                "⬇️ 下載 NER JSON",
                data=json.dumps(ner_res, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="ner_result.json",
                mime="application/json",
            )

        with rtab_table:
            # 展平成表格：類別 | 實體
            rows = []
            if isinstance(ner_res, dict):
                for category, entities in ner_res.items():
                    if isinstance(entities, list):
                        for ent in entities:
                            rows.append({"類別": category, "實體": str(ent)})
            if rows:
                ner_df = pd.DataFrame(rows)
                st.dataframe(ner_df, use_container_width=True, height=350)
                st.download_button(
                    "⬇️ 下載 CSV",
                    data=ner_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="ner_result.csv",
                    mime="text/csv",
                )
            else:
                st.info("無法解析為表格，請查看 JSON 頁籤。")

        with rtab_re:
            if "re_result" in st.session_state:
                re_res = st.session_state["re_result"]
                if isinstance(re_res, list) and re_res and isinstance(re_res[0], dict) and "主體" in re_res[0]:
                    re_df = pd.DataFrame(re_res)
                    st.dataframe(re_df, use_container_width=True, height=350)
                    st.download_button(
                        "⬇️ 下載關係 CSV",
                        data=re_df.to_csv(index=False).encode("utf-8-sig"),
                        file_name="re_result.csv",
                        mime="text/csv",
                    )
                else:
                    st.json(re_res)
            else:
                st.info("ℹ️ 請點擊「🔗 NER + 關係識別」按鈕以執行關係識別。")


# ───────────────────────────────────────────────────────
# Tab 5：關於
# ───────────────────────────────────────────────────────
with tab_about:
    st.markdown("""
## 🕸️ 關於本系統

本系統為 **html-to-kg-json** 知識圖譜 ETL Pipeline 的 Streamlit 前端，
提供對本地 Virtuoso RDF 三元組資料庫的互動式查詢與視覺化介面。

### 📦 系統架構

```
HTML / PDF 原始文件
    ↓  1_html2json / 1_pdf2json  ←─────────────────────┐
JSON 結構化資料                                          │
    ↓  2_get_metadata                         📄 PDF 解析 Tab（上傳 PDF）
詮釋資料（Dublin Core）                                  │
    ↓  3_cot_NER / 3_resolution_NER（LLaMA） ←──────────┤
NER / RE / GCR 結果                           🔍 文字 NER Tab（貼文字）
    ↓  4_human_review
人工審查（CSV → JSON）
    ↓  5_wiki1
實體連結（Wikidata / DBpedia）
    ↓  6_RDF_meta_event
RDF 序列化（.ttl / .jsonld）
    ↓  匯入 Virtuoso Docker
🕸️  本系統：SPARQL NLI 查詢介面
```

### 🔧 技術棧

| 元件 | 說明 |
|------|------|
| **Virtuoso** | 本地 RDF 三元組資料庫（Docker） |
| **LangChain + Groq** | 自然語言 → SPARQL 轉換 |
| **LLaMA 3.3 70B** | Groq 托管推理 |
| **pyvis** | 互動式知識圖譜視覺化 |
| **Streamlit** | 前端 Web 介面 |

### 🚀 啟動方式

```bash
pip install -r requirements.txt
streamlit run app.py
```

### ⚙️ 環境變數（可選）

| 變數 | 說明 |
|------|------|
| `GROQ_API_KEY` | Groq API 金鑰（也可在側邊欄輸入） |
| `SPARQL_ENDPOINT` | Virtuoso SPARQL URL（預設 localhost:8890） |

### 🎨 圖形節點色彩說明

| 顏色 | 說明 |
|------|------|
| 🔵 藍色橢圓 | 主體節點（Subject URI） |
| 🔴 紅色橢圓 | 客體節點（Object URI） |
| 🟢 綠色方框 | 文字值（Literal） |
""")
