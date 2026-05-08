import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io
import datetime

# --- 1. Google Drive 自動保存用の設定（共有ドライブ対応版） ---
def upload_to_drive(audio_bytes, filename):
    try:
        # StreamlitのSecretsからサービスアカウント情報を取得
        info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)

        # 【重要】共有ドライブ内に作成した「新しいフォルダ」のIDを入力してください
        FOLDER_ID = "1uBO_fZYG-c4T7ORXxavpx-5YertAzAPb" 
        
        file_metadata = {
            'name': filename,
            'parents': [FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(audio_bytes), mimetype='audio/wav')
        
        # 共有ドライブへの書き込みを許可する設定（supportsAllDrives=True）を追加
        service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id',
            supportsAllDrives=True 
        ).execute()
        return True
    except Exception as e:
        st.error(f"ドライブへの保存に失敗しました: {e}")
        return False

# --- 2. 認証設定 ---
ACCESS_PASSWORD = "nittai2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏥 救急医療学科 AI面談室")
    st.write("この面談を受けるには、指示されたアクセスコードが必要です。")
    user_password = st.text_input("アクセスコードを入力してください", type="password")
    if st.button("ログイン"):
        if user_password == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("コードが正しくありません")
    st.stop()

# --- 3. AI・チャット設定 ---
st.title("🚑 モラルガイダンス特別面談")
st.caption("指示不備の要因分析と再発防止策の検討")
st.info("※この面談は音声入力のみです。ご自身の言葉でしっかり話してください。")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("APIキーが設定されていません。")

SYSTEM_INSTRUCTION = """
あなたは救急医療学科のリスク管理担当教員です。
指示（点数のスクショ提出）を守れなかった学生に対し、要因を掘り下げる面談を行います。
1. なぜ「スクショ忘れ」が起きたのか、本人の声を聞き、確認プロセスを振り返らせる。
2. 医療現場での「記録漏れ」に例えて、その重大なリスクを自覚させる。
3. 最後に、具体的な（「気をつけます」以外の）再発防止策を本人の口から宣言させる。
丁寧ですが、厳格なプロの姿勢で対応してください。
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_INSTRUCTION)
    st.session_state.chat = model.start_chat(history=[])

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 音声入力と自動処理 ---
st.write("---")
st.write("🎤 **ボタンを押して話し、話し終わったらもう一度押してください**")
audio = mic_recorder(
    start_prompt="面談を開始する（録音）",
    stop_prompt="話を送信する（録音終了）",
    key='recorder'
)

if audio:
    with st.spinner("AIが確認中 ＆ ドライブへ録音を保存中..."):
        # ファイル名を「日付_時刻.wav」で作成
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_{timestamp}.wav"
        
        # 1. Google Driveへ自動保存を実行
        success = upload_to_drive(audio['bytes'], filename)
        
        # 保存に失敗した場合は処理を中断（AIの連続エラーを防ぐため）
        if not success:
            st.warning("音声の保存に失敗したため、AI面談を一時中断します。共有ドライブの設定を確認してください。")
            st.stop()
        
        # 2. 保存成功時のみ、Gemini AIへ音声を送信して解析
        audio_part = {"mime_type": "audio/wav", "data": audio['bytes']}
        response = st.session_state.chat.send_message([audio_part, "学生からの返答です。教員として次の問いを投げてください。"])
        
        # 3. 画面に反映
        st.session_state.messages.append({"role": "user", "content": f"（音声を送信しました：{filename}）"})
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
