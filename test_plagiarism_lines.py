from plagiarism import compare_codes

code1 = """def add(a, b):
    # This is a comment
    return a + b

def subtract(a, b):
    return a - b
"""

code2 = """def sum_nums(x, y):
    return x + y

def subtract(a, b):
    # Identical logic
    return a - b
"""

result = compare_codes(code1, code2)
print(f"Similarity Score: {result['score']}%")
print("\nSimilar Lines Detected:")
print(result['diff_preview'])
