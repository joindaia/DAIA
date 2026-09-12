"""Trusted, bounded DATA-ONLY demo verifier. Never executes contributed code.

The demo certifies only a nontrivial integer factorization, not a new theorem.
No shell, imports, network, Lean, or arbitrary checker definitions are accepted.
"""
from .crypto import strict_json


def check_factorization(number: int, artifact: str) -> bool:
    if type(number) is not int or not 4 <= number <= 10**12:
        return False
    if not isinstance(artifact, str):
        return False
    try:
        size = len(artifact.encode("utf-8"))
    except UnicodeEncodeError:
        return False
    if size > 4096:
        return False
    try:
        value = strict_json(artifact)
    except (ValueError, TypeError, RecursionError):
        return False
    if not isinstance(value, dict) or set(value) != {"factors"}:
        return False
    factors = value["factors"]
    if not isinstance(factors, list) or not 2 <= len(factors) <= 40:
        return False
    product = 1
    for f in factors:
        if type(f) is not int or not 1 < f < number:
            return False
        product *= f
        if product > number:
            return False
    return product == number
