# plagiarism.py
# Logical/statistical plagiarism detection using difflib, tokenize, ast, re, statistics.
# Ignores variable renaming and formatting changes via AST normalization and token filtering.
# Uses structural boosting and power curve for accurate similarity scoring.

import difflib
import tokenize
import io
import ast
import re
from statistics import mean


# --- Normalization helpers ---

def normalize_lines(code: str) -> list:
    """Remove comments and normalize whitespace per-line (preserving line structure)."""
    result = []
    for line in code.splitlines():
        # Remove inline comments
        cleaned = re.sub(r"#.*", "", line)
        # Normalize internal whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            result.append(cleaned)
    return result


def strip_comments_and_whitespace(code: str) -> str:
    """Remove comments and normalize whitespace (single string, for tokenization)."""
    lines = normalize_lines(code)
    return "\n".join(lines)


class NameNormalizer(ast.NodeTransformer):
    """AST transformer that replaces variable/function/class names with generic placeholders."""
    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id="VAR", ctx=node.ctx), node)

    def visit_arg(self, node):
        node.arg = "ARG"
        return node

    def visit_FunctionDef(self, node):
        node.name = "FUNC"
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        node.name = "FUNC"
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        node.name = "CLASS"
        self.generic_visit(node)
        return node


def ast_structure_signature(code: str) -> str:
    """Parse code to AST, normalize names, and return an ordered structural signature."""
    try:
        tree = ast.parse(code)
        normalizer = NameNormalizer()
        normalized_tree = normalizer.visit(tree)
        ast.fix_missing_locations(normalized_tree)
        # Preserve walk order (NOT sorted) to capture structural sequence
        node_types = [type(n).__name__ for n in ast.walk(normalized_tree)]
        return " ".join(node_types)
    except Exception:
        return ""


def tokenize_code_filtered(code: str):
    """Tokenize code and filter out formatting tokens."""
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            toknum, tokval = tok.type, tok.string
            if toknum in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL):
                continue
            if toknum == tokenize.NAME:
                tokens.append("IDENT")
            else:
                tokens.append(tokval)
    except Exception:
        pass
    return tokens


def similarity_ratio(a, b):
    """Compute difflib ratio between two sequences."""
    if not a and not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def compare_codes(code_a, code_b, language=None):
    """
    Compare two code snippets and return plagiarism metrics.
    Uses structural boosting for rename-only plagiarism and a power curve
    to amplify high-similarity results.
    """
    # --- Line-level similarity (per-line, not collapsed) ---
    lines_a = normalize_lines(code_a)
    lines_b = normalize_lines(code_b)
    line_sim = similarity_ratio(lines_a, lines_b)

    # --- Token-level similarity (identifiers normalized to IDENT) ---
    clean_a = strip_comments_and_whitespace(code_a)
    clean_b = strip_comments_and_whitespace(code_b)
    tokens_a = tokenize_code_filtered(clean_a)
    tokens_b = tokenize_code_filtered(clean_b)
    token_sim = similarity_ratio(tokens_a, tokens_b)

    # --- Structural similarity (AST with normalized names, ordered) ---
    struct_a = ast_structure_signature(code_a)
    struct_b = ast_structure_signature(code_b)
    struct_sim = similarity_ratio(struct_a, struct_b)

    # --- Weighted combination: structure-heavy to catch renames ---
    raw_score = 0.30 * line_sim + 0.35 * token_sim + 0.35 * struct_sim

    # --- Structural boost: if AST is near-identical but text differs,
    #     this is classic rename-only plagiarism → boost score ---
    if struct_sim > 0.85 and line_sim < 0.6:
        boost = 0.15 * (struct_sim - 0.85) / 0.15   # scales 0–0.15 as struct_sim goes 0.85→1.0
        raw_score = min(1.0, raw_score + boost)

    # --- Power curve to amplify high similarity ---
    curved_score = raw_score ** 0.85

    score = round(max(0, min(curved_score * 100, 100)), 2)

    # --- Diff preview ---
    diff_lines = []
    for d in difflib.unified_diff([l.rstrip() for l in code_a.splitlines()],
                                  [l.rstrip() for l in code_b.splitlines()],
                                  lineterm=""):
        if d.startswith("  "):
            diff_lines.append(d[2:])
        if len(diff_lines) >= 20:
            break
    diff_preview = "\n".join(diff_lines)

    # --- Explanation ---
    explanation = (
        f"- Line similarity: {round(line_sim * 100, 2)}%\n"
        f"- Token similarity (identifiers normalized): {round(token_sim * 100, 2)}%\n"
        f"- Structural similarity (AST normalized): {round(struct_sim * 100, 2)}%\n"
        f"- Structural boost applied: {'Yes' if struct_sim > 0.85 and line_sim < 0.6 else 'No'}\n"
        f"- Weights: 30% lines, 35% tokens, 35% structure\n"
        f"- Final score (after power curve): {score}%"
    )

    return {"score": score, "explanation": explanation, "diff_preview": diff_preview}


def token_similarity_ratio(tokens_a, tokens_b) -> float:
    """Compute difflib ratio between token sequences."""
    return difflib.SequenceMatcher(None, tokens_a, tokens_b).ratio()


def structural_similarity_ratio(sig_a: str, sig_b: str) -> float:
    """Compare AST structural signatures using difflib ratio."""
    return difflib.SequenceMatcher(None, sig_a, sig_b).ratio()


def compare_line_by_line(code_sources):
    """Produce a human-readable summary of line-by-line similarity across multiple sources."""
    summaries = []
    for i in range(len(code_sources)):
        for j in range(i + 1, len(code_sources)):
            name_i, code_i = code_sources[i]
            name_j, code_j = code_sources[j]
            lines_i = [l.rstrip() for l in code_i.splitlines()]
            lines_j = [l.rstrip() for l in code_j.splitlines()]
            diff = difflib.unified_diff(lines_i, lines_j, fromfile=name_i, tofile=name_j, lineterm="")
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
    """Compute plagiarism score using token and structural similarity."""
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
    diff_preview = difflib.ndiff([l.rstrip() for l in best_ref.splitlines()],
                                 [l.rstrip() for l in code.splitlines()])
    suspicious_lines = []
    for d in diff_preview:
        if d.startswith("  "):
            suspicious_lines.append(d[2:])
        if len(suspicious_lines) >= 20:
            break
    suspicious = "\n".join(suspicious_lines)

    explanation = (
        f"- Token similarity (identifier-normalized): {round(token_sim * 100, 2)}%\n"
        f"- Structural similarity (AST-normalized): {round(struct_sim * 100, 2)}%\n"
        f"- Method: difflib for sequence ratios, AST normalization to ignore renaming."
    )

    return {"score": score, "explanation": explanation, "suspicious": suspicious}
