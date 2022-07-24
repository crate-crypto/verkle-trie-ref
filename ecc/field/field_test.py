import unittest
from field import Field


class TestGenericFieldMethods(unittest.TestCase):

    def test_addition(self):
        a = Field(10, 13)
        b = Field(30, 13)

        got = Field(0, 13)
        got.add(a, b)

        expected = Field(40, 13)

        self.assertEqual(expected, got)

    def test_subtraction(self):
        a = Field(10, 13)
        b = Field(30, 13)

        got = Field(0, 13)
        got.sub(a, b)

        expected = Field(-20, 13)

        self.assertEqual(expected, got)

    def test_multiplication(self):
        a = Field(200, 13)
        b = Field(3, 13)

        got = Field(0, 13)
        got.mul(a, b)

        expected = Field(2, 13)

        self.assertEqual(expected, got)

    def test_division_inversion(self):
        a = Field(200, 13)
        b = Field(3, 13)

        got = Field(0, 13)
        got.div(a, b)

        expected = Field(0, 13)
        expected.inv(b)
        expected.mul(expected, a)

        self.assertEqual(expected, got)

    def test_inversion(self):
        b = Field(3, 13)

        b_inv = Field(0, 13)
        b_inv.inv(b)

        result = Field(0, 13)
        result.mul(b_inv, b)

        expected = Field(1, 13)

        self.assertEqual(expected, result)

    def test_sqrt_sqr(self):
        b = Field(3, 13)
        self.assertTrue(b.legendre() == 1)

        b_sqrt = Field(0, 13)
        b_sqrt.sqrt(b)

        result = Field(0, 13)
        result.exp(b_sqrt, 2)

        expected = b

        self.assertEqual(expected, result)

    def test_neg(self):
        b = Field(3, 13)
        self.assertTrue(b.legendre() == 1)

        b_neg = Field(0, 13)
        b_neg.neg(b)

        expected = Field(-3, 13)

        self.assertEqual(expected, b_neg)

    def test_serialise(self):
        three = Field(3, 13)

        bytes = three.to_bytes(2)
        deserialised_three = Field.from_bytes(bytes, 13)

        self.assertEqual(three, deserialised_three)


if __name__ == '__main__':
    unittest.main()
