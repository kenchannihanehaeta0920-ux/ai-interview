import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import requests
import base64
import datetime

# --- 1. ドライブ保存（GAS窓口）の設定 ---
def upload_to_drive_via_gas(audio_bytes, filename):
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
    user_password = st.text_input("アクセスコードを入力してください", type="password")
    if st.button("ログイン"):
        if user_password == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. AI初期化（自己修復型） ---
st.title("🚑 モラルガイダンス特別面談")

api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        # 使用可能なFlashモデルを自動で検索
        models = [m.name for m in genai.list_models() 
                  if 'generateContent' in m.supported_generation_methods 
                  and 'flash' in m.name.lower()]
        
        target_model = models[0] if models else "gemini-1.5-flash"

        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction="あなたは救急医療学科の厳格な教員です。指示（スクショ提出）を守れなかった学生に対し、要因を掘り下げる面談を行ってください。医療現場での『記録漏れ』のリスクに例えて厳しく、しかし教育的に指導してください。"
        )
        st.session_state.chat = model.start_chat(history=[])
        
    except Exception as e:
        st.error(f"AIの準備中にエラーが発生しました。設定を確認してください: {e}")
        st.stop()

# チャット履歴の表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. 音声入力と自動処理 ---
st.write("---")
st.write("🎤 **ボタンを押して話し、話し終わったらもう一度押してください**")
audio = mic_recorder(start_prompt="面談を開始（録音）", stop_prompt="送信（録音終了）", key='recorder')

if audio:
    with st.spinner("AI教員が確認中..."):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_{timestamp}.wav"
        
        # 1. ドライブ保存（GAS経由）
        if upload_to_drive_via_gas(audio['bytes'], filename):
            # 2. AIへ送信
            audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
            try:
                response = st.session_state.chat.send_message([audio_part, "学生からの返答です。教員として次の問いを投げてください。"])
                st.session_state.messages.append({"role": "user", "content": f"（音声を送信しました：{filename}）"})
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"AI送信エラー: {e}")
        else:
            st.error("保存に失敗しました。SecretsのGAS_URLが正しく設定されているか確認してください。")
