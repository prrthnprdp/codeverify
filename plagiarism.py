import difflib
import re
import tokenize
import io
import ast

def normalize_whitespace(code):
    return re.sub(r'\s+', ' ', code.strip())

def strip_comments(code, language):
    if language == "Python":
        return re.sub(r'#.*', '', code)
    elif language in ["C", "C++"]:
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code
    return code

def tokenize_code(code, language):
    if language == "Python":
        try:
            tokens = []
            for tok in tokenize.generate_tokens(io.StringIO(code).readline):
                if tok.type == tokenize.NAME:
                    tokens.append("IDENT")
                elif tok.type not in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL):
                    tokens.append(tok.string)
            return tokens
        except Exception:
            return []
    elif language in ["C", "C++"]:
        code = strip_comments(code, language)
        code = normalize_whitespace(code)
        tokens = re.findall(r'\b(?:int|float|char|if|else|for|while|return|void|main|printf|scanf|struct|class|include|using|namespace|new|delete|cout|cin|std)\b|\W', code)
        return [t for t in tokens if t.strip()]
    return []

def extract_structure(code, language):
    if language == "Python":
        try:
            tree = ast.parse(code)
            node_types = [type(n).__name__ for n in ast.walk(tree)]
            return " ".join(sorted(node_types))
        except Exception:
            return ""
    elif language in ["C", "C++"]:
        patterns = [
            r'\bfor\s*\(.*?\)', r'\bwhile\s*\(.*?\)', r'\bif\s*\(.*?\)', r'\bswitch\s*\(.*?\)',
            r'\bstruct\b', r'\bclass\b', r'\breturn\b', r'\bmain\s*\(.*?\)', r'\binclude\b'
        ]
        structure = []
        for pattern in patterns:
            matches = re.findall(pattern, code)
            structure.extend([pattern] * len(matches))
        return " ".join(structure)
    return ""

def similarity_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def compare_codes(code_a, code_b, language):
    code_a_clean = strip_comments(code_a, language)
    code_b_clean = strip_comments(code_b, language)

    lines_a = [l.strip() for l in code_a_clean.splitlines() if l.strip()]
    lines_b = [l.strip() for l in code_b_clean.splitlines() if l.strip()]
    line_sim = similarity_ratio(lines_a, lines_b)

    tokens_a = tokenize_code(code_a, language)
    tokens_b = tokenize_code(code_b, language)
    token_sim = similarity_ratio(tokens_a, tokens_b)

    struct_a = extract_structure(code_a, language)
    struct_b = extract_structure(code_b, language)
    struct_sim = similarity_ratio(struct_a, struct_b)


    score = round(100 * (0.4 * line_sim + 0.4 * token_sim + 0.2 * struct_sim), 2)


def token_similarity_ratio(tokens_a, tokens_b) -> float:
    """Compute difflib ratio between token sequences."""
    return difflib.SequenceMatcher(None, tokens_a, tokens_b).ratio()

def structural_similarity_ratio(sig_a: str, sig_b: str) -> float:
    """Compare AST structural signatures using difflib ratio."""
    return difflib.SequenceMatcher(None, sig_a, sig_b).ratio()

def compare_line_by_line(code_sources):
    """
    Produce a human-readable summary of line-by-line similarity across multiple sources.
    Uses difflib unified diff to highlight overlaps while ignoring trivial whitespace.
    """
    summaries = []
    for i in range(len(code_sources)):
        for j in range(i + 1, len(code_sources)):
            name_i, code_i = code_sources[i]
            name_j, code_j = code_sources[j]
            lines_i = [l.rstrip() for l in code_i.splitlines()]
            lines_j = [l.rstrip() for l in code_j.splitlines()]
            diff = difflib.unified_diff(lines_i, lines_j, fromfile=name_i, tofile=name_j, lineterm="")
            # Keep only a short preview to avoid overwhelming UI
            preview = []
            count = 0
            for d in diff:
                preview.append(d)
                count += 1
                if count >= 80:
                    preview.append("... (diff truncated)")
                    break
            summaries.append("\n".join(preview))
    return "\n\n".join(summaries)

def analyze_plagiarism(code: str):
    """
    Compute plagiarism score using:
    - Token similarity (with identifier normalization)
    - AST structural similarity (with name normalization)
    - Line-by-line comparison (exposed via compare_line_by_line in app)
    Returns score, explanation, and suspicious snippet preview.
    """

    normalized = strip_comments_and_whitespace(code)

    tokens = tokenize_code_filtered(normalized)

    struct_sig = ast_structure_signature(code)

    
    reference_snippets = [
        "def add(a, b): return a + b",
        "class Example:\n    def method(self, x):\n        for i in range(x):\n            print(i)",
        "def factorial(n):\n    return 1 if n<=1 else n*factorial(n-1)",
    ]

    token_ratios = []
    struct_ratios = []
    for ref in reference_snippets:
        ref_tokens = tokenize_code_filtered(strip_comments_and_whitespace(ref))
        ref_sig = ast_structure_signature(ref)
        token_ratios.append(token_similarity_ratio(tokens, ref_tokens))
        struct_ratios.append(structural_similarity_ratio(struct_sig, ref_sig))

    
    token_sim = max(token_ratios) if token_ratios else 0.0
    struct_sim = max(struct_ratios) if struct_ratios else 0.0

    
    score = round(100 * (0.6 * token_sim + 0.4 * struct_sim), 2)

    
    best_ref_idx = 0
    if token_ratios:
        best_ref_idx = max(range(len(reference_snippets)), key=lambda i: (0.6 * token_ratios[i] + 0.4 * struct_ratios[i]))
    best_ref = reference_snippets[best_ref_idx]
    diff_preview = difflib.ndiff(
        [l.rstrip() for l in best_ref.splitlines()],
        [l.rstrip() for l in code.splitlines()],
    )
    suspicious_lines = []
    for d in diff_preview:
        # Lines starting with '  ' are common; '+' or '-' indicate differences
        if d.startswith("  "):
            suspicious_lines.append(d[2:])
        if len(suspicious_lines) >= 20:
            break
    suspicious = "\n".join(suspicious_lines)


    explanation = (
        f"- Line similarity: {round(line_sim * 100, 2)}%\n"
        f"- Token similarity: {round(token_sim * 100, 2)}%\n"
        f"- Structural similarity: {round(struct_sim * 100, 2)}%\n"
        f"- Weighted score: 40% lines + 40% tokens + 20% structure"
    )

    diff = difflib.unified_diff(lines_a, lines_b, lineterm="")
    preview = "\n".join(list(diff)[:30])

    return {
        "score": score,
        "explanation": explanation,
        "diff_preview": preview
    }