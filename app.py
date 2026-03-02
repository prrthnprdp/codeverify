# app.py
import streamlit as st
from plagiarism import compare_codes
from utils import load_code_from_file, detect_language
from pdf_report import generate_pdf_report_bytes

st.set_page_config(page_title="CodeVerify", layout="wide")
st.title("🧪 CodeVerify: Plagiarism Detection for Python, C, and C++")

st.markdown("""
Upload two code files (original and suspected) to detect plagiarism using logical and statistical methods.
This tool works **offline** and supports **Python (.py)**, **C (.c)**, and **C++ (.cpp)** files.
""")

# Upload section
col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("Upload Original Code", type=["py", "c", "cpp"], key="file1")
with col2:
    file2 = st.file_uploader("Upload Suspected Code", type=["py", "c", "cpp"], key="file2")

# Compare button
if st.button("Compare for Plagiarism"):
    if not file1 or not file2:
        st.warning("Please upload both files.")
    else:
        code1 = load_code_from_file(file1)
        code2 = load_code_from_file(file2)
        lang1 = detect_language(file1.name)
        lang2 = detect_language(file2.name)

        if lang1 != lang2:
            st.error(f"Language mismatch: {lang1} vs {lang2}. Please upload files of the same language.")
        elif lang1 == "Unknown":
            st.error("Unsupported file type. Please upload .py, .c, or .cpp files.")
        else:
            with st.spinner(f"Analyzing {lang1} files for plagiarism..."):
                result = compare_codes(code1, code2, lang1)

            st.success("Analysis complete!")

            # Display results
            st.metric("Plagiarism Score", f"{result['score']}%")
            st.subheader("Explanation")
            st.text(result["explanation"])

            st.subheader("Similar Code Sections")
            st.code(result["diff_preview"], language="text")

            # PDF report
            st.subheader("📄 Download PDF Report")
            pdf_bytes = generate_pdf_report_bytes(
                file1.name, file2.name, lang1, result
            )
            st.download_button(
                label="Download Report",
                data=pdf_bytes,
                file_name="CodeVerify_Report.pdf",
                mime="application/pdf"
            )

# Footer
st.markdown("---")
st.caption("CodeVerify uses logical and statistical methods only. No AI/ML models or external APIs are used. Designed for academic integrity and offline use.")