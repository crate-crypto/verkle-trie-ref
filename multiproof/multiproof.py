from dataclasses import dataclass
from typing import List
from ecc import Banderwagon, Fr
from polynomial.lagrange_basis import LagrangeBasis
from ipa.transcript import Transcript
# TODO: re-export the correct objects in dunder init
# TODO: so we don't have ipa.ipa
from ipa.ipa import ProverQuery as IPAProverQuery, VerifierQuery as IPAVerifierQuery, check_ipa_proof, make_ipa_proof, Proof as IPAProof
from polynomial.precomputed_weights import PrecomputedWeights
from .quotient import compute_quotient_inside_domain
from crs import CRS


# TODO: duplicated
def varbase_commit(values: List[Fr], elements: List[Banderwagon]):
    from crs import commit
    return commit(elements, values)


# We could store the polynomial once and just gather the queries for
# that polynomial. This way is in-efficient, however it's easier to read
@dataclass
class ProverQuery:
    f: LagrangeBasis
    # Commitment to f(X)
    C: Banderwagon
    # f(z) = y
    z: Fr
    y: Fr


@dataclass
class VerifierQuery:
    # Commitment to f(X)
    C: Banderwagon
    # f(z) = y
    z: Fr
    y: Fr


@dataclass
class Proof:
    ipa: IPAProof
    D: Banderwagon


# TODO: rename this as it sounds like the object that holds the proof
# TODO Maybe multiprover
@dataclass
class MultiProof:
    precomp: PrecomputedWeights
    crs: CRS

    def __init__(self, domain: List[Fr], crs: CRS) -> None:
        self.precomp = PrecomputedWeights(domain)
        self.crs = crs

    def make_multiproof(self, transcript: Transcript, queries: List[ProverQuery]):
        domain_size = len(self.precomp.domain)

        transcript.domain_sep(b"multiproof")

        # Add queries into transcript
        for query in queries:
            transcript.append_point(query.C, b"C")
            transcript.append_scalar(query.z, b"z")
            transcript.append_scalar(query.y, b"y")

        # Generate challenge from queries
        r = transcript.challenge_scalar(b"r")

        g = [Fr.zero()] * domain_size
        power_of_r = Fr.one()
        for query in queries:
            f = query.f
            index = query.z
            quotient = compute_quotient_inside_domain(self.precomp, f, index)
            for i in range(domain_size):
                g[i] += power_of_r * quotient[i]

            power_of_r = power_of_r * r

        D = self.crs.commit(g)
        transcript.append_point(D, b"D")

        # Step 2: Compute h in evaluation form

        t = transcript.challenge_scalar(b"t")

        h = [Fr.zero()] * domain_size
        power_of_r = Fr.one()

        for query in queries:
            f = query.f
            index = query.z.value  # TODO: expose a method on Fr called to_int
            denominator_inv = Fr.zero()  # TODO expose Fr.inv method
            denominator_inv = denominator_inv.inv(
                t - self.precomp.domain[index])
            for i in range(domain_size):
                h[i] += power_of_r * f[i] * denominator_inv

            power_of_r = power_of_r * r

        h_minus_g = [(h[i] - g[i]) for i in range(domain_size)]

        # Step 3: Evaluate and compute IPA proofs

        E = self.crs.commit(h)
        transcript.append_point(E, b"E")

        ipa_commitment = E - D
        polynomial = h_minus_g
        input_point = t
        input_point_vector = self.precomp.barycentric_formula_constants(
            input_point)

        query = IPAProverQuery(polynomial, ipa_commitment,
                               input_point, input_point_vector)

        # TODO: can we modify the API to not return the output point?
        output_point, ipa_proof = make_ipa_proof(self.crs, transcript, query)

        return Proof(ipa_proof, D)

    def check_multiproof(self, transcript: Transcript, queries: List[VerifierQuery], proof: Proof):

        transcript.domain_sep(b"multiproof")
        D = proof.D
        ipa_proof = proof.ipa

        for query in queries:
            C_i = query.C
            z_i = query.z
            y_i = query.y
            transcript.append_point(C_i, b"C")
            transcript.append_scalar(z_i, b"z")
            transcript.append_scalar(y_i, b"y")

        # Step 1
        r = transcript.challenge_scalar(b"r")

        # Step 2
        transcript.append_point(D, b"D")
        t = transcript.challenge_scalar(b"t")

        E_coefficients = {}
        g_2_of_t = Fr.zero()
        power_of_r = Fr.one()

        C_by_serialized = {}

        for query in queries:
            C = query.C
            z = query.z.value
            y = query.y

            E_coefficient = power_of_r / t - self.precomp.domain[z]
            C_serialized = bytes(C.to_bytes())
            C_by_serialized[C_serialized] = C
            E_coefficients[C_serialized] = E_coefficient if C_serialized not in E_coefficients \
                else (E_coefficients[C_serialized] + E_coefficient)
            g_2_of_t += E_coefficient * y

            power_of_r = power_of_r * r

        E = varbase_commit(E_coefficients.values(), [C_by_serialized[x]
                                                     for x in E_coefficients.keys()])
        transcript.append_point(E, b"E")

        # Step 3 (Check IPA proofs)
        y = g_2_of_t
        ipa_commitment = E - D
        input_point = t
        output_point = y
        input_point_vector = self.precomp.barycentric_formula_constants(
            input_point)

        query = IPAVerifierQuery(ipa_commitment, input_point,
                                 input_point_vector, output_point, ipa_proof)

        return check_ipa_proof(self.crs, transcript, query)
