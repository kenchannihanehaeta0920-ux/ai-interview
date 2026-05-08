import streamlit as st
import streamlit.components.v1 as components

# ページの設定（ブラウザのタブ名など）
st.set_page_config(page_title="救急医療学科 特別面談室", layout="centered")

# タイトルと説明文
st.title("🚑 特別個別面談（ロジスティクス・モラル編）")
st.write("---")

st.warning("⚠️ **これは救急医療現場での『記録の正確性』と『指示の遵守』を学ぶためのシミュレーションです。**")
st.info("下のアイコンをクリックして、面談を開始してください。マイクの使用を求められた場合は『許可』を選択すること。")

# ElevenLabs ウィジェットの埋め込み
# 先生専用のエージェントID（agent_2601kr2yvn8rf77vb25f0zhd85jz）を使用
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
