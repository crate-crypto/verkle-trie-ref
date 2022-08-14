from ecc import Fr
from polynomial.lagrange_basis import LagrangeBasis
from polynomial.precomputed_weights import PrecomputedWeights


# Previously named: compute_inner_quotient_in_evaluation_form
def compute_quotient_inside_domain(precomp: PrecomputedWeights, f: LagrangeBasis, index: Fr):
    domain_size = len(precomp.domain)
    inverses = precomp.domain_inverses
    Aprime_domain = precomp.Aprime_DOMAIN
    Aprime_domain_inv = precomp.Aprime_DOMAIN_inv

    # TODO: check that index is on domain
    index = index.value
    q = [Fr.zero()] * domain_size
    y = f[index]
    for i in range(domain_size):
        if i != index:
            q[i] = (f[i] - y) * inverses[i - index]
            q[index] += (f[i] - y) * inverses[index - i] * \
                Aprime_domain[index] * Aprime_domain_inv[i]

    return q


def compute_quotient_outside_domain(precomp: PrecomputedWeights, f: LagrangeBasis, z: Fr, y: Fr):

    domain = precomp.domain
    domain_size = len(domain)

    q = [0] * domain_size
    for i in range(domain_size):
        q[i] = (f[i] - y) / (domain[i] - z)

    return q
