from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

def _draw_wrapped_text(c, x, y, text, max_width, line_height=12, font_name="Helvetica", font_size=10):
    """Draw wrapped text within max_width, moving upward as lines are added."""
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y

def generate_pdf_report_bytes(code_sources, combined_code, plagiarism_result, ai_result, line_compare_summary=""):
    """
    Build a PDF report with analysis summary, scores, explanations, and conclusion.
    Returns PDF bytes for Streamlit download.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CodeVerify Analysis Report")

    # Scores
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 90, f"Plagiarism Score: {plagiarism_result['score']}%")
    c.drawString(50, height - 110, f"AI Likelihood Score: {ai_result['score']}%")

    # Sources
    y = height - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Analyzed Sources:")
    y -= 18
    c.setFont("Helvetica", 10)
    for name, _ in code_sources:
        c.drawString(60, y, f"- {name}")
        y -= 12

    # Plagiarism explanation
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Plagiarism Explanation:")
    y -= 18
    y = _draw_wrapped_text(c, 50, y, plagiarism_result["explanation"], max_width=500)

    # AI explanation
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "AI Detection Explanation:")
    y -= 18
    y = _draw_wrapped_text(c, 50, y, ai_result["explanation"], max_width=500)

    # Line-by-line summary (if any)
    if line_compare_summary:
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Line-by-line Comparison Summary:")
        y -= 18
        y = _draw_wrapped_text(c, 50, y, line_compare_summary[:3000], max_width=500)

    # Conclusion
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Conclusion:")
    y -= 18
    conclusion = (
        "This report provides heuristic analysis of the submitted code for plagiarism and AI-generated patterns. "
        "Results are indicative and should be interpreted with academic discretion. "
        "The system uses logical, statistical, and rule-based methods only, without AI models or external services."
    )
    y = _draw_wrapped_text(c, 50, y, conclusion, max_width=500)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()