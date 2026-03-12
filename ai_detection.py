import re
from statistics import mean, stdev

def analyze_ai_likelihood(code: str):
    """
    Compute AI-likelihood score using heuristic indicators:
    - Uniform indentation (low std dev suggests machine-like regularity)
    - Excessive commenting (high ratio may indicate generated explanations)
    - Repetitive structures (many for/while/if blocks in short code)
    - Average line length regularity
    Returns score, explanation, and suspicious snippet preview.
    """
    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip()]
    indent_lengths = [len(re.match(r"^\s*", line).group()) for line in non_empty]
    comment_lines = [line for line in lines if line.strip().startswith("#")]
    repetitive_patterns = sum(
        1 for line in lines if re.search(r"\b(for|while|if|elif|try|except)\b.*:", line)
    )
    avg_len = mean([len(l) for l in non_empty]) if non_empty else 0
    len_std = stdev([len(l) for l in non_empty]) if len(non_empty) > 1 else 0
    indent_std = stdev(indent_lengths) if len(indent_lengths) > 1 else 0
    comment_ratio = len(comment_lines) / len(lines) if lines else 0
    repetition_ratio = repetitive_patterns / max(len(non_empty), 1)

    indent_component = (1 - min(indent_std / 8, 1))
    comment_component = min(comment_ratio * 2, 1)
    repetition_component = min(repetition_ratio * 3, 1)
    length_reg_component = (1 - min(len_std / max(avg_len, 1), 1))

    raw_score = 100 * (0.35 * indent_component + 0.25 * comment_component + 0.25 * repetition_component + 0.15 * length_reg_component)
    score = round(max(0, min(raw_score, 100)), 2)

    suspicious_blocks = []
    suspicious_blocks.extend(comment_lines[:5])
    for line in lines:
        if re.search(r"\b(for|while|if|elif|try|except)\b.*:", line):
            suspicious_blocks.append(line)
        if len(suspicious_blocks) >= 12:
            break
    suspicious = "\n".join(suspicious_blocks)

    explanation = (
        f"- Indentation std dev: {round(indent_std, 2)} (lower suggests uniformity)\n"
        f"- Comment ratio: {round(comment_ratio * 100, 2)}%\n"
        f"- Repetitive structures count: {repetitive_patterns}\n"
        f"- Avg line length: {round(avg_len, 2)}, Length std dev: {round(len_std, 2)}\n"
        f"- Heuristics combine uniformity, density, and repetition to estimate AI-likelihood."
    )

    return {
        "score": score,
        "explanation": explanation,
        "suspicious": suspicious,
    }