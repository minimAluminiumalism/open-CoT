"""Benchmark problems with programmatic ground-truth verifiers.

Every problem carries a verifier that computes the answer independently
(brute force / DP / discriminant solving), so correctness never depends
on remembered answers or model self-evaluation.
"""
import itertools
import math
import re


def v_perm_f3():
    return sum(1 for p in itertools.permutations(range(7))
               if all(p[p[p[x]]] == x for x in range(7)))


def v_imo81():
    best = 0
    for m in range(1, 1982):
        for e in (1, -1):
            disc = 5 * m * m + 4 * e          # n^2 - m n - (m^2+e) = 0
            if disc < 0:
                continue
            s = math.isqrt(disc)
            if s * s != disc:
                continue
            for n in ((m + s) // 2, (m - s) // 2):
                if 1 <= n <= 1981 and n * n - m * n - m * m == e:
                    best = max(best, m * m + n * n)
    return best


def v_subsets5():
    dp = [0] * 5
    dp[0] = 1
    for n in range(1, 1001):
        dp = [dp[r] + dp[(r - n) % 5] for r in range(5)]
    return dp[0]


def v_derange8():
    return sum(1 for p in itertools.permutations(range(8))
               if all(p[i] != i for i in range(8)))


def v_invol8():
    return sum(1 for p in itertools.permutations(range(8))
               if all(p[p[i]] == i for i in range(8)))


def v_fixed2_7():
    return sum(1 for p in itertools.permutations(range(7))
               if sum(p[i] == i for i in range(7)) == 2)


def v_factor9000():
    cnt = 0
    for a in range(1, 9001):
        if 9000 % a:
            continue
        b = 9000 // a
        if a < b and (b - a) % 2 == 0:
            y, x = (b - a) // 2, (a + b) // 2
            if y > 0 and x * x - y * y == 9000:
                cnt += 1
    return cnt


def v_mod7poly():
    return sum(1 for n in range(1, 1001) if (n * n + n + 1) % 7 == 0)


def v_paths():
    cnt = 0
    for right in itertools.combinations(range(16), 8):
        x = y = 0
        ok = True
        for i in range(16):
            if i in right:
                x += 1
            else:
                y += 1
            if y > x:
                ok = False
                break
        cnt += ok
    return cnt


def v_triple():
    cnt = 0
    for a in range(1, 100):
        for b in range(1, 100):
            for c in range(1, 100):
                if (a + b + c) % 7 == 0 and (a * b * c) % 5 == 0:
                    cnt += 1
    return cnt


PROBLEMS = [
    {"id": "perm-f3-7",
     "q": "Let f: {1,2,3,4,5,6,7} -> {1,2,3,4,5,6,7} be a function such that "
         "f(f(f(x))) = x for every x in the domain. Find the number of such "
         "functions f.",
     "verify": v_perm_f3},
    {"id": "imo-1981-p3",
     "q": "Determine the maximum value of m^2 + n^2, where m and n are integers "
         "in {1, 2, ..., 1981} satisfying (n^2 - mn - m^2)^2 = 1.",
     "verify": v_imo81},
    {"id": "subsets-mod5",
     "q": "Let S = {1, 2, ..., 1000}. Compute the exact number of subsets T of "
         "S (including the empty set) such that the sum of the elements of T is "
         "divisible by 5. Express your answer in closed form.",
     "verify": v_subsets5, "closed_form": True},
    {"id": "derange-8",
     "q": "Find the number of permutations of {1,2,3,4,5,6,7,8} in which no "
         "element appears in its original position.",
     "verify": v_derange8},
    {"id": "invol-8",
     "q": "Find the number of functions f: {1,...,8} -> {1,...,8} satisfying "
         "f(f(x)) = x for all x.",
     "verify": v_invol8},
    {"id": "fixed2-7",
     "q": "How many permutations of {1,2,3,4,5,6,7} have exactly two fixed "
         "points?",
     "verify": v_fixed2_7},
    {"id": "factor-9000",
     "q": "Find the number of ordered pairs (x, y) of positive integers "
         "satisfying x^2 - y^2 = 9000.",
     "verify": v_factor9000},
    {"id": "mod7-poly",
     "q": "How many integers n in {1, 2, ..., 1000} satisfy the condition that "
         "n^2 + n + 1 is divisible by 7?",
     "verify": v_mod7poly},
    {"id": "catalan-paths",
     "q": "Find the number of lattice paths from (0,0) to (8,8) using only "
         "unit steps right or up that never rise above the diagonal y = x.",
     "verify": v_paths},
    {"id": "triple-mod",
     "q": "How many ordered triples (a, b, c) of integers with "
         "1 <= a, b, c <= 99 satisfy both (a + b + c) divisible by 7 and "
         "abc divisible by 5?",
     "verify": v_triple},
]


def ground_truth(problem):
    return problem["verify"]()


def judge(answer_text, problem, expected=None):
    """Check whether the answer text contains the expected value.

    Handles LaTeX thousand separators (3,\\!524,\\!578) and plain commas.
    Closed-form problems get a dedicated pattern check.
    """
    ans = (answer_text or "").replace(",\\!", "").replace("{,}", "")
    flat = re.sub(r"[,{}]", "", ans)
    if problem.get("closed_form"):
        return bool(re.search(r"2\^?1000\s*\+\s*4", flat))
    if expected is None:
        expected = problem["verify"]()
    return str(expected) in re.findall(r"\d+", flat)
