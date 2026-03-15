"""
Test script for CodeVerify scoring accuracy.
Validates AI detection and plagiarism scoring with known code samples.
"""

import sys
sys.path.insert(0, ".")

from ai_detection import analyze_ai_likelihood
from plagiarism import compare_codes

# ============================================================
# AI DETECTION TESTS
# ============================================================

# --- Typical AI-generated code (docstrings, uniform style, comments) ---
AI_CODE = '''
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number using dynamic programming."""
    if n <= 0:
        return 0
    if n == 1:
        return 1

    # Initialize the base cases
    prev, curr = 0, 1

    # Iterate through the sequence
    for i in range(2, n + 1):
        prev, curr = curr, prev + curr

    return curr


def is_prime(n):
    """Check if a number is prime."""
    if n < 2:
        return False

    # Check for divisibility
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False

    return True


def merge_sort(arr):
    """Sort an array using the merge sort algorithm."""
    if len(arr) <= 1:
        return arr

    # Find the middle point
    mid = len(arr) // 2

    # Recursively sort both halves
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    # Merge the sorted halves
    return merge(left, right)


def merge(left, right):
    """Merge two sorted arrays into a single sorted array."""
    result = []
    i = j = 0

    # Compare elements from both arrays
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # Add remaining elements
    result.extend(left[i:])
    result.extend(right[j:])

    return result
'''

# --- Minimal human code (no comments, irregular style) ---
HUMAN_CODE = '''
def fib(n):
    a,b=0,1
    for _ in range(n): a,b=b,a+b
    return a

def chk(x):
  if x<2: return False
  i=2
  while i*i<=x:
      if x%i==0:
        return False
      i+=1
  return True

stuff = [fib(i) for i in range(20) if chk(fib(i))]
print(stuff)
x = {k:v for k,v in enumerate(stuff)}
'''

# ============================================================
# PLAGIARISM TESTS
# ============================================================

# --- Original code ---
ORIGINAL = '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
'''

# --- Same logic, renamed variables ---
RENAMED = '''
def sort_list(data):
    size = len(data)
    for x in range(size):
        for y in range(0, size-x-1):
            if data[y] > data[y+1]:
                data[y], data[y+1] = data[y+1], data[y]
    return data
'''

# --- Completely different code ---
DIFFERENT = '''
import os
import json

config = {}
with open("settings.json") as f:
    config = json.load(f)

for key, value in config.items():
    os.environ[key] = str(value)
    print(f"Set {key} = {value}")
'''


def run_tests():
    print("=" * 60)
    print("  CodeVerify Scoring Tests")
    print("=" * 60)

    passed = 0
    failed = 0

    # --- AI Detection ---
    print("\n--- AI DETECTION ---\n")

    ai_result = analyze_ai_likelihood(AI_CODE)
    ai_score = ai_result["score"]
    print(f"AI-generated code score: {ai_score}%")
    print(f"  Explanation:\n{ai_result['explanation']}")
    if ai_score >= 65:
        print("  ✅ PASS (expected >= 65%)")
        passed += 1
    else:
        print(f"  ❌ FAIL (expected >= 65%, got {ai_score}%)")
        failed += 1

    print()

    human_result = analyze_ai_likelihood(HUMAN_CODE)
    human_score = human_result["score"]
    print(f"Human-written code score: {human_score}%")
    print(f"  Explanation:\n{human_result['explanation']}")
    if human_score <= 50:
        print("  ✅ PASS (expected <= 50%)")
        passed += 1
    else:
        print(f"  ❌ FAIL (expected <= 50%, got {human_score}%)")
        failed += 1

    # --- Plagiarism ---
    print("\n--- PLAGIARISM DETECTION ---\n")

    identical = compare_codes(ORIGINAL, ORIGINAL)
    ident_score = identical["score"]
    print(f"Identical code score: {ident_score}%")
    if ident_score >= 95:
        print("  ✅ PASS (expected >= 95%)")
        passed += 1
    else:
        print(f"  ❌ FAIL (expected >= 95%, got {ident_score}%)")
        failed += 1

    renamed_result = compare_codes(ORIGINAL, RENAMED)
    ren_score = renamed_result["score"]
    print(f"Renamed variables score: {ren_score}%")
    print(f"  Explanation:\n{renamed_result['explanation']}")
    if ren_score >= 75:
        print("  ✅ PASS (expected >= 75%)")
        passed += 1
    else:
        print(f"  ❌ FAIL (expected >= 75%, got {ren_score}%)")
        failed += 1

    diff_result = compare_codes(ORIGINAL, DIFFERENT)
    diff_score = diff_result["score"]
    print(f"Completely different code score: {diff_score}%")
    if diff_score <= 25:
        print("  ✅ PASS (expected <= 25%)")
        passed += 1
    else:
        print(f"  ❌ FAIL (expected <= 25%, got {diff_score}%)")
        failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
