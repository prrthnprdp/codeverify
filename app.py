# app.py
# Streamlit UI for CodeVerify: Academic code plagiarism & AI-likelihood detection
# Works offline; uses logical, statistical, and heuristic methods only.

import streamlit as st
from plagiarism import analyze_plagiarism, compare_line_by_line
from ai_detection import analyze_ai_likelihood
from pdf_report import generate_pdf_report_bytes
from utils import load_code_from_file, safe_preview

st.set_page_config(page_title="CodeVerify - Plagiarism & AI Code Detector", layout="wide")

# Header
st.title("📘 CodeVerify: Academic Code Plagiarism & AI Detection")
st.markdown(
    "Upload or paste Python code to analyze for plagiarism and AI-generated patterns. "
    "This tool uses logical, statistical, and heuristic methods—no AI models, no external APIs."
)

# Sidebar instructions
with st.sidebar:
    st.header("Instructions")
    st.markdown(
        "- Upload one or more `.py` files or paste code.\n"
        "- Click **Analyze Code** to compute plagiarism and AI-likelihood scores.\n"
        "- View suspicious sections and explanations.\n"
        "- Download a PDF report for academic records.\n"
        "- All analysis is offline and rule-based."
    )
    st.markdown("**Ethics:** Use responsibly for learning and academic integrity.")

# Inputs
uploaded_files = st.file_uploader("Upload Python files", type=["py"], accept_multiple_files=True)
pasted_code = st.text_area("Or paste your Python code here", height=240, placeholder="# Paste Python code...")

# Aggregate code from uploads and paste
code_sources = []
if uploaded_files:
    for uf in uploaded_files:
        content = load_code_from_file(uf)
        if content.strip():
            code_sources.append((uf.name, content))
if pasted_code.strip():
    code_sources.append(("pasted_code.py", pasted_code))

# Analyze button
analyze_clicked = st.button("Analyze Code")

if analyze_clicked:
    if not code_sources:
        st.warning("Please upload at least one Python file or paste code.")
    else:
        # Combine all code into a single corpus for analysis
        combined_code = "\n\n".join([src for _, src in code_sources])

        with st.spinner("Analyzing code with logical and heuristic methods..."):
            # Plagiarism analysis
            plagiarism_result = analyze_plagiarism(combined_code)

            # Line-by-line difflib comparison across files (if multiple)
            line_compare_summary = ""
            if len(code_sources) > 1:
                line_compare_summary = compare_line_by_line([src for _, src in code_sources])

            # AI-likelihood analysis
            ai_result = analyze_ai_likelihood(combined_code)

        # Results layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔍 Plagiarism Detection")
            st.metric("Plagiarism Score", f"{plagiarism_result['score']}%")
            st.caption("Score combines token similarity and structural similarity, ignoring variable renaming and formatting.")
            st.markdown("**Explanation**")
            st.write(plagiarism_result["explanation"])

            if line_compare_summary:
                st.markdown("**Line-by-line comparison summary**")
                st.code(line_compare_summary, language="text")

        with col2:
            st.subheader("🤖 AI-Generated Code Likelihood")
            st.metric("AI Likelihood Score", f"{ai_result['score']}%")
            st.caption("Rule-based indicators: repetitive structures, uniform indentation, excessive commenting, statistical regularity.")
            st.markdown("**Explanation**")
            st.write(ai_result["explanation"])

        st.subheader("📄 Suspicious Code Sections")
        suspicious_preview = safe_preview(plagiarism_result["suspicious"], ai_result["suspicious"])
        if suspicious_preview.strip():
            st.code(suspicious_preview, language="python")
        else:
            st.info("No strongly suspicious sections detected based on current thresholds.")

        # PDF report
        st.subheader("🧾 Download PDF Report")
        pdf_bytes = generate_pdf_report_bytes(
            code_sources=code_sources,
            combined_code=combined_code,
            plagiarism_result=plagiarism_result,
            ai_result=ai_result,
            line_compare_summary=line_compare_summary,
        )
        st.download_button(
            label="Download CodeVerify Report (PDF)",
            data=pdf_bytes,
            file_name="CodeVerify_Report.pdf",
            mime="application/pdf",
        )

# Footer
st.divider()
st.caption(
    "CodeVerify provides heuristic analysis for educational use. "
    "Scores are indicative and should be interpreted with academic discretion."
)