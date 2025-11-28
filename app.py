import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="咖啡咖萬能助理", page_icon="🤖")
st.title("咖啡咖萬能助理")
st.write("可以統整文字也可以判別圖片唷！")

# --- 2. 共用設定 (側邊欄) ---
# API Key 只需要輸入一次，兩個功能都能用
with st.sidebar:
    st.header("🔑 權限設定")
    
    # 檢查是否已在系統後台設定了鑰匙 (Secrets)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ 已啟用自動授權模式")
        st.info("目前使用開發者的額度，請愛惜使用。")
    else:
        # 如果後台沒設定，就讓使用者自己輸入
        api_key = st.text_input("請輸入 Gemini API Key", type="password")
        st.markdown("只要輸入一次，所有功能通用！")
    st.markdown("---")
    st.markdown("只要輸入一次，所有功能通用！")

# --- 3. 建立分頁 (Tabs) ---
# 這裡我們建立兩個標籤頁
tab1, tab2 = st.tabs(["📄 文章摘要", "👁️ 視覺辨識"])

# ==========================================
# 功能一：文章摘要 (Tab 1)
# ==========================================
with tab1:
    st.header("📄 智能文章摘要")
    user_text = st.text_area("請貼上長篇文章：", height=200, placeholder="在此貼上新聞、報告或會議記錄...")
    
    if st.button("🚀 生成摘要", key="btn_text"): # key 是為了區分兩個按鈕
        if not api_key:
            st.error("請先在左側輸入 API Key！")
        elif not user_text:
            st.warning("請先貼上文章內容！")
        else:
            try:
                genai.configure(api_key=api_key)
                # 使用我們測試過最強的 2.0 模型
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                with st.spinner('AI 正在閱讀並思考重點...'):
                    prompt = f"請將以下這篇文章整理成 3-5 個關鍵重點，並用繁體中文列點說明：\n\n{user_text}"
                    response = model.generate_content(prompt)
                
                st.success("摘要完成！")
                st.markdown("### 📝 重點整理：")
                st.write(response.text)
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# ==========================================
# 功能二：視覺辨識 (Tab 2)
# ==========================================
with tab2:
    st.header("👁️ 超級視覺眼")
    uploaded_file = st.file_uploader("上傳圖片 (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="預覽圖片", use_container_width=True)
        
        # 預設問題設為空白，讓使用者自己填，或者給個預設值
        default_question = "這張圖裡面有什麼？如果有物件請幫我計算數量。"
        user_prompt = st.text_input("你想問這張圖什麼？", value=default_question)

        if st.button("🚀 開始分析圖片", key="btn_image"):
            if not api_key:
                st.error("請先在左側輸入 API Key！")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    
                    with st.spinner('AI 正在觀察圖片細節...'):
                        response = model.generate_content([user_prompt, image])
                    
                    st.success("分析完成！")
                    st.markdown("### 🔍 分析結果：")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"發生錯誤：{e}")