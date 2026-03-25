# plagiarism.py
# Multi-language plagiarism detection (Python, C, C++).
# Uses line, token, and structural similarity with proper language-aware parsing.
# Identical code always returns 100%. Variable renaming is detected via normalization.

import difflib
import tokenize
import io
import ast
import re
from statistics import mean


# ---------------------------------------------------------------------------
# Comment stripping helpers
# ---------------------------------------------------------------------------

def strip_comments(code: str, language: str) -> str:
    """Remove comments for the given language."""
    if language == "Python":
        # Remove Python # comments
        code = re.sub(r'#[^\n]*', '', code)
    elif language in ("C", "C++"):
        # Remove // line comments
        code = re.sub(r'//[^\n]*', '', code)
        # Remove /* ... */ block comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    return code


def normalize_whitespace(code: str) -> str:
    """Collapse whitespace."""
    return re.sub(r'\s+', ' ', code.strip())


# ---------------------------------------------------------------------------
# Line normalisation
# ---------------------------------------------------------------------------

def normalize_lines(code: str, language: str = "Python") -> list:
    """Remove comments and normalise whitespace, return non-empty lines."""
    stripped = strip_comments(code, language)
    result = []
    for line in stripped.splitlines():
        cleaned = re.sub(r'\s+', ' ', line).strip()
        if cleaned:
            result.append(cleaned)
    return result


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def tokenize_python(code: str) -> list:
    """Tokenize Python code, normalising identifiers to IDENT."""
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            toknum, tokval = tok.type, tok.string
            if toknum in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.COMMENT):
                continue
            if toknum == tokenize.NAME:
                tokens.append("IDENT")
            else:
                tokens.append(tokval)
    except Exception:
        pass
    return tokens


_C_KEYWORDS = re.compile(
    r'\b(int|float|double|char|long|short|unsigned|void|struct|union|enum|typedef|'
    r'if|else|for|while|do|switch|case|break|continue|return|goto|'
    r'class|public|private|protected|new|delete|this|namespace|using|template|'
    r'include|define|main|printf|scanf|cout|cin|std|endl)\b'
)


def tokenize_c(code: str) -> list:
    """Tokenize C/C++ code using regex; normalise identifiers to IDENT."""
    tokens = []
    # Simple lexer: keywords kept, identifiers normalised, operators/punct kept
    pattern = re.compile(
        r'(//[^\n]*|/\*.*?\*/|'        # comments (strip)
        r'"(?:[^"\\]|\\.)*"|'          # string literals
        r"'(?:[^'\\]|\\.)*'|"          # char literals
        r'\b\d+\b|'                    # numbers – keep as-is
        r'[a-zA-Z_]\w*|'              # identifiers / keywords
        r'[{}()\[\];,.<>!&|^~%+\-*/=]+)',  # operators/punctuation
        re.DOTALL
    )
    for m in pattern.finditer(code):
        tok = m.group(0)
        if tok.startswith('//') or tok.startswith('/*'):
            continue  # skip comments
        if _C_KEYWORDS.fullmatch(tok):
            tokens.append(tok)           # keep keywords as structural markers
        elif re.fullmatch(r'[a-zA-Z_]\w*', tok):
            tokens.append('IDENT')       # normalise identifiers
        else:
            tokens.append(tok)
    return tokens


def tokenize_code(code: str, language: str) -> list:
    """Dispatch to language-appropriate tokenizer."""
    clean = strip_comments(code, language)
    if language == "Python":
        return tokenize_python(clean)
    elif language in ("C", "C++"):
        return tokenize_c(clean)
    return tokenize_python(clean)


# ---------------------------------------------------------------------------
# Structural signatures
# ---------------------------------------------------------------------------

class NameNormalizer(ast.NodeTransformer):
    """Replace Python AST names with generic placeholders."""
    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id="VAR", ctx=node.ctx), node)
    def visit_arg(self, node):
        node.arg = "ARG"; return node
    def visit_FunctionDef(self, node):
        node.name = "FUNC"; self.generic_visit(node); return node
    def visit_AsyncFunctionDef(self, node):
        node.name = "FUNC"; self.generic_visit(node); return node
    def visit_ClassDef(self, node):
        node.name = "CLASS"; self.generic_visit(node); return node


def ast_structure_signature(code: str) -> str:
    """Python AST structural signature (ordered node types)."""
    try:
        tree = ast.parse(code)
        normalizer = NameNormalizer()
        normalized_tree = normalizer.visit(tree)
        ast.fix_missing_locations(normalized_tree)
        node_types = [type(n).__name__ for n in ast.walk(normalized_tree)]
        return " ".join(node_types)
    except Exception:
        return ""


def c_structure_signature(code: str) -> str:
    """C/C++ structural signature based on control-flow patterns."""
    patterns = [
        r'\bfor\s*\(',
        r'\bwhile\s*\(',
        r'\bdo\s*\{',
        r'\bif\s*\(',
        r'\belse\b',
        r'\bswitch\s*\(',
        r'\bstruct\b',
        r'\bclass\b',
        r'\breturn\b',
        r'\bmain\s*\(',
        r'#\s*include\b',
        r'\bprintf\s*\(',
        r'\bscanf\s*\(',
        r'\bcout\b',
        r'\bcin\b',
    ]
    structure = []
    for pat in patterns:
        count = len(re.findall(pat, code))
        if count:
            structure.extend([pat] * count)
    return " ".join(structure)


def extract_structure(code: str, language: str) -> str:
    if language == "Python":
        return ast_structure_signature(code)
    elif language in ("C", "C++"):
        return c_structure_signature(code)
    return ast_structure_signature(code)


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------

def similarity_ratio(a, b) -> float:
    """Compute difflib ratio between two sequences.
    Returns 1.0 if both are empty (identical empty inputs),
    0.0 if one is empty while the other is not.
    """
    if not a and not b:
        return 1.0   # both empty → identical
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------------------
# Main compare function
# ---------------------------------------------------------------------------

def compare_codes(code_a: str, code_b: str, language: str = "Python") -> dict:
    """
    Compare two code snippets and return plagiarism metrics.
    Supports Python, C, and C++.
    Identical code always returns 100%.
    """
    # --- Line-level similarity ---
    lines_a = normalize_lines(code_a, language)
    lines_b = normalize_lines(code_b, language)
    line_sim = similarity_ratio(lines_a, lines_b)

    # --- Token-level similarity ---
    tokens_a = tokenize_code(code_a, language)
    tokens_b = tokenize_code(code_b, language)
    token_sim = similarity_ratio(tokens_a, tokens_b)

    # --- Structural similarity ---
    struct_a = extract_structure(code_a, language)
    struct_b = extract_structure(code_b, language)
    struct_sim = similarity_ratio(struct_a.split(), struct_b.split())

    # --- Weighted combination ---
    raw_score = 0.35 * line_sim + 0.40 * token_sim + 0.25 * struct_sim

    # --- Structural boost: near-identical structure but text differs (rename-only) ---
    if struct_sim > 0.85 and line_sim < 0.6:
        boost = 0.15 * (struct_sim - 0.85) / 0.15
        raw_score = min(1.0, raw_score + boost)

    # --- Power curve to amplify high-similarity ---
    curved_score = raw_score ** 0.85
    score = round(max(0, min(curved_score * 100, 100)), 2)

    # --- Similar Lines Preview ---
    raw_lines_a = code_a.splitlines()
    raw_lines_b = code_b.splitlines()

    def clean_line(l):
        c = strip_comments(l, language)
        return re.sub(r'\s+', ' ', c).strip()

    norm_a = [clean_line(l) for l in raw_lines_a]
    norm_b = [clean_line(l) for l in raw_lines_b]

    matcher = difflib.SequenceMatcher(None, norm_a, norm_b)
    matches = []
    for a, b, size in matcher.get_matching_blocks():
        for i in range(size):
            if a + i < len(norm_a) and b + i < len(norm_b) and norm_a[a + i]:
                matches.append(f"Line {b + i + 1}: {raw_lines_b[b + i].strip()}")

    diff_preview = "\n".join(matches[:30])
    if len(matches) > 30:
        diff_preview += f"\n... and {len(matches) - 30} more similar lines."

    # --- Explanation ---
    explanation = (
        f"- Line similarity: {round(line_sim * 100, 2)}%\n"
        f"- Token similarity (identifiers normalized): {round(token_sim * 100, 2)}%\n"
        f"- Structural similarity: {round(struct_sim * 100, 2)}%\n"
        f"- Structural boost applied: {'Yes' if struct_sim > 0.85 and line_sim < 0.6 else 'No'}\n"
        f"- Weights: 35% lines, 40% tokens, 25% structure\n"
        f"- Final score (after power curve): {score}%"
    )

    return {"score": score, "explanation": explanation, "diff_preview": diff_preview}


# ---------------------------------------------------------------------------
# compare_line_by_line (multi-file summary)
# ---------------------------------------------------------------------------

def compare_line_by_line(code_sources):
    """Produce a human-readable unified diff across multiple source pairs."""
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
