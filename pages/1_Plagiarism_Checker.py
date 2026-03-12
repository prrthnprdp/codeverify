import streamlit as st
from plagiarism import analyze_plagiarism, compare_line_by_line
from utils import load_code_from_file, safe_preview

st.set_page_config(page_title="Plagiarism Checker", layout="wide")
st.title("🔍 Plagiarism Checker")

uploaded_files = st.file_uploader("Upload Python files", type=["py"], accept_multiple_files=True)
pasted_code = st.text_area("Or paste your Python code here", height=240)

if st.button("Analyze Plagiarism"):
    code_sources = []
    if uploaded_files:
        for uf in uploaded_files:
            content = load_code_from_file(uf)
            if content.strip():
                code_sources.append((uf.name, content))
    if pasted_code.strip():
        code_sources.append(("pasted_code.py", pasted_code))

    if not code_sources:
        st.warning("Please upload or paste code.")
    else:
        combined_code = "\n\n".join([src for _, src in code_sources])
        result = analyze_plagiarism(combined_code)

        st.metric("Plagiarism Score", f"{result['score']}%")
        st.write(result["explanation"])
        st.subheader("Suspicious Sections")
        st.code(result["suspicious"], language="python")

        if len(code_sources) > 1:
            summary = compare_line_by_line(code_sources)
            st.subheader("Line-by-line Comparison")
            st.code(summary, language="text")