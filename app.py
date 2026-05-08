import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import requests
import base64
import datetime

# --- 1. GAS経由で保存する関数 ---
def upload_to_drive_via_gas(audio_bytes, filename):
    # 【重要】ステップ1でコピーしたURLをここに貼り付けてください
    GAS_URL = "https://script.google.com/macros/s/AKfycbyof1U79hsUD0_4rLTI4kwCK7lJPCDNSogGir44nvimVq_MrYVHgVQAD9igSpGlGUr0/exec"
    
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    payload = {"base64": b64_audio, "filename": filename}
    
    try:
        response = requests.post(GAS_URL, json=payload)
        return response.text == "Success"
    except:
        return False

# --- 2. 認証・AI設定 ---
ACCESS_PASSWORD = "nittai2026"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏥 救急医療学科 AI面談室")
    user_password = st.text_input("アクセスコード", type="password")
    if st.button("ログイン"):
        if user_password == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

st.title("🚑 モラルガイダンス特別面談")
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
    
    try:
        # モデル名を 'models/' から始まる正式名称に変更
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction="あなたは厳格な教員です。指示不備の要因を分析させてください。"
        )
        # チャットセッションを開始
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"AIの準備中にエラーが発生しました。APIキーの設定を確認してください: {e}")
        st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 3. 音声入力と自動処理 ---
audio = mic_recorder(start_prompt="面談を開始（録音）", stop_prompt="送信（録音終了）", key='recorder')

if audio:
    with st.spinner("AIが確認中 ＆ 保存中..."):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_{timestamp}.wav"
        
        # GAS経由で保存
        if upload_to_drive_via_gas(audio['bytes'], filename):
            # AIへ送信
            audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
            response = st.session_state.chat.send_message([audio_part, "教員として返答してください。"])
            st.session_state.messages.append({"role": "user", "content": f"（音声を送信しました：{filename}）"})
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()
        else:
            st.error("音声の保存に失敗しました。設定を確認してください。")
