from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime

def _draw_header(c, width, height):
    """Draw a dark blue header bar with title and date."""
    c.setFillColor(colors.HexColor("#1e3d59"))
    c.rect(0, height - 80, width, 80, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 55, "CodeVerify Analysis Report")
    c.setFont("Helvetica", 10)
    c.drawString(width - 200, height - 30, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

def _draw_footer(c, width, page_num):
    """Draw a thin grey footer with page and disclaimer."""
    c.setFillColor(colors.grey)
    c.setFont("Helvetica", 8)
    c.drawString(50, 30, "CodeVerify Academic Integrity Tool - Offline Heuristic Analysis")
    c.drawRightString(width - 50, 30, f"Page {page_num}")

def _get_score_color(score):
    """Get color for score severity."""
    if score >= 70:
        return colors.red
    elif score >= 40:
        return colors.orange
    else:
        return colors.green

def _draw_wrapped_text(c, x, y, text, max_width, line_height=12, font_name="Helvetica", font_size=10, fill_color=colors.black):
    """Draw wrapped text within max_width, moving downward as lines are added."""
    c.setFont(font_name, font_size)
    c.setFillColor(fill_color)
    lines = []
    # Handle explicit newlines first
    for block in text.splitlines():
        if not block.strip():
            lines.append("")
            continue
        words = block.split()
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
        if y < 50: # Basic check to avoid drawing off the bottom
            break
        c.drawString(x, y, line)
        y -= line_height
    return y

def generate_pdf_report_bytes(code_sources, combined_code, plagiarism_result, ai_result, line_compare_summary=""):
    """
    Build a PDF report with analysis summary, scores, explanations, and conclusion.
    Enhanced with colored headers, severiry-based colors, and better layout.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Page 1 ---
    _draw_header(c, width, height)
    y = height - 120

    # Summary Section Background
    c.setStrokeColor(colors.lightgrey)
    c.setFillColor(colors.HexColor("#f8f9fa"))
    c.rect(40, y - 72, width - 80, 80, fill=True, stroke=True)


    y -= 25
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Analysis Summary")

    # Plagiarism Score
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "Plagiarism Score:")
    score = plagiarism_result['score']
    c.setFillColor(_get_score_color(score))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, y, f"{score}%")

    # AI Score
    y -= 20
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "AI Likelihood Score:")
    ai_score = ai_result['score']
    c.setFillColor(_get_score_color(ai_score))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, y, f"{ai_score}%")

    # Sources
    y -= 50
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Analyzed Sources:")
    y -= 20
    c.setFont("Helvetica", 10)
    for name, _ in code_sources:
        c.drawString(70, y, f"• {name}")
        y -= 15

    # Detailed sections
    sections = [
        ("Plagiarism Explanation", plagiarism_result["explanation"]),
        ("AI Detection Explanation", ai_result["explanation"])
    ]

    # Include detected matches if available
    if "diff_preview" in plagiarism_result and plagiarism_result["diff_preview"]:
        sections.append(("Identified Similar Code Sections", plagiarism_result["diff_preview"]))

    for title, content in sections:
        y -= 30
        if y < 150:
            _draw_footer(c, width, 1) # Simplified pagination
            c.showPage()
            _draw_header(c, width, height)
            y = height - 120

        c.setFillColor(colors.HexColor("#1e3d59"))
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, y, title)
        y -= 5
        c.setStrokeColor(colors.lightgrey)
        c.line(50, y, width - 50, y)
        y -= 20

        # Adjust content for code sections (use Monospace)
        font = "Courier" if "Similar" in title else "Helvetica"
        
        # Cleaner AI metrics if available
        if title == "AI Detection Explanation" and "metrics" in ai_result:
            metric_lines = []
            for m_name, m_info in ai_result["metrics"].items():
                m_val = m_info["value"]
                m_weight = m_info["weight"]
                metric_lines.append(f"• {m_name}: {round(m_val * 100, 1)}% (weight: {int(m_weight * 100)}%)")
            content = "\n".join(metric_lines)

        y = _draw_wrapped_text(c, 50, y, content, max_width=520, font_name=font, font_size=9)


    # Conclusion
    if y < 150:
        c.showPage()
        _draw_header(c, width, height)
        y = height - 120

    y -= 40
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Disclaimer & Conclusion")
    y -= 20
    conclusion = (
        "This report provides heuristic analysis of code patterns for plagiarism and AI authorship. "
        "The findings are based on structural, logical, and statistical models. "
        "A high similarity score is an indicator for review, not definitive proof of misconduct. "
        "Verified manual inspection is always recommended."
    )
    y = _draw_wrapped_text(c, 50, y, conclusion, max_width=500, font_size=10, fill_color=colors.grey)

    _draw_footer(c, width, 1)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()