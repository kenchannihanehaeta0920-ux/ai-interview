import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import requests
import base64
import datetime

# --- 1. ドライブ保存（GAS窓口）の設定 ---
def upload_to_drive_via_gas(audio_bytes, filename):
    # SecretsからURLを取得
    gas_url = st.secrets.get("GAS_URL")
    if not gas_url:
        return False
    
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    payload = {"base64": b64_audio, "filename": filename}
    
    try:
        response = requests.post(gas_url, json=payload)
        return response.text == "Success"
    except:
        return False

# --- 2. 認証・ログイン設定 ---
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

# --- 3. AI初期化（ここが NotFound 解消の鍵） ---
st.title("🚑 モラルガイダンス特別面談")

# 毎回APIキーを設定
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        # 枝葉を切り落とした最もシンプルな名前を指定します
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", 
            system_instruction="あなたは救急医療学科の教員です。指示不備の要因を分析させてください。"
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        # 万が一失敗した時、あなたのAPIキーで使えるモデルを画面に表示します（原因特定のため）
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        st.error(f"AI起動失敗。利用可能なモデル例: {available_models[:3]}")
        st.stop()

# --- 4. 音声入力と自動処理 ---
st.write("---")
audio = mic_recorder(start_prompt="面談を開始（録音）", stop_prompt="送信（録音終了）", key='recorder')

if audio:
    with st.spinner("AIが確認中..."):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_{timestamp}.wav"
        
        # 1. ドライブ保存
        if upload_to_drive_via_gas(audio['bytes'], filename):
            # 2. AIへ送信
            audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
            try:
                response = st.session_state.chat.send_message([audio_part, "教員として返答してください。"])
                st.session_state.messages.append({"role": "user", "content": f"（録音を送信しました：{filename}）"})
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"AI送信エラー: {e}")
        else:
            st.error("保存に失敗しました。SecretsのGAS_URLを確認してください。")
