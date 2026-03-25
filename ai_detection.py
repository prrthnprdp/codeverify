# ai_detection.py
# Rule-based AI-likelihood detection using heuristic indicators.
# Supports Python, C, and C++ code.
# Heuristics: indentation uniformity, comment density & phrasing,
# docstring/block-comment patterns, function length uniformity,
# repetitive structures, and line length regularity.
# Uses a sigmoid scoring curve for realistic output distribution.

import re
import math
from statistics import mean, stdev
from collections import Counter


def _sigmoid(x, midpoint=0.45, steepness=10):
    """Map a 0–1 raw score through a sigmoid curve centred at `midpoint`."""
    return 1 / (1 + math.exp(-steepness * (x - midpoint)))


# ---------------------------------------------------------------------------
# Language detection helper
# ---------------------------------------------------------------------------

def _detect_language(code: str) -> str:
    """Heuristically detect if code is Python, C, or C++."""
    if re.search(r'#include\s*[<"]', code):
        if re.search(r'\b(cout|cin|class|namespace|template|std::)\b', code):
            return "C++"
        return "C"
    if re.search(r'\bdef\s+\w+\s*\(', code) or re.search(r'^\s*import\s+\w+', code, re.MULTILINE):
        return "Python"
    # Default: guess from comment style
    if '//' in code or re.search(r'/\*', code):
        return "C"
    return "Python"


# ---------------------------------------------------------------------------
# Comment extraction helpers (multi-language)
# ---------------------------------------------------------------------------

def _get_comment_lines(lines: list, language: str) -> list:
    """Extract comment lines for the given language."""
    comments = []
    in_block = False
    for line in lines:
        s = line.strip()
        if language == "Python":
            if s.startswith("#"):
                comments.append(line)
        else:  # C / C++
            if in_block:
                comments.append(line)
                if "*/" in s:
                    in_block = False
            elif s.startswith("//"):
                comments.append(line)
            elif "/*" in s:
                in_block = True
                comments.append(line)
                if "*/" in s[s.index("/*") + 2:]:
                    in_block = False
    return comments


def _strip_comment_marker(comment: str, language: str) -> str:
    """Remove comment markers to get the text content."""
    s = comment.strip()
    if language == "Python":
        return s.lstrip("#").strip()
    s = re.sub(r'^//', '', s).strip()
    s = re.sub(r'^/\*+', '', s).strip()
    s = re.sub(r'\*+/$', '', s).strip()
    s = re.sub(r'^\*', '', s).strip()
    return s


# ---------------------------------------------------------------------------
# Individual heuristic components (each returns a float in 0–1)
# ---------------------------------------------------------------------------

def _indentation_uniformity(non_empty_lines):
    """Lower std-dev of leading whitespace → more uniform → higher score."""
    if len(non_empty_lines) < 2:
        return 0.5
    indent_lengths = [len(re.match(r"^\s*", l).group()) for l in non_empty_lines]
    std = stdev(indent_lengths)
    return max(0.0, min(1.0, 1 - (std / 6)))


def _comment_density(lines: list, language: str) -> float:
    """Higher ratio of comment lines → more likely AI-generated."""
    if not lines:
        return 0.0
    comment_lines = _get_comment_lines(lines, language)
    ratio = len(comment_lines) / len(lines)
    return max(0.0, min(1.0, ratio * 3.0))


def _repetitive_structures(lines: list, non_empty_lines: list, language: str) -> float:
    """High density of control-flow keywords in short code → AI pattern."""
    if not non_empty_lines:
        return 0.0
    if language == "Python":
        pattern = r'\b(for|while|if|elif|else|try|except|with|return)\b'
    else:
        pattern = r'\b(for|while|if|else|switch|case|do|return|break|continue)\b'
    count = sum(1 for l in lines if re.search(pattern, l))
    ratio = count / len(non_empty_lines)
    return max(0.0, min(1.0, ratio * 2.5))


def _line_length_regularity(non_empty_lines):
    """Lower coefficient of variation in line lengths → more uniform → AI."""
    if len(non_empty_lines) < 2:
        return 0.5
    lengths = [len(l) for l in non_empty_lines]
    avg = mean(lengths)
    if avg == 0:
        return 0.5
    cv = stdev(lengths) / avg
    return max(0.0, min(1.0, 1 - cv))


def _docstring_density(code: str, language: str) -> float:
    """Ratio of functions/methods that have a docstring/block comment."""
    lines = code.split("\n")

    if language == "Python":
        func_pattern = re.compile(r"^[ \t]*def\s+\w+\s*\(", re.MULTILINE)
        func_matches = list(func_pattern.finditer(code))
        if not func_matches:
            return 0.0
        func_line_nums = [code[:m.start()].count("\n") for m in func_matches]
        docstring_count = 0
        for fn_line in func_line_nums:
            for offset in range(1, 4):
                idx = fn_line + offset
                if idx >= len(lines):
                    break
                stripped = lines[idx].strip()
                if not stripped:
                    continue
                if stripped.startswith(('"""', "'''", 'r"""', "r'''")):
                    docstring_count += 1
                break
        return docstring_count / len(func_matches)

    else:  # C / C++
        # Match function definitions: return_type func_name(...) {
        func_pattern = re.compile(
            r'^\s*(?:(?:static|inline|extern|virtual|const)\s+)*'
            r'(?:void|int|float|double|char|long|short|bool|auto|[A-Za-z_]\w*)\s+'
            r'\w+\s*\([^)]*\)\s*\{',
            re.MULTILINE
        )
        func_matches = list(func_pattern.finditer(code))
        if not func_matches:
            return 0.0
        func_line_nums = [code[:m.start()].count("\n") for m in func_matches]
        docstring_count = 0
        for fn_line in func_line_nums:
            # Look backwards for a /** or /* comment immediately before the function
            for offset in range(1, 4):
                idx = fn_line - offset
                if idx < 0:
                    break
                stripped = lines[idx].strip()
                if not stripped:
                    continue
                if stripped.startswith('/*') or stripped.endswith('*/') or stripped.startswith('//'):
                    docstring_count += 1
                break
        return docstring_count / len(func_matches)


def _function_length_uniformity(code: str, language: str) -> float:
    """If function bodies are roughly the same length → AI-like consistency."""
    lines = code.split("\n")

    if language == "Python":
        func_pattern = re.compile(r"^([ \t]*)def\s+\w+\s*\(", re.MULTILINE)
        matches = list(func_pattern.finditer(code))
        if len(matches) < 2:
            return 0.0
        func_lengths = []
        for i, m in enumerate(matches):
            start_line = code[:m.start()].count("\n")
            end_line = code[:matches[i + 1].start()].count("\n") if i + 1 < len(matches) else len(lines)
            body_lines = sum(1 for ln in range(start_line + 1, min(end_line, len(lines))) if lines[ln].strip())
            func_lengths.append(max(body_lines, 1))
    else:  # C / C++
        # Find opening braces after function-like patterns
        func_pattern = re.compile(
            r'(?:void|int|float|double|char|long|short|bool|auto|[A-Za-z_]\w*)\s+\w+\s*\([^)]*\)\s*\{',
            re.MULTILINE
        )
        matches = list(func_pattern.finditer(code))
        if len(matches) < 2:
            return 0.0
        func_lengths = []
        for i, m in enumerate(matches):
            start_line = code[:m.start()].count("\n")
            end_line = code[:matches[i + 1].start()].count("\n") if i + 1 < len(matches) else len(lines)
            body_lines = sum(1 for ln in range(start_line + 1, min(end_line, len(lines))) if lines[ln].strip())
            func_lengths.append(max(body_lines, 1))

    if not func_lengths:
        return 0.0
    avg = mean(func_lengths)
    if avg == 0:
        return 0.0
    cv = stdev(func_lengths) / avg if len(func_lengths) > 1 else 0.0
    return max(0.0, min(1.0, 1 - (cv * 1.5)))


def _comment_phrasing_repetition(lines: list, language: str) -> float:
    """AI comments often start with similar verb phrases."""
    comment_lines = _get_comment_lines(lines, language)
    texts = [_strip_comment_marker(c, language) for c in comment_lines]
    texts = [t for t in texts if t]
    if len(texts) < 3:
        return 0.0

    prefixes = [t.split()[0].lower() for t in texts if t.split()]
    if not prefixes:
        return 0.0

    counts = Counter(prefixes)
    most_common_count = counts.most_common(1)[0][1]
    repetition_ratio = most_common_count / len(prefixes)

    ai_verbs = {
        "initialize", "create", "define", "check", "return", "set",
        "get", "update", "calculate", "compute", "process", "handle",
        "validate", "convert", "parse", "extract", "generate", "build",
        "format", "apply", "add", "remove", "find", "search", "load",
        "save", "display", "render", "configure", "setup", "ensure",
        "print", "read", "write", "open", "close", "allocate", "free",
        "increment", "decrement", "iterate", "loop", "traverse",
    }
    ai_verb_count = sum(1 for p in prefixes if p in ai_verbs)
    ai_verb_ratio = ai_verb_count / len(prefixes) if prefixes else 0

    combined = 0.5 * repetition_ratio + 0.5 * ai_verb_ratio
    return max(0.0, min(1.0, combined * 2.0))


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_ai_likelihood(code: str, language: str = None):
    """
    Compute AI-likelihood score using 7 heuristic indicators.
    Supports Python, C, and C++ code.
    If `language` is not supplied, it is auto-detected.

    Returns dict with 'score', 'explanation', 'suspicious', and 'metrics'.
    """
    if not language:
        language = _detect_language(code)

    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip()]

    if not non_empty:
        return {"score": 0, "explanation": "No code provided.", "suspicious": "", "metrics": {}}

    # --- Compute all components (0–1 each) ---
    indent_score   = _indentation_uniformity(non_empty)
    comment_score  = _comment_density(lines, language)
    repet_score    = _repetitive_structures(lines, non_empty, language)
    length_score   = _line_length_regularity(non_empty)
    docstr_score   = _docstring_density(code, language)
    func_uni_score = _function_length_uniformity(code, language)
    phrase_score   = _comment_phrasing_repetition(lines, language)

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
    comment_lines_full = _get_comment_lines(lines, language)
    suspicious_blocks = list(comment_lines_full[:5])
    if language == "Python":
        ctrl_pat = r"\b(for|while|if|elif|try|except)\b.*:"
    else:
        ctrl_pat = r"\b(for|while|if|switch)\b\s*\("
    for line in lines:
        if re.search(ctrl_pat, line):
            suspicious_blocks.append(line)
        if len(suspicious_blocks) >= 12:
            break
    suspicious = "\n".join(suspicious_blocks)

    # --- Detailed explanation ---
    detail_lines = [f"Detected language: {language}"]
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
        "metrics": {name: {"value": val, "weight": w} for name, (val, w) in weights.items()},
    }