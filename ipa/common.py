
from typing import List
from ecc import Fr

# TODO: Methods here may be moved into different modules in the future


# Take the inner product between two lists of field
# elements
def inner_product(a: List[Fr], b: List[Fr]) -> Fr:
    result = Fr(0)
    for a_i, b_i in zip(a, b):
        term = Fr(0)
        term.mul(a_i, b_i)
        result.add(result, term)
    return result
