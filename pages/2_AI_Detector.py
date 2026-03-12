import streamlit as st
from ai_detection import analyze_ai_likelihood

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
    else:
        st.warning("Please paste some code to analyze.")