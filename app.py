import streamlit as st
import google.generativeai as genai

# --- 1. 認証設定 ---
# 学生に伝えるパスワードです。必要に応じて変更してください。
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

# --- 2. メイン機能 ---
st.title("🚑 モラルガイダンス特別面談")
st.caption("指示不備の要因分析と再発防止策の検討")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("APIキーが設定されていません。StreamlitのSecrets設定を確認してください。")

# AI Studioでテストした指示内容です
SYSTEM_INSTRUCTION = """
あなたは救急医療学科のリスク管理担当教員です。
指示（点数のスクショ提出）を守れなかった学生に対し、要因を掘り下げる面談を行います。
1. なぜ「スクショ忘れ」が起きたのか、確認プロセスを振り返らせる。
2. 医療現場での「記録漏れ」に例えて、そのリスクを自覚させる。
3. 最後に、具体的な（「気をつけます」以外の）再発防止策を宣言させる。
丁寧ですが、厳格なプロの姿勢で対応してください。
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
    # 2026年現在、最も安定しているモデルを指定しています
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_INSTRUCTION)
    st.session_state.chat = model.start_chat(history=[])

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 学生の入力処理
if prompt := st.chat_input("先生に状況を説明してください"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = st.session_state.chat.send_message(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    with st.chat_message("assistant"):
        st.markdown(response.text)
