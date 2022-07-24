#!/usr/bin/env python3
import unittest
from ecc import Banderwagon, Fr
from random import randint
from .transcript import Transcript


class TestTranscript(unittest.TestCase):

    def test_prover_verifier_consistency(self):
        """
            Test that if the prover and verifier
            do the exact same operations, they will end up
            at the exact same state.
        """
        point = Banderwagon.generator()
        scalar = Fr(randint(0, 2**256))

        # Prover's View
        prover_transcript = Transcript(b"protocol_name")

        prover_transcript.append_point(point, b"D")
        prover_transcript.domain_sep(b"sub_protocol_name")
        prover_transcript.append_scalar(scalar, b"r")

        # Prover challenge
        prover_q = prover_transcript.challenge_scalar(b"q")

        # Verifier's View
        verifier_transcript = Transcript(b"protocol_name")

        verifier_transcript.append_point(point, b"D")
        verifier_transcript.domain_sep(b"sub_protocol_name")
        verifier_transcript.append_scalar(scalar, b"r")

        # Verifier challenge
        verifier_q = verifier_transcript.challenge_scalar(b"q")

        assert prover_q == verifier_q

    def test_vector_0(self):
        """
            Test that squeezing out a challenge twice
            will produce different challenges. ie it is 
            not possible to accidentally generate the same challenge
        """
        transcript = Transcript(b"foo")
        first_challenge = transcript.challenge_scalar(b"f")
        second_challenge = transcript.challenge_scalar(b"f")

        self.assertNotEqual(first_challenge, second_challenge)

    def test_vector_1(self):
        """
            Test that challenge creation is consistent across implementations
        """
        transcript = Transcript(b"simple_protocol")
        challenge = transcript.challenge_scalar(b"simple_challenge")

        self.assertEqual("c2aa02607cbdf5595f00ee0dd94a2bbff0bed6a2bf8452ada9011eadb538d003",
                         challenge.to_bytes().hex())

    def test_vector_2(self):
        """
            Test that append scalar is consistent across implementations
        """
        transcript = Transcript(b"simple_protocol")
        scalar = Fr(5)

        transcript.append_scalar(scalar, b"five")
        transcript.append_scalar(scalar, b"five again")

        challenge = transcript.challenge_scalar(b"simple_challenge")

        self.assertEqual("498732b694a8ae1622d4a9347535be589e4aee6999ffc0181d13fe9e4d037b0b",
                         challenge.to_bytes().hex())

    def test_vector_3(self):
        """
            Test that domain separation is consistent across implementations
        """
        transcript = Transcript(b"simple_protocol")
        minus_one = Fr(-1)
        one = Fr(1)
        transcript.append_scalar(minus_one, b"-1")
        transcript.domain_sep(b"separate me")
        transcript.append_scalar(minus_one, b"-1 again")
        transcript.domain_sep(b"separate me again")
        transcript.append_scalar(one, b"now 1")

        challenge = transcript.challenge_scalar(b"simple_challenge")

        self.assertEqual("14f59938e9e9b1389e74311a464f45d3d88d8ac96adf1c1129ac466de088d618",
                         challenge.to_bytes().hex())

    def test_vector_4(self):
        """
            Test that appending points is consistent across implementations
        """
        transcript = Transcript(b"simple_protocol")

        generator = Banderwagon.generator()

        transcript.append_point(generator, b"generator")
        challenge = transcript.challenge_scalar(b"simple_challenge")

        self.assertEqual("8c2dafe7c0aabfa9ed542bb2cbf0568399ae794fc44fdfd7dff6cc0e6144921c",
                         challenge.to_bytes().hex())


if __name__ == '__main__':
    unittest.main()
