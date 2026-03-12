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

def generate_pdf_report_bytes(file1_name, file2_name, language, result):
    """
    Generate a PDF report for plagiarism comparison.
    Includes language, score, explanation, and diff preview.
    Returns PDF bytes for download.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CodeVerify Plagiarism Report")

    # File names and language
    y = height - 90
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Original File: {file1_name}")
    y -= 20
    c.drawString(50, y, f"Suspected File: {file2_name}")
    y -= 20
    c.drawString(50, y, f"Detected Language: {language}")
    y -= 30

    # Score
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Plagiarism Score: {result['score']}%")
    y -= 30

    # Explanation
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Explanation:")
    y -= 18
    y = _draw_wrapped_text(c, 50, y, result["explanation"], max_width=500)

    # Similar code preview
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Similar Code Sections:")
    y -= 18
    preview = result["diff_preview"][:3000]  # Limit to avoid overflow
    y = _draw_wrapped_text(c, 50, y, preview, max_width=500)

    # Footer
    y -= 20
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, y, "Note: This report is generated using logical and statistical methods only. No AI or external services were used.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()