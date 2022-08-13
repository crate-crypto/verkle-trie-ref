# import unittest
# from ecc import Fr
# from .precomputed_weights import check_domain_is_continuous_and_increasing


# class TestPrecomputedWeights(unittest.TestCase):

#     def test_domain_correctness(self):
#         """
#             Test that the domain is continuos and increasing. If this is not the case
#             then the setup for precomputed weights, will need to be changed
#         """
#         domain = [Fr(0), Fr(1), Fr(2), Fr(3), Fr(4), Fr(5)]
#         domain_is_correct = check_domain_is_continuous_and_increasing(domain)
#         self.assertTrue(domain_is_correct)

#         # This domain has a gap between 0 and 2
#         domain = [Fr(0), Fr(2), Fr(3), Fr(4), Fr(5)]
#         domain_is_correct = check_domain_is_continuous_and_increasing(domain)
#         self.assertFalse(domain_is_correct)

#         # This domain is not increasing
#         domain = [Fr(5), Fr(4), Fr(3), Fr(2), Fr(1)]
#         domain_is_correct = check_domain_is_continuous_and_increasing(domain)
#         self.assertFalse(domain_is_correct)


# if __name__ == '__main__':
#     unittest.main()
