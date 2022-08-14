import unittest
from .multiproof import MultiProof, VerifierQuery,  ProverQuery
from ipa.transcript import Transcript
from crs import CRS
from ecc import Fr
from polynomial.precomputed_weights import PrecomputedWeights


class TestMultiProof(unittest.TestCase):

    def test_basic_multiproof(self):
        """
            Test a simple multipoint proof
        """
        # Polynomials in lagrange basis
        poly_eval_a = [Fr(1), Fr(2), Fr(3), Fr(4), Fr(5), Fr(6), Fr(7), Fr(8), Fr(9), Fr(10), Fr(11), Fr(12), Fr(13), Fr(14), Fr(15), Fr(16),
                       Fr(17), Fr(18), Fr(19), Fr(20), Fr(21), Fr(22), Fr(23), Fr(24), Fr(25), Fr(26), Fr(27), Fr(28), Fr(29), Fr(30), Fr(31), Fr(32)]*8
        poly_eval_b = [Fr(32), Fr(31), Fr(30), Fr(29), Fr(28), Fr(27), Fr(26), Fr(25), Fr(24), Fr(23), Fr(22), Fr(21), Fr(20),
                       Fr(19), Fr(18), Fr(17), Fr(16), Fr(15), Fr(14), Fr(13), Fr(12), Fr(11), Fr(10), Fr(9), Fr(8), Fr(7), Fr(6), Fr(5), Fr(4), Fr(3), Fr(2), Fr(1)]*8

        crs = CRS.default()
        C_a = crs.commit(poly_eval_a)
        C_b = crs.commit(poly_eval_b)
        zs = [Fr.zero(), Fr.zero()]
        ys = [Fr(1), Fr(32)]
        fs = [poly_eval_a, poly_eval_b]
        Cs = [C_a, C_b]

        query_a = ProverQuery(fs[0], Cs[0], zs[0], ys[0])
        query_b = ProverQuery(fs[1], Cs[1], zs[1], ys[1])

        domain = [Fr(i) for i in range(256)]
        multiproof = MultiProof(domain, crs)

        prover_transcript = Transcript(b"test")
        proof = multiproof.make_multiproof(
            prover_transcript, [query_a, query_b])

        # Lets check the state of the transcript by squeezing out another challenge
        p_challenge = prover_transcript.challenge_scalar(b"state")

        self.assertEqual(
            "eee8a80357ff74b766eba39db90797d022e8d6dee426ded71234241be504d519", p_challenge.to_bytes().hex())

        verifier_transcript = Transcript(b"test")
        query_a = VerifierQuery(Cs[0], zs[0], ys[0])
        query_b = VerifierQuery(Cs[1], zs[1], ys[1])
        ok = multiproof.check_multiproof(
            verifier_transcript, [query_a, query_b], proof)

        self.assertTrue(ok)

        v_challenge = verifier_transcript.challenge_scalar(b"state")
        self.assertEqual(v_challenge, p_challenge)


if __name__ == '__main__':
    unittest.main()
