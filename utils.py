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