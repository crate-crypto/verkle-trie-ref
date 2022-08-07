from dataclasses import dataclass
from typing import List
from ecc import Fr
from copy import deepcopy

# Polynomial in coefficient form


@dataclass
class MonomialBasis:
    # Represents polynomials in coefficient form
    # The coefficient corresponding to the lowest
    # degree monomial is stored in the lowest index
    # ie [1,2,3] = 3x^2 + 2x + 1
    coeffs: List[Fr]

    def _empty():
        return MonomialBasis([])

    def mul(self, a, b):
        o = [0] * (len(a) + len(b) - 1)
        for i, aval in enumerate(a):
            for j, bval in enumerate(b):
                o[i+j] += a[i] * b[j]
        self.coeffs = o
        return self

    def div(self, a, b):
        assert len(a) >= len(b)
        a = [x for x in a]
        o = []
        apos = len(a) - 1
        bpos = len(b) - 1
        diff = apos - bpos
        while diff >= 0:
            quot = a[apos] / b[bpos]
            o.insert(0, quot)
            for i in range(bpos, -1, -1):
                a[diff+i] -= b[i] * quot
            apos -= 1
            diff -= 1

        self.coeffs = o
        return self

    def evaluate(self, x: Fr):
        y = Fr.zero()
        power_of_x = Fr.one()
        for _, p_coeff in enumerate(self.coeffs):
            y += power_of_x * p_coeff
            power_of_x = power_of_x * x
        return y

    def formal_derivative(self, f):
        derivative = [Fr(n + 1) * c for n, c in enumerate(f[1:])]
        self.coeffs = derivative
        return self

    def vanishing_poly(xs: List[Fr]):
        root = [Fr.one()]
        for x in xs:
            root.insert(0, Fr.zero())
            for j in range(len(root)-1):
                root[j] -= root[j+1] * x
        return MonomialBasis(root)

    # Methods for operator overload
    def __truediv__(self, other):
        result = MonomialBasis([])
        result.div(self, other)
        return result

    def __mul__(self, other):
        result = MonomialBasis([])
        result.mul(self, other)
        return result

    def __getitem__(self, index):
        return deepcopy(self.coeffs[index])

    def __len__(self):
        return len(self.coeffs)

    def __eq__(self, other):
        if isinstance(other, MonomialBasis) == False:
            raise TypeError(
                "can only check equality of polynomials in coefficient form")
        return self.coeffs == other.coeffs

    def __str__(self) -> str:
        result = ""
        for index, coeff in enumerate(self.coeffs):
            result += " " + format(coeff.value)
            if index != 0:
                result += " x^"+format(index)
            if index != len(self.coeffs) - 1:
                result += " +"

        return result
