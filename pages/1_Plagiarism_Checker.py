import streamlit as st
from plagiarism import compare_codes
from ai_detection import analyze_ai_likelihood
from pdf_report import generate_pdf_report_bytes
from utils import load_code_from_file, inject_custom_css

st.set_page_config(page_title="Plagiarism Checker", layout="wide")

inject_custom_css()


st.title("🔍 Plagiarism Checker")

st.markdown("""
You can either **upload a file** or **paste/type code manually** for both the original and suspected code. If both are provided, the manually entered code will be used.
""")

# --- Original Code Input ---
st.subheader("📄 Original Code")
col1, col2 = st.columns([2, 1])
with col1:
    original_code_text = st.text_area("Paste or type the original code here:", height=300, key="original_code")
with col2:
    original_file = st.file_uploader("Or upload original code file (.py, .c, .cpp)", type=["py", "c", "cpp"], key="original_file")

# --- Suspected Code Input ---
st.subheader("📄 Suspected Code")
col3, col4 = st.columns([2, 1])
with col3:
    suspected_code_text = st.text_area("Paste or type the suspected code here:", height=300, key="suspected_code")
with col4:
    suspected_file = st.file_uploader("Or upload suspected code file (.py, .c, .cpp)", type=["py", "c", "cpp"], key="suspected_file")

# --- Language Selection ---
language = st.selectbox("Select Programming Language", ["Python", "C", "C++"])

# --- Compare Button ---
if st.button("Compare for Plagiarism"):
    original_code = original_code_text.strip() if original_code_text.strip() else (
        load_code_from_file(original_file) if original_file else "")
    suspected_code = suspected_code_text.strip() if suspected_code_text.strip() else (
        load_code_from_file(suspected_file) if suspected_file else "")

    if not original_code or not suspected_code:
        st.warning("Please provide both original and suspected code — either by typing or uploading files.")
    else:
        with st.spinner(f"Analyzing {language} code for plagiarism..."):
            result = compare_codes(original_code, suspected_code, language)

        st.success("Analysis complete!")

        st.metric("Plagiarism Score", f"{result['score']}%")
        st.subheader("Explanation")
        st.text(result["explanation"])

        st.subheader("Similar Code Sections")
        st.code(result["diff_preview"], language="text")

        st.subheader("📄 Download PDF Report")
        original_name = original_file.name if original_file else "Original_Code_Input"
        suspected_name = suspected_file.name if suspected_file else "Suspected_Code_Input"
        code_sources = [(original_name, original_code), (suspected_name, suspected_code)]
        combined_code = original_code + "\n" + suspected_code
        ai_result = analyze_ai_likelihood(combined_code)
        pdf_bytes = generate_pdf_report_bytes(
            code_sources,
            combined_code,
            result,
            ai_result
        )
        st.download_button(
            label="Download Report",
            data=pdf_bytes,
            file_name="CodeVerify_Report.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.caption("CodeVerify uses only logical and statistical methods. No AI/ML or external services are used. Designed for academic integrity and offline use.")
