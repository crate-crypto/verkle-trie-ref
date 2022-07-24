import hashlib
from crs import get_crs
import unittest
from ecc import Banderwagon


class TestCRS(unittest.TestCase):

    def test_crs_is_consistent(self):
        """
            Test that the CRS is consistent with https://hackmd.io/1RcGSMQgT4uREaq1CCx_cg#Methodology
        """
        crs = get_crs()

        self.assertEqual(256, len(crs))

        got_first_point = crs[0].to_bytes().hex()
        expected_fist_point = "01587ad1336675eb912550ec2a28eb8923b824b490dd2ba82e48f14590a298a0"
        self.assertEqual(got_first_point, expected_fist_point)

        got_256th_point = crs[255].to_bytes().hex()
        expected_256th_point = "3de2be346b539395b0c0de56a5ccca54a317f1b5c80107b0802af9a62276a4d8"
        self.assertEqual(got_256th_point, expected_256th_point)

        hasher = hashlib.sha256()
        for point in crs:
            hasher.update(point.to_bytes())
        result = hasher.digest().hex()

        self.assertEqual(
            "1fcaea10bf24f750200e06fa473c76ff0468007291fa548e2d99f09ba9256fdb", result)

    def test_crs_not_generator(self):
        """
            We use the generator point as the point `Q`, corresponding to the inner product
            so we check if the generated point is one of these
        """
        crs = get_crs()

        generator = Banderwagon.generator()

        for point in crs:
            self.assertNotEqual(generator, point)


if __name__ == '__main__':
    unittest.main()
