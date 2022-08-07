import unittest
from ecc import Fr
from .common import inner_product


class TestCommon(unittest.TestCase):

    def test_inner_product_smoke(self):
        a = [Fr(1), Fr(2), Fr(3), Fr(4), Fr(5)]
        b = [Fr(10), Fr(12), Fr(13), Fr(14), Fr(15)]
        # Expected result should be 1*10 + 2*12 + 3*13 + 4*14 + 5*15
        expected_result = Fr(204)
        got_result = inner_product(a, b)
        self.assertTrue(got_result.equal(expected_result))


if __name__ == '__main__':
    unittest.main()
