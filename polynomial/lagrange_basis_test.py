import unittest
from .lagrange_basis import LagrangeBasis as Polynomial
from ecc import Fr


class TestLagrangeBasis(unittest.TestCase):

    def test_add_sub(self):
        domain = [Fr(0), Fr(1), Fr(2), Fr(3), Fr(4), Fr(5)]

        # Evaluations
        # x^2
        x_squared = [Fr(0), Fr(1), Fr(4), Fr(9), Fr(16), Fr(25)]
        # x + 2
        x_plus_2 = [Fr(2), Fr(3), Fr(4), Fr(5), Fr(6), Fr(7)]

        a = Polynomial(x_squared, domain)
        b = Polynomial(x_plus_2, domain)

        result = a + b

        expected_evaluations = [Fr(2), Fr(4), Fr(8), Fr(14), Fr(22), Fr(32)]
        expected_result = Polynomial(expected_evaluations, domain)

        self.assertEqual(expected_result, result)

        expected_result = expected_result - b
        self.assertEqual(expected_result, a)

    def test_mul(self):
        domain = [Fr(0), Fr(1), Fr(2), Fr(3), Fr(4), Fr(5)]

        # Evaluations
        # x^2
        x_squared = [Fr(0), Fr(1), Fr(4), Fr(9), Fr(16), Fr(25)]
        # x^4
        x_pow_4 = [Fr(0), Fr(1), Fr(16), Fr(81), Fr(256), Fr(625)]

        a = Polynomial(x_squared, domain)

        result = a * a

        expected_result = Polynomial(x_pow_4, domain)

        self.assertEqual(expected_result, result)

    def test_scale(self):
        domain = [Fr(0), Fr(1), Fr(2), Fr(3), Fr(4), Fr(5)]

        # Evaluations
        # x^2
        x_squared = [Fr(0), Fr(1), Fr(4), Fr(9), Fr(16), Fr(25)]
        constant = Fr(10)

        a = Polynomial(x_squared, domain)

        result = a * constant

        expected_evaluations = [
            Fr(0), Fr(10), Fr(40), Fr(90), Fr(160), Fr(250)]

        expected_result = Polynomial(expected_evaluations, domain)

        self.assertEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
