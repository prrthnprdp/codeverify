import streamlit as st
from ai_detection import analyze_ai_likelihood
from pdf_report import generate_pdf_report_bytes

st.set_page_config(page_title="AI Code Detector", layout="wide")
st.title("🤖 AI Code Detector")

pasted_code = st.text_area("Paste Python code to analyze", height=240)

if st.button("Analyze AI Likelihood"):
    if pasted_code.strip():
        result = analyze_ai_likelihood(pasted_code)
        st.metric("AI Likelihood Score", f"{result['score']}%")
        st.write(result["explanation"])
        st.subheader("Suspicious Sections")
        st.code(result["suspicious"], language="python")

        # PDF report
        pdf_bytes = generate_pdf_report_bytes(
            code_sources=[("pasted_code.py", pasted_code)],
            combined_code=pasted_code,
            plagiarism_result={"score": 0, "explanation": "", "suspicious": ""},
            ai_result=result,
            line_compare_summary=""
        )
        st.download_button(
            label="Download AI Detection Report (PDF)",
            data=pdf_bytes,
            file_name="AI_Detection_Report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("Please paste some code to ana