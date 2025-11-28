import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import io

# --- 1. 網頁基本設定 ---
st.set_page_config(
    page_title="咖啡咖萬能助理",
    page_icon="☕",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. CSS 美化工程 ---
st.markdown("""
    <style>
    /* 全站背景顏色 */
    .stApp { background-color: #2E2727; }
    
    /* 全站文字顏色 */
    h1, h2, h3, p, div, label, span, li { color: #E0D8CC !important; }
    
    /* 標題特別樣式 */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        text-align: center;
        font-weight: bold;
        color: #C2A386 !important;
    }
    
    /* 側邊欄背景 */
    section[data-testid="stSidebar"] { background-color: #3B2F2F; }

    /* 輸入框樣式 */
    .stTextInput input, .stTextArea textarea {
        background-color: #4A3B3B !important;
        color: #FFFFFF !important;
        border: 2px solid #8B5A2B !important;
        border-radius: 10px;
    }
    input::placeholder, textarea::placeholder {
        color: #C2A386 !important;
        opacity: 1 !important;
        font-weight: bold;
    }
    
    /* 檔案上傳區 */
    [data-testid="stFileUploader"] {
        background-color: #4A3B3B;
        border-radius: 10px;
        padding: 10px;
        border: 2px dashed #8B5A2B;
    }
    [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] div {
        color: #E0D8CC !important;
    }

    /* 按鈕樣式 */
    .stButton>button {
        background-color: #6F4E37;
        color: white !important;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
        margin-top: 10px;
    }
    .stButton>button:hover {
        background-color: #8B5A2B;
        transform: scale(1.02);
    }

    /* 分頁標籤樣式 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #2E2727; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #3B2F2F;
        border-radius: 10px 10px 0px 0px;
        color: #AB988B !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6F4E37;
        color: #FFFFFF !important;
        font-weight: bold;
    }

    /* 聊天室氣泡優化 */
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #4A3B3B;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #3B2F2F;
        border: 1px solid #6F4E37;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 初始化記憶體 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# --- 4. 標題區 ---
st.markdown("<h1>☕ 咖啡咖萬能助理</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #AB988B !important;'>來杯咖啡的時間，讓咖啡咖幫你解決吧！</p>", unsafe_allow_html=True)
st.markdown("---")

# --- 5. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 設定中心")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ VIP 自動通關")
    else:
        api_key = st.text_input("輸入 API Key", type="password")
        if not api_key:
            st.info("請輸入 API Key 才能使用 AI 功能喔！")
    
    st.markdown("---")
    
    if st.button("🗑️ 清除對話紀錄"):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("###### © 2025 咖啡咖萬能助理")
    st.markdown("###### Designed by Coffee0821")

# --- 6. 功能分頁 ---
tab1, tab2 = st.tabs(["📝 文章摘要", "👁️ 視覺辨識"])

# === 功能一：文章摘要 ===
with tab1:
    st.subheader("📝 幫你讀文章")
    input_type = st.radio("請選擇來源：", ["✍️ 貼上文字", "🌐 網頁連結 (URL)", "📄 上傳 PDF"], horizontal=True)
    
    final_text_content = ""

    if input_type == "✍️ 貼上文字":
        user_text = st.text_area("請貼上文章內容：", height=200, placeholder="在此貼上新聞、報告、會議記錄...")
        final_text_content = user_text
    elif input_type == "🌐 網頁連結 (URL)":
        url = st.text_input("請輸入文章網址：", placeholder="https://example.com/news")
        if url:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                paragraphs = soup.find_all('p')
                final_text_content = " ".join([p.get_text() for p in paragraphs])
                st.info(f"✅ 成功抓取，共 {len(final_text_content)} 字")
            except Exception as e:
                st.error(f"無法讀取網頁：{e}")
    elif input_type == "📄 上傳 PDF":
        uploaded_pdf = st.file_uploader("請上傳 PDF 文件", type="pdf")
        if uploaded_pdf:
            try:
                reader = PdfReader(uploaded_pdf)
                text_list = []
                for page in reader.pages:
                    text_list.append(page.extract_text())
                final_text_content = "\n".join(text_list)
                st.info(f"✅ 成功讀取 PDF，共 {len(reader.pages)} 頁")
            except Exception as e:
                st.error(f"PDF 讀取失敗：{e}")

    if st.button("🚀 幫我抓重點", key="btn_text"):
        if not api_key:
            st.error("請先輸入 API Key！")
        elif not final_text_content or len(final_text_content.strip()) < 10:
            st.warning("內容太少！")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash')
                with st.spinner('☕ AI 正在研磨重點...'):
                    prompt = f"請用文章內容語言，將這篇文章整理成 5 個重點：\n{final_text_content[:20000]}"
                    response = model.generate_content(prompt)
                st.success("完成！")
                st.markdown("### 重點整理：")
                st.write(response.text)
            except Exception as e:
                st.error(f"錯誤：{e}")

# === 功能二：視覺辨識 (理性思考版) ===
with tab2:
    st.subheader("👁️ 幫你看照片")
    
    with st.expander("📸 點擊這裡 查看/更換 照片", expanded=True):
        uploaded_file_ai = st.file_uploader("請先上傳照片 (JPG/PNG)", type=["jpg", "png"], key="ai_upload")
        image = None
        if uploaded_file_ai:
            image = Image.open(uploaded_file_ai)
            st.image(image, caption="目前分析的照片", use_container_width=True)
            if st.session_state.last_uploaded_file != uploaded_file_ai.name:
                st.session_state.chat_history = []
                st.session_state.last_uploaded_file = uploaded_file_ai.name
    
    st.divider()
    st.markdown("### 💬 對話區")

    for role, text in st.session_state.chat_history:
        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.write(text)
        else:
            with st.chat_message("assistant", avatar="☕"):
                st.write(text)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("👉 請輸入問題...", placeholder="例如:圖片裡的咖啡看起來好喝嗎?")
        submit_button = st.form_submit_button("🚀 發送問題")

    if submit_button and user_input:
        if not api_key:
            st.error("請先輸入 API Key！")
        elif not image:
            st.error("請先上傳照片！")
        else:
            st.session_state.chat_history.append(("user", user_input))

            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                history_context = ""
                for role, text in st.session_state.chat_history[:-1]:
                    role_name = "User" if role == "user" else "AI Assistant"
                    history_context += f"{role_name}: {text}\n"

                # 【關鍵修改】使用 CoT (Chain of Thought) 思維鏈指令
                final_prompt = f"""
                You are an intelligent AI visual analyst.
                
                Previous Conversation History: 
                {history_context}
                
                Current User Question: 
                {user_input}
                
                CRITICAL REASONING INSTRUCTIONS:
                1. Answer in the SAME language as the User's question.
                2. If the user disagrees with your analysis (e.g., the count):
                   - Do NOT just blindly agree.
                   - Instead, RE-EXAMINE the image data critically.
                   - Look for potential "False Positives" (e.g., confusing a coat, statue, or poster for a real person).
                   - Explain your reasoning process: "I initially thought X was a person, but looking closer, it seems to be Y."
                   - If you still honestly see 7, respectfully describe where each one is so the user can verify.
                   - If you realize you were wrong, explain WHAT object tricked you.
                """
                
                with st.spinner("AI 正在重新推理與觀察..."):
                    response = model.generate_content([final_prompt, image])
                
                st.session_state.chat_history.append(("assistant", response.text))
                st.rerun()
                
            except Exception as e:
                st.error(f"錯誤：{e}")