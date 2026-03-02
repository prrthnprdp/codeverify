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