from dataclasses import dataclass
from typing import List
from ecc import Fr
from copy import deepcopy
from .monomial_basis import MonomialBasis


@dataclass
class LagrangeBasis:
    evaluations: List[Fr]
    domain: List[Fr]

    # An empty polynomial with no evaluations and no domain
    # This is useful because arithmetic methods require a `self`
    # to store their results
    def _empty():
        return LagrangeBasis([], [])

    def values(self):
        return deepcopy(self.evaluations)

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
        for eval in poly.evaluations:
            result.append(eval * constant)

        self.evaluations = result
        self.domain = poly.domain

    # TODO: we cannot add the type PrecomputedWeights because it
    # TODO: will trigger a circular import
    # TODO: we could take as a parameter: Aprime_DOMAIN_inv
    def evaluate_outside_domain(self, precomputed_weights, z: Fr):

        r = Fr.zero()
        A = MonomialBasis.vanishing_poly(self.domain)
        Az = A.evaluate(z)

        if Az.is_zero() == True:
            raise Exception(
                "vanishing polynomial evaluated to zero. z is therefore a point on the domain")

        inverses = Fr.multi_inv([z - x for x in self.domain])

        for i, x in enumerate(inverses):
            r += self[i] * precomputed_weights.Aprime_DOMAIN_inv[i] * x

        r = r * Az

        return r

    def interpolate(self):

        xs = self.domain
        ys = self.evaluations

        # Generate master numerator polynomial, eg. (x - x1) * (x - x2) * ... * (x - xn)
        root = MonomialBasis.vanishing_poly(xs)
        assert len(root) == len(ys) + 1

        # Generate per-value numerator polynomials, eg. for x=x2,
        # (x - x1) * (x - x3) * ... * (x - xn), by dividing the master
        # polynomial back by each x coordinate
        nums = [root / MonomialBasis([-x, Fr.one()]) for x in xs]
        # Generate denominators by evaluating numerator polys at each x
        denoms = [nums[i].evaluate(xs[i]) for i in range(len(xs))]
        invdenoms = Fr.multi_inv(denoms)
        # Generate output polynomial, which is the sum of the per-value numerator
        # polynomials rescaled to have the right y values
        b = [Fr.zero()] * len(ys)
        for i in range(len(xs)):
            yslice = ys[i] * invdenoms[i]
            for j in range(len(ys)):
                if nums[i][j] and ys[i]:
                    b[j] += nums[i][j] * yslice

        # Remove zero terms from the highest degree until
        # we get to a non-zero term
        while b[-1].is_zero():
            b.pop()

        return MonomialBasis(b)

    def equal(self, other):
        assert(isinstance(other, LagrangeBasis))
        for lhs_i, rhs_i in zip(self.evaluations, other.evaluations):
            if lhs_i != rhs_i:
                return False
        return True

    def __add__(self, other):
        result = LagrangeBasis._empty()
        result.add(self, other)
        return result

    def __sub__(self, other):
        result = LagrangeBasis._empty()
        result.sub(self, other)
        return result

    def __mul__(self, other):
        result = LagrangeBasis._empty()
        if isinstance(other, LagrangeBasis):
            result.mul(self, other)
        elif isinstance(other, Fr):
            result.scale(self, other)
        else:
            raise TypeError(
                "can only multiply polynomial by a constant or another polynomial")
        return result

    def __getitem__(self, index: int):
        # This is essentially an "evaluate_inside_domain" function
        return self.evaluations[index]
