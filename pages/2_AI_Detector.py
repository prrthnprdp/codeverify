import streamlit as st
import os
from ai_detection import analyze_ai_likelihood
from utils import load_code_from_file, inject_custom_css

st.set_page_config(page_title="AI Detection", layout="wide")

inject_custom_css()

st.title("AI Code Detector")

st.info("""
Analyze Python, C, or C++ code for AI-generated patterns using heuristic analysis.
""")

# --- Input Section ---
with st.container():
    st.subheader("Input Code")
    code_text = st.text_area("Paste code here:", height=300, key="ai_code")
    code_file = st.file_uploader("Or upload file (.py, .c, .cpp)", type=["py", "c", "cpp"], key="ai_file")

# --- Language Selection ---
language = st.selectbox(
    "Programming Language",
    ["Auto-detect", "Python", "C", "C++"],
    key="ai_language"
)

# --- Analyze Button ---
if st.button("Analyze for AI Patterns"):
    code = ""
    lang_arg = None if language == "Auto-detect" else language

    if code_text.strip():
        code = code_text.strip()
    elif code_file:
        code = load_code_from_file(code_file)
        # Auto-detect language from file extension if user chose Auto-detect
        if lang_arg is None:
            ext = os.path.splitext(code_file.name)[1].lower()
            if ext == ".py":
                lang_arg = "Python"
            elif ext == ".c":
                lang_arg = "C"
            elif ext == ".cpp":
                lang_arg = "C++"

    if not code:
        st.warning("Please provide code — either by typing or uploading a file.")
    else:
        with st.spinner("Analyzing code for AI-generated patterns..."):
            result = analyze_ai_likelihood(code, language=lang_arg)

        st.success("Analysis complete!")

        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            st.metric("AI Likelihood Score", f"{result['score']}%")

        with res_col2:
            st.subheader("📊 Explanation")
            st.info(result["explanation"])

        if result.get("suspicious"):
            with st.expander("🚨 Suspicious Code Sections", expanded=True):
                # Determine display language for syntax highlighting
                first_line = result["explanation"].split("\n")[0]
                if "C++" in first_line:
                    display_lang = "cpp"
                elif first_line.endswith("C"):
                    display_lang = "c"
                else:
                    display_lang = "python"
                st.code(result["suspicious"], language=display_lang)

st.markdown("---")
st.caption("CodeVerify AI Detector uses heuristic patterns only. No AI/ML models or external APIs. For educational and academic integrity use.")