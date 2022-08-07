

from dataclasses import dataclass
from typing import List
from ecc import Fr


# We never need to represent polynomials in their coefficient form
# unless it is for testing. Therefore, we use the class Polynomial
# to mean a polynomial represented in evaluation form
@dataclass
class Polynomial:
    evaluations: List[Fr]
    # We can probably ignore this as the domain never changes
    domain: List[Fr]

    # An empty polynomial with no evaluations and no domain
    # This is useful because arithmetic methods require a `self`
    # to store their results
    def _empty():
        return Polynomial([], [])

    def __arithmetic_op(self, lhs, rhs, operation):
        if lhs.domain != rhs.domain:
            raise Exception(
                "can only perform arithmetic operations on polynomials over the same domain")

        result: List[Fr] = []
        for lhs_i, rhs_i in zip(lhs.evaluations, rhs.evaluations):
            result.append(operation(lhs_i, rhs_i))

        self.evaluations = result
        self.domain = lhs.domain

        return self

    def add(self, lhs, rhs):
        def add(x, y): return x + y
        return self.__arithmetic_op(lhs, rhs, add)

    def sub(self, lhs, rhs):
        def sub(x, y): return x - y
        return self.__arithmetic_op(lhs, rhs, sub)

    def mul(self, lhs, rhs):
        def mul(x, y): return x * y
        return self.__arithmetic_op(lhs, rhs, mul)

    def scale(self, poly, constant: Fr):
        result: List[Fr] = []
        for eval in poly:
            result.append(eval * constant)

        self.evaluations = eval

    def equal(self, other):
        assert(isinstance(other, Polynomial))
        for lhs_i, rhs_i in zip(self.evaluations, other.evaluations):
            if lhs_i != rhs_i:
                return False
        return True

    def __add__(self, other):
        result = Polynomial._empty()
        result.add(self, other)
        return result

    def __sub__(self, other):
        result = Polynomial._empty()
        result.sub(self, other)
        return result

    def __mul__(self, other):
        result = Polynomial._empty()
        if isinstance(other, Polynomial):
            result.mul(self, other)
        elif isinstance(other, Fr):
            result.scale(self, other)
        else:
            raise TypeError(
                "can only multiply polynomial by a constant or another polynomial")
        return result
