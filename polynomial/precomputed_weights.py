from dataclasses import dataclass
from .monomial_basis import MonomialBasis
from .lagrange_basis import LagrangeBasis
from typing import List
from ecc import Fr


@dataclass
class PrecomputedWeights:
    # TODO: We don't _need_ to store the vanishing polynomial
    # TODO: we only need to store its derivative and whenever we need to evaluate
    # TODO: the vanishing polynomial, it can be done via the domain
    # Vanishing polynomial
    A: MonomialBasis
    # Derivative of the vanishing polynomial
    Aprime: MonomialBasis
    # Aprime evaluated on the domain
    Aprime_DOMAIN: LagrangeBasis
    # Aprime evaluated on the domain and then inverted
    Aprime_DOMAIN_inv: LagrangeBasis
    # domain
    domain: List[Fr]
    # Inverse of the domain
    domain_inverses: List[Fr]

    def __init__(self, domain: List[Fr]) -> None:

        assert check_domain_is_continuous_and_increasing(domain) == True

        self.domain = domain
        domain_size = len(domain)

        self.A = MonomialBasis.vanishing_poly(domain)

        Aprime = MonomialBasis._empty()
        Aprime.formal_derivative(self.A)
        self.Aprime = Aprime

        self.Aprime_DOMAIN = []
        self.Aprime_DOMAIN_inv = []

        for x in range(len(domain)):
            Aprime_x = self.Aprime.evaluate(Fr(x))

            APrime_x_inv = Fr.zero()
            APrime_x_inv.inv(Aprime_x)

            self.Aprime_DOMAIN.append(Aprime_x)
            self.Aprime_DOMAIN_inv.append(APrime_x_inv)

        # This is not fully correct as the first element will be the inverse of 0
        # We keep it this way for now because it is what the research code did
        # TODO: refactor this to make it more readable
        # If domain size is 4 for example, the output would be:
        # [1/0, 1/1, 1/2, 1/3, -1/3, -1/2,-1/1]
        inverses = []
        for d in list(range(domain_size)) + list(range(-domain_size + 1, 0)):
            d_inv = Fr.zero()
            d_inv.inv(Fr(d))
            inverses.append(d_inv)

        self.domain_inverses = inverses

    def barycentric_formula_constants(self, z):
        """
        Gives the constant used in the barycentric formula when evaluating a polynomial at z
        b_i = A(z) / A'(DOMAIN[i]) * 1 / (z - DOMAIN[i])
        """

        r: List[Fr] = []
        Az = self.A.evaluate(z)

        inverses = self.multi_inv([z - x for x in self.domain])

        for i, x in enumerate(inverses):
            r.append(Az * self.Aprime_DOMAIN_inv[i] * x)

        return r


def check_domain_is_continuous_and_increasing(domain: List[Fr]):
    prev_element = domain[0]

    for element in domain[1:]:
        diff = element - prev_element
        if diff.is_one() == False:
            return False
        prev_element = element
    return True
