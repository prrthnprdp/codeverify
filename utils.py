# utils.py
# Utility helpers for safe file loading and preview formatting.

def load_code_from_file(uploaded_file):
    """Safely read uploaded file content as UTF-8 text."""
    try:
        data = uploaded_file.read()
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        return str(data)
    except Exception:
        return ""

def safe_preview(*sections, max_chars=2000):
    """
    Concatenate sections and limit preview length to avoid UI overload.
    """
    combined = "\n\n".join([s for s in sections if s])
    if len(combined) > max_chars:
        return combined[:max_chars] + "\n... (preview truncated)"
    return combined

def load_code_from_file(uploaded_file):
    try:
        data = uploaded_file.read()
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        return str(data)
    except Exception:
        return ""

def detect_language(filename):
    if filename.endswith(".py"):
        return "Python"
    elif filename.endswith(".c"):
        return "C"
    elif filename.endswith(".cpp"):
        return "C++"
    return "Unknown"
