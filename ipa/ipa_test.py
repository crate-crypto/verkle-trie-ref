import unittest
from .ipa import VerifierQuery, check_ipa_proof, make_ipa_proof, ProverQuery
from .transcript import Transcript
from crs import CRS
from ecc import Fr
from polynomial.precomputed_weights import PrecomputedWeights


class TestIPA(unittest.TestCase):

    def test_basic_ipa_proof(self):
        """
            Test a simple IPA proof
        """
        domain = [Fr(i) for i in range(256)]
        weights = PrecomputedWeights(domain)

        # Polynomial in lagrange basis
        lagrange_poly = [Fr(1), Fr(2), Fr(3), Fr(4), Fr(5), Fr(6), Fr(7), Fr(8), Fr(9), Fr(10), Fr(11), Fr(12), Fr(13), Fr(14), Fr(15), Fr(16),
                         Fr(17), Fr(18), Fr(19), Fr(20), Fr(21), Fr(22), Fr(23), Fr(24), Fr(25), Fr(26), Fr(27), Fr(28), Fr(29), Fr(30), Fr(31), Fr(32)]*8

        # Commit to the polynomial in lagrange basis
        crs = CRS.default()
        commitment = crs.commit(lagrange_poly)

        self.assertEqual(
            "1b9dff8f5ebbac250d291dfe90e36283a227c64b113c37f1bfb9e7a743cdb128", commitment.to_bytes().hex())

        prover_transcript = Transcript(b"test")

        # create a opening proof for a point outside of the domain
        input_point = Fr(2101)
        b = weights.barycentric_formula_constants(input_point)
        query = ProverQuery(lagrange_poly, commitment, input_point, b)

        output_point, proof = make_ipa_proof(crs, prover_transcript, query)

        # # Lets check the state of the transcript by squeezing out another challenge
        p_challenge = prover_transcript.challenge_scalar(b"state")

        self.assertEqual(
            "0a81881cbfd7d7197a54ebd67ed6a68b5867f3c783706675b34ece43e85e7306", p_challenge.to_bytes().hex())

        verifier_transcript = Transcript(b"test")

        query = VerifierQuery(commitment, input_point, b, output_point, proof)

        ok = check_ipa_proof(crs, verifier_transcript, query)

        self.assertTrue(ok)


if __name__ == '__main__':
    unittest.main()
