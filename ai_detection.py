# ai_detection.py
# Rule-based AI-likelihood detection using heuristic indicators:
# indentation uniformity, comment density & phrasing, docstring patterns,
# function length uniformity, repetitive structures, and line length regularity.
# Uses a sigmoid scoring curve for realistic output distribution.

import re
import math
from statistics import mean, stdev
from collections import Counter


def _sigmoid(x, midpoint=0.45, steepness=10):
    """Map a 0–1 raw score through a sigmoid curve centred at `midpoint`."""
    return 1 / (1 + math.exp(-steepness * (x - midpoint)))


# ---------------------------------------------------------------------------
# Individual heuristic components (each returns a float in 0–1)
# ---------------------------------------------------------------------------

def _indentation_uniformity(non_empty_lines):
    """Lower std-dev of leading whitespace → more uniform → higher score."""
    if len(non_empty_lines) < 2:
        return 0.5
    indent_lengths = [len(re.match(r"^\s*", l).group()) for l in non_empty_lines]
    std = stdev(indent_lengths)
    # Tight threshold: std < 2 is very uniform (AI-like), std > 6 is messy
    return max(0.0, min(1.0, 1 - (std / 6)))


def _comment_density(lines):
    """Higher ratio of comment lines → more likely AI-generated."""
    if not lines:
        return 0.0
    comment_lines = [l for l in lines if l.strip().startswith("#")]
    ratio = len(comment_lines) / len(lines)
    # AI code typically has 15-40% comments; scale so 20% → ~0.7, 40%+ → 1.0
    return max(0.0, min(1.0, ratio * 3.0))


def _repetitive_structures(lines, non_empty_lines):
    """High density of control-flow keywords in short code → AI pattern."""
    if not non_empty_lines:
        return 0.0
    count = sum(
        1 for l in lines
        if re.search(r"\b(for|while|if|elif|else|try|except|with|return)\b", l)
    )
    ratio = count / len(non_empty_lines)
    # AI code is often 25-50% control flow; scale so 30% → ~0.7
    return max(0.0, min(1.0, ratio * 2.5))


def _line_length_regularity(non_empty_lines):
    """Lower coefficient of variation in line lengths → more uniform → AI."""
    if len(non_empty_lines) < 2:
        return 0.5
    lengths = [len(l) for l in non_empty_lines]
    avg = mean(lengths)
    if avg == 0:
        return 0.5
    cv = stdev(lengths) / avg          # coefficient of variation
    # AI code: cv ~ 0.3-0.5 ; human code: cv ~ 0.6-1.2
    return max(0.0, min(1.0, 1 - cv))


def _docstring_density(code):
    """Ratio of functions/methods that have a docstring → AI almost always adds them."""
    # Find all function definitions
    func_pattern = re.compile(r"^[ \t]*def\s+\w+\s*\(", re.MULTILINE)
    func_matches = list(func_pattern.finditer(code))
    if not func_matches:
        return 0.0     # no functions → neutral

    lines = code.split("\n")
    func_line_nums = []
    for m in func_matches:
        line_num = code[:m.start()].count("\n")
        func_line_nums.append(line_num)

    docstring_count = 0
    for fn_line in func_line_nums:
        # Look at the next 1-3 non-empty lines after the def for a docstring
        for offset in range(1, 4):
            idx = fn_line + offset
            if idx >= len(lines):
                break
            stripped = lines[idx].strip()
            if not stripped:
                continue
            if stripped.startswith(('"""', "'''", 'r"""', "r'''")):
                docstring_count += 1
            break   # only check the first non-empty line after def

    ratio = docstring_count / len(func_matches)
    # AI code: nearly always has docstrings (ratio ~0.8-1.0)
    return ratio


def _function_length_uniformity(code):
    """If function bodies are roughly the same length → AI-like consistency."""
    # Split code at function definitions
    func_pattern = re.compile(r"^([ \t]*)def\s+\w+\s*\(", re.MULTILINE)
    matches = list(func_pattern.finditer(code))

    if len(matches) < 2:
        return 0.0     # need at least 2 functions to compare

    lines = code.split("\n")
    func_lengths = []

    for i, m in enumerate(matches):
        start_line = code[:m.start()].count("\n")
        func_indent = len(m.group(1))

        if i + 1 < len(matches):
            end_line = code[:matches[i + 1].start()].count("\n")
        else:
            end_line = len(lines)

        # Count non-empty body lines
        body_lines = 0
        for ln in range(start_line + 1, min(end_line, len(lines))):
            stripped = lines[ln].strip()
            if stripped:
                body_lines += 1
        func_lengths.append(max(body_lines, 1))

    avg = mean(func_lengths)
    if avg == 0:
        return 0.0
    cv = stdev(func_lengths) / avg     # coefficient of variation
    # AI functions tend to be same-ish length (cv < 0.3), human: cv > 0.6
    return max(0.0, min(1.0, 1 - (cv * 1.5)))


def _comment_phrasing_repetition(lines):
    """AI comments often start with similar verb phrases ('Initialize', 'Check if', etc.)."""
    comment_lines = [l.strip().lstrip("#").strip() for l in lines if l.strip().startswith("#")]
    if len(comment_lines) < 3:
        return 0.0

    # Extract leading 2-word phrases
    prefixes = []
    for c in comment_lines:
        words = c.split()
        if len(words) >= 2:
            prefixes.append(words[0].lower())

    if not prefixes:
        return 0.0

    counts = Counter(prefixes)
    most_common_count = counts.most_common(1)[0][1]
    repetition_ratio = most_common_count / len(prefixes)

    # Also check for AI-typical verbs
    ai_verbs = {"initialize", "create", "define", "check", "return", "set",
                "get", "update", "calculate", "compute", "process", "handle",
                "validate", "convert", "parse", "extract", "generate", "build",
                "format", "apply", "add", "remove", "find", "search", "load",
                "save", "display", "render", "configure", "setup", "ensure"}
    ai_verb_count = sum(1 for p in prefixes if p in ai_verbs)
    ai_verb_ratio = ai_verb_count / len(prefixes) if prefixes else 0

    combined = 0.5 * repetition_ratio + 0.5 * ai_verb_ratio
    return max(0.0, min(1.0, combined * 2.0))


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_ai_likelihood(code: str):
    """
    Compute AI-likelihood score using 7 heuristic indicators, each normalized
    to 0–1, weighted, and passed through a sigmoid curve for realistic output.

    Returns dict with 'score', 'explanation', and 'suspicious' preview.
    """
    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip()]

    if not non_empty:
        return {"score": 0, "explanation": "No code provided.", "suspicious": ""}

    # --- Compute all components (0–1 each) ---
    indent_score   = _indentation_uniformity(non_empty)
    comment_score  = _comment_density(lines)
    repet_score    = _repetitive_structures(lines, non_empty)
    length_score   = _line_length_regularity(non_empty)
    docstr_score   = _docstring_density(code)
    func_uni_score = _function_length_uniformity(code)
    phrase_score   = _comment_phrasing_repetition(lines)

    # --- Weighted combination ---
    weights = {
        "Indentation uniformity":     (indent_score,   0.15),
        "Comment density":            (comment_score,   0.10),
        "Repetitive structures":      (repet_score,     0.10),
        "Line length regularity":     (length_score,    0.10),
        "Docstring density":          (docstr_score,    0.20),
        "Function length uniformity": (func_uni_score,  0.20),
        "Comment phrasing patterns":  (phrase_score,    0.15),
    }

    raw = sum(val * w for val, w in weights.values())

    # --- Sigmoid curve to map into realistic range ---
    curved = _sigmoid(raw, midpoint=0.40, steepness=10)
    score = round(max(0, min(curved * 100, 100)), 2)

    # --- Suspicious preview ---
    suspicious_blocks = []
    comment_lines_full = [l for l in lines if l.strip().startswith("#")]
    suspicious_blocks.extend(comment_lines_full[:5])
    for line in lines:
        if re.search(r"\b(for|while|if|elif|try|except)\b.*:", line):
            suspicious_blocks.append(line)
        if len(suspicious_blocks) >= 12:
            break
    suspicious = "\n".join(suspicious_blocks)

    # --- Detailed explanation ---
    detail_lines = []
    for name, (val, w) in weights.items():
        bar = "#" * int(val * 10) + "-" * (10 - int(val * 10))
        detail_lines.append(f"- {name}: {round(val * 100, 1)}% [{bar}]  (weight: {int(w*100)}%)")
    detail_lines.append(f"- Raw weighted score: {round(raw * 100, 1)}%")
    detail_lines.append(f"- After sigmoid curve: {score}%")
    explanation = "\n".join(detail_lines)

    return {
        "score": score,
        "explanation": explanation,
        "suspicious": suspicious,
    }