import streamlit as st
from ai_detection import analyze_ai_likelihood
from utils import load_code_from_file

st.set_page_config(page_title="AI Detection", layout="wide")
st.title("🤖 AI-Generated Code Detector")

st.markdown("""
Upload or paste Python code to analyze its likelihood of being AI-generated.
The detector uses heuristic methods based on code patterns, uniformity, and structure.
""")

# --- Code Input ---
st.subheader("📝 Input Code")
col1, col2 = st.columns([2, 1])
with col1:
    code_text = st.text_area("Paste or type your Python code here:", height=300, key="ai_code")
with col2:
    code_file = st.file_uploader("Or upload a Python file (.py)", type=["py"], key="ai_file")

# --- Analyze Button ---
if st.button("Analyze for AI Patterns"):
    code = code_text.strip() if code_text.strip() else (
        load_code_from_file(code_file) if code_file else "")

    if not code:
        st.warning("Please provide code — either by typing or uploading a file.")
    else:
        with st.spinner("Analyzing code for AI-generated patterns..."):
            result = analyze_ai_likelihood(code)

        st.success("Analysis complete!")

        st.metric("AI Likelihood Score", f"{result['score']}%")
        st.subheader("📊 Explanation")
        st.text(result["explanation"])

        if result.get("suspicious"):
            st.subheader("🚨 Suspicious Code Sections")
            st.code(result["suspicious"], language="python")

st.markdown("---")
st.caption("CodeVerify AI Detector uses heuristic patterns only. No AI/ML models or external APIs. For educational and academic integrity use.")