import re
from statistics import mean, stdev

def analyze_ai_likelihood(code: str):

    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip()]

    # ---------- Indentation Analysis ----------
    indent_lengths = [len(re.match(r"^\s*", line).group()) for line in non_empty]
    indent_std = stdev(indent_lengths) if len(indent_lengths) > 1 else 0

    # ---------- Comment Detection ----------
    comment_lines = []
    in_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#") or stripped.startswith("//"):
            comment_lines.append(line)

        if "/*" in stripped:
            in_block = True
            comment_lines.append(line)

        elif "*/" in stripped:
            in_block = False
            comment_lines.append(line)

        elif in_block:
            comment_lines.append(line)

    comment_ratio = len(comment_lines) / max(len(lines), 1)

    # ---------- Control Structure Detection ----------
    control_pattern = r"\b(for|while|if|elif|else|switch|case|try|except)\b"
    control_count = sum(1 for line in lines if re.search(control_pattern, line))
    repetition_ratio = control_count / max(len(non_empty), 1)

    # ---------- Line Length Analysis ----------
    lengths = [len(l) for l in non_empty]
    avg_len = mean(lengths) if lengths else 0
    len_std = stdev(lengths) if len(lengths) > 1 else 0

    # ---------- Identifier Entropy ----------
    keywords = {
        "for","while","if","else","elif","switch","case","try","except",
        "return","int","float","char","void","include","print"
    }

    identifiers = [
        word for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code)
        if word not in keywords
    ]

    unique_ids = set(identifiers)
    entropy = len(unique_ids) / max(len(identifiers), 1)

    # ---------- Components ----------
    indent_component = 1 - min(indent_std / 8, 1)
    comment_component = min(comment_ratio * 2, 1)
    repetition_component = min(repetition_ratio * 2, 1)
    length_component = 1 - min(len_std / max(avg_len, 1), 1)
    entropy_component = 1 - entropy

    # ---------- Final Score ----------
    raw_score = 100 * (
        0.2 * indent_component +
        0.2 * comment_component +
        0.2 * repetition_component +
        0.2 * length_component +
        0.2 * entropy_component
    )

    score = round(max(0, min(raw_score, 100)), 2)

    # ---------- Suspicious Snippets ----------
    suspicious_lines = []

    for line in lines:
        if re.search(control_pattern, line) or line in comment_lines:
            suspicious_lines.append(line)

        if len(suspicious_lines) >= 10:
            break

    suspicious = "\n".join(suspicious_lines)

    explanation = (
        f"Indentation variation: {round(indent_std,2)}\n"
        f"Comment ratio: {round(comment_ratio*100,2)}%\n"
        f"Control structures: {control_count}\n"
        f"Average line length: {round(avg_len,2)}\n"
        f"Identifier entropy: {round(entropy,2)}"
    )

    return {
        "score": score,
        "explanation": explanation,
        "suspicious": suspicious
    }