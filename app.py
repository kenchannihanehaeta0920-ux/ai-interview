import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import requests
import base64
import datetime
from gtts import gTTS  # 音声合成ライブラリ
import io

# --- 1. ドライブ保存（GAS窓口） ---
def upload_to_drive_via_gas(audio_bytes, filename):
    gas_url = st.secrets.get("GAS_URL")
    if not gas_url: return False
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    payload = {"base64": b64_audio, "filename": filename}
    try:
        response = requests.post(gas_url, json=payload)
        return response.text == "Success"
    except: return False

# --- 2. 認証設定 ---
ACCESS_PASSWORD = "nittai2026"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏥 救急医療学科 AI面談室")
    user_password = st.text_input("アクセスコードを入力", type="password")
    if st.button("ログイン"):
        if user_password == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. AI初期化 ---
st.title("🚑 モラルガイダンス特別面談")
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower()]
        target_model = models[0] if models else "gemini-1.5-flash"
        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction="あなたは救急医療学科の厳格な教員です。医療現場での記録の重要性を説き、厳しい口調で指導してください。返答は短く（100文字程度）まとめてください。"
        )
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"AIエラー: {e}")
        st.stop()

# 履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. 音声入力と自動処理 ---
st.write("---")
st.write("🎤 **1. 録音ボタンを押して話し、終わったらもう一度押してください**")
audio = mic_recorder(start_prompt="録音開始", stop_prompt="録音終了", key='recorder')

if audio:
    st.write("✅ 録音完了。内容を確認して送信してください。")
    # 「送信」ボタンを出すことで、勝手に進むのを防ぎます
    if st.button("AI教員に送信する"):
        with st.spinner("AI教員が確認中..."):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_{timestamp}.wav"
            
            # ドライブ保存
            if upload_to_drive_via_gas(audio['bytes'], filename):
                # AIへ送信
                audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
                try:
                    response = st.session_state.chat.send_message([audio_part, "学生の返答です。指導を続けてください。"])
                    
                    # 音声合成 (TTS)
                    tts = gTTS(text=response.text, lang='ja')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    
                    # 履歴に追加
                    st.session_state.messages.append({"role": "user", "content": f"（音声を送信しました：{filename}）"})
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    # 音声を自動再生させるためのフラグ
                    st.session_state.play_audio = audio_fp.getvalue()
                    st.rerun()
                except Exception as e:
                    st.error(f"AI送信エラー: {e}")
            else:
                st.error("保存失敗")

# 音声の自動再生処理
if "play_audio" in st.session_state:
    st.audio(st.session_state.play_audio, format="audio/mp3", autoplay=True)
    del st.session_state.play_audio # 一度再生したら消す
