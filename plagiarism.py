# plagiarism.py
# Logical/statistical plagiarism detection using difflib, tokenize, ast, re, statistics.
# Ignores variable renaming and formatting changes via AST normalization and token filtering.

import difflib
import tokenize
import io
import ast
import re
from statistics import mean

# --- Normalization helpers ---

def strip_comments_and_whitespace(code: str) -> str:
    """Remove comments and normalize whitespace to reduce formatting influence."""
    # Remove inline comments
    code_no_comments = re.sub(r"#.*", "", code)
    # Normalize whitespace
    code_norm = re.sub(r"\s+", " ", code_no_comments)
    return code_norm.strip()

class NameNormalizer(ast.NodeTransformer):
    """
    AST transformer that replaces variable/function/class names with generic placeholders.
    This helps ignore variable renaming during structural comparison.
    """
    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id="VAR", ctx=node.ctx), node)

    def visit_arg(self, node):
        node.arg = "ARG"
        return node

    def visit_FunctionDef(self, node):
        node.name = "FUNC"
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        node.name = "CLASS"
        self.generic_visit(node)
        return node

def ast_structure_signature(code: str) -> str:
    """
    Parse code to AST, normalize names, and return a structural signature string.
    If parsing fails, return an empty signature.
    """
    try:
        tree = ast.parse(code)
        normalizer = NameNormalizer()
        normalized_tree = normalizer.visit(tree)
        ast.fix_missing_locations(normalized_tree)
        # Signature: sequence of node types
        node_types = [type(n).__name__ for n in ast.walk(normalized_tree)]
        return " ".join(sorted(node_types))
    except Exception:
        return ""

# --- Tokenization helpers ---

def tokenize_code_filtered(code: str):
    """
    Tokenize code and filter out formatting tokens.
    Replace identifiers with a generic token to reduce renaming impact.
    """
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            toknum, tokval = tok.type, tok.string
            if toknum in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL):
                continue
            # Replace identifiers with a placeholder
            if toknum == tokenize.NAME:
                tokens.append("IDENT")
            else:
                tokens.append(tokval)
    except Exception:
        pass
    return tokens

# --- Core analysis ---

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
    # Normalize formatting and comments
    normalized = strip_comments_and_whitespace(code)

    # Tokenization with identifier normalizationdir
    tokens = tokenize_code_filtered(normalized)

    # AST structural signature with name normalization
    struct_sig = ast_structure_signature(code)

    # Reference corpus (simple baseline to avoid external data)
    # In academic use, this can be replaced with instructor-provided references offline.
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

    # Aggregate similarity
    token_sim = max(token_ratios) if token_ratios else 0.0
    struct_sim = max(struct_ratios) if struct_ratios else 0.0

    # Weighted score: emphasize tokens but include structure
    score = round(100 * (0.6 * token_sim + 0.4 * struct_sim), 2)

    # Suspicious preview: show top overlapping lines via difflib against best reference
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
        f"- Token similarity (identifier-normalized): {round(token_sim * 100, 2)}%\n"
        f"- Structural similarity (AST-normalized): {round(struct_sim * 100, 2)}%\n"
        f"- Method: difflib for sequence ratios, AST normalization to ignore renaming, token filtering to reduce formatting impact."
    )

    return {
        "score": score,
        "explanation": explanation,
        "suspicious": suspicious,
    }