import streamlit as st

st.set_page_config(page_title="CodeVerify", layout="centered")

st.title("👋 Welcome to CodeVerify")
st.markdown("Choose a tool to get started:")

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/1_Plagiarism_Checker.py", label="🔍 Plagiarism Checker", icon="🧾")

with col2:
    st.page_link("pages/2_AI_Detector.py", label="🤖 AI Code Detector", icon="🧠")

st.markdown("---")
st.caption("CodeVerify is an offline tool for academic code analysis. Choose a feature to begin.")
