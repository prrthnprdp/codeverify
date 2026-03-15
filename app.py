# app.py
# Streamlit home page for CodeVerify with navigation to different tools

import streamlit as st

st.set_page_config(page_title="CodeVerify - Plagiarism & AI Code Detector", layout="wide")

st.markdown("""
<style>
    h1 {
        font-size: 52px !important;
    }
    h3 {
        font-size: 40px !important;
    }
    .stMarkdown p, .stMarkdown li {
        font-size: 32px !important;
        line-height: 1.4 !important;
    }
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] li, [data-testid="stSidebarNav"] li {
        font-size: 32px !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📘 CodeVerify: Academic Code Plagiarism & AI Detection")
st.markdown(
    "A comprehensive offline tool for detecting plagiarism and AI-generated code patterns. "
    "Uses logical, statistical, and heuristic methods only—no AI models, no external APIs."
)

st.divider()

# Feature cards
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 Plagiarism Checker")
    st.write(
        "Compare two code snippets to detect plagiarism, code reuse, and structural similarities. "
        "Analyzes token patterns, line-by-line overlap, and code structure."
    )
    if st.button("Open Plagiarism Checker", key="plagiarism_btn"):
        st.switch_page("pages/1_Plagiarism_Checker.py")

with col2:
    st.subheader("🤖 AI Detector")
    st.write(
        "Analyze code for evidence of AI-generated patterns. "
        "Examines indentation uniformity, comment density, repetitive structures, and identifier entropy."
    )
    if st.button("Open AI Detector", key="ai_btn"):
        st.switch_page("pages/2_AI_Detector.py")

st.divider()

# Instructions
with st.sidebar:
    st.header("ℹ️ Instructions")
    st.markdown(
        """
        **Plagiarism Checker:**
        - Upload two code files or paste two snippets
        - Select programming language
        - Get similarity score and diff preview
        - Download PDF report
        
        **AI Detector:**
        - Upload or paste single code file
        - Get AI-likelihood score
        - See heuristic indicators
        - View suspicious code sections
        """
    )

st.divider()
st.caption(
    "CodeVerify provides heuristic analysis for educational use on academic integrity. "
    "All analysis is offline. Scores are indicative and should be interpreted with discretion."
)