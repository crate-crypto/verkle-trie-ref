import unittest
from ecc import Banderwagon, Fr
from .monomial_basis import MonomialBasis as Polynomial


class TestMonomialBasis(unittest.TestCase):

    def test_vanishing_poly(self):
        """
            Test that the vanishing polynomial vanishes (returns 0) on the specified
            domain
        """
        xs = [Fr(0), Fr(1), Fr(2), Fr(3), Fr(4), Fr(5)]
        z = Polynomial.vanishing_poly(xs)
        for x in xs:
            eval = z.evaluate(x)
            self.assertTrue(eval.is_zero())

    def test_poly_div(self):
        # a = (x+1)(x+2) = x^2 + 3x + 2
        a = Polynomial([Fr(2), Fr(3), Fr(1)])
        # b = (x+1)
        b = Polynomial([Fr(1), Fr(1)])

        result = a / b

        # Expected result should be (x+2)
        expected = Polynomial([Fr(2), Fr(1)])

        self.assertEqual(result, expected)

    def test_derivative(self):
        # a = 6x^4 + 5x^3 + 10x^2 + 20x + 9
        a = Polynomial([Fr(9), Fr(20), Fr(10), Fr(5), Fr(6)])
        # the derivative of a is 24x^3 + 15x^2 + 20x + 20
        expected_a_prime = Polynomial([Fr(20), Fr(20), Fr(15), Fr(24)])

        got_a_prime = Polynomial._empty()
        got_a_prime.formal_derivative(a)

        self.assertEqual(got_a_prime, expected_a_prime)


if __name__ == '__main__':
    unittest.main()
