from pdf_report import generate_pdf_report_bytes

code_sources = [("original.py", "def add(a, b): return a + b"), ("suspected.py", "def sum(x, y): return x + y")]
combined_code = "def add(a, b): return a + b\ndef sum(x, y): return x + y"
plagiarism_result = {
    "score": 85.0,
    "explanation": "High similarity detected in function structure and logic.",
    "diff_preview": "Line 1: def sum(x, y):\nLine 2:     return x + y"
}
ai_result = {
    "score": 75.66,
    "explanation": "High likelihood of AI generation.",
    "metrics": {
        "Indentation uniformity": {"value": 0.513, "weight": 0.15},
        "Comment density": {"value": 0.0, "weight": 0.10},
        "Repetitive structures": {"value": 0.573, "weight": 0.10},
        "Line length regularity": {"value": 0.332, "weight": 0.10},
        "Docstring density": {"value": 1.0, "weight": 0.20},
        "Function length uniformity": {"value": 0.73, "weight": 0.20},
        "Comment phrasing patterns": {"value": 0.0, "weight": 0.15}
    }
}

pdf_bytes = generate_pdf_report_bytes(code_sources, combined_code, plagiarism_result, ai_result)
with open("test_report_cleaned_ai.pdf", "wb") as f:
    f.write(pdf_bytes)

print("Test PDF report generated: test_report_cleaned_ai.pdf")
