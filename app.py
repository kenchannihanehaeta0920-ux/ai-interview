import streamlit as st
import streamlit.components.v1 as components

# ページの設定
st.set_page_config(page_title="救急医療学科 特別面談室", layout="centered")

# タイトル
st.title("🚑 特別個別面談（ロジスティクス・モラル編）")
st.write("---")

# 学生への案内（教育的な意図を明記）
st.warning("⚠️ **本面談は、救急医療現場における『規律』と『記録の正確性』を再確認するための演習です。**")
st.info("右下のアイコンをクリックして面談を開始してください。感情的な弁明ではなく、プロフェッショナルとしての論理的な説明を求めます。")

# ElevenLabs ウィジェット（先生のエージェントIDを反映済み）
components.html(
    """
    <div style="display: flex; justify-content: center; align-items: center; height: 500px;">
        <elevenlabs-convai agent-id="agent_2601kr2yvn8rf77vb25f0zhd85jz"></elevenlabs-convai>
    </div>
    <script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async type="text/javascript"></script>
    """,
    height=600,
)

st.write("---")
st.caption("© 2026 Nippon Sport Science University - Dept. of EMS (Suzuki Lab)")
