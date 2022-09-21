import unittest
from ecc import Banderwagon, Fr
from verkle.nodes.inner_node import InnerNode
from .verkle import VerkleTrie
from .nodes.suffix_tree import VALUE_EXISTS_MARKER,  VerkleValue
from .common_types import VerkleCommitment
from crs import get_crs, CRS
from .basic_rng import BasicPRNG


# Insert `batch_size * num_batches` into a trie
# We collect the root at every `batch_size` inserts
# For example, if the num_batches = 5 and batch_size = 100
# We insert 100 values into the trie and then collect the root at that point
# Then we insert another 100 values into the same trie and then collect the root
# We would end up with 5 roots altogether, which is what this function returns
def prng_test_helper(prng, batch_size, num_batches):

    got_roots = []

    # Generate pseudo random values
    list_of_keys = prng.rand_vec_bytes(num_batches * batch_size)

    for step in range(1, num_batches+1):

        trie = VerkleTrie(CRS.default())

        for i in range(step * batch_size):
            key = list_of_keys[i]
            trie.insert(key, key)

        got_roots.append(
            trie.root_node.commitment_to_field().to_bytes().hex())

    return got_roots


class TestVerkle(unittest.TestCase):

    def test_smoke(self):
        trie = VerkleTrie(CRS.default())
        trie.insert([1]*32, [2]*32)

    def test_consistent_group_to_field(self):
        """
            Test the group to field implementation. This hardcoded value was cross-checked with the Rust and Go implementation.
        """
        generator = VerkleCommitment(Banderwagon.generator())

        self.assertEqual(
            "d1e7de2aaea9603d5bc6c208d319596376556ecd8336671ba7670c2139772d14", generator.commitment_to_field().to_bytes().hex())

    def test_empty_trie(self):
        """
            Test the root when the trie is empty, should be 0
        """

        trie = VerkleTrie(CRS.default())

        self.assertEqual(
            "0000000000000000000000000000000000000000000000000000000000000000", trie.root().hex())

    def test_simple_insert_consistency(self):
        """
        Test a simple key insert
        """
        key = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                     17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32])
        value = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                       17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32])
        trie = VerkleTrie(CRS.default())

        trie.insert(key, value)

        # All children of the root node except for the one with index=1 should be empty
        self.assertEqual(len(trie.root_node.children), 1)
        child_index = 1
        child = trie.root_node[child_index]

        # Now looking into the stem, it should only have 1 child/suffix value
        self.assertEqual(child.stem, key[0:31])
        self.assertEqual(len(child.values), 1)

        # The suffix value should be at the index=32 as 32 was the last byte of the key
        suffix_index = 32
        self.assertEqual(child.values[suffix_index], VerkleValue(value))

        # Since the suffix index was 32 which is less than 128, it means we only need to modify C1 and not C2
        # Note, a single value can only ever modify one of C1 and C2, never both of them.
        c2_field = child.C2.commitment_to_field().to_bytes().hex()
        self.assertEqual(c2_field, Fr(0).to_bytes().hex())

        self.assertEqual(
            "029b6c4c8af9001f0ac76472766c6579f41eec84a73898da06eb97ebdab80a09", trie.root_node.commitment_to_field().to_bytes().hex())

    def test_simple_update_consistency(self):
        """
        Test a simple value update
        """
        key = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                     17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32])
        value = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                       17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32])
        old_value = int(0).to_bytes(32, "little")

        trie = VerkleTrie(CRS.default())
        trie.insert(key, old_value)
        self.assertEqual(
            "77a0747bd526d9d9af60bd5665d24d6cb421f5c8e726b1de62f914f3ff9a361c", trie.root_node.commitment_to_field().to_bytes().hex())

        trie.insert(key, value)

        child_index = 1
        child = trie.root_node[child_index]

        c2_field = child.C2.commitment_to_field().to_bytes().hex()
        self.assertEqual(c2_field, Fr(0).to_bytes().hex())

        c1_field = child.C1.commitment_to_field().to_bytes().hex()
        self.assertEqual(
            "bb4ea329042701a82badf0da8d1ace7df0e290686e16b7bc89ee0f3c8fd7ab16", c1_field)

        self.assertEqual("b897ba52c5317acd75f5f3c3922f461357d4fb8b685fe63f20a3b2adb014370a",
                         child.commitment_to_field().to_bytes().hex())
        # Value taken from test: test_simple_insert_consistency
        self.assertEqual(
            "6f5e7cfc3a158a64e5718b0d2f18f564171342380f5808f3d2a82f7e7f3c2778", trie.root().hex())
        self.assertEqual(
            "029b6c4c8af9001f0ac76472766c6579f41eec84a73898da06eb97ebdab80a09", trie.root_node.commitment_to_field().to_bytes().hex())

    def test_insert_longest_path(self):
        """
        Test where keys create the longest path
        """
        trie = VerkleTrie(CRS.default())

        key_zero = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        key_zero_except_30 = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0])

        trie.insert(key_zero, key_zero)
        trie.insert(key_zero_except_30, key_zero_except_30)

        self.assertEqual("fe2e17833b90719eddcad493c352ccd491730643ecee39060c7c1fff5fcc621a",
                         trie.root_node.commitment_to_field().to_bytes().hex())

    def test_basic_prng(self):
        """
        Test prng outputs expected values
        """
        # Default seed is 32 zeroes
        seed = int(0).to_bytes(32, "little")

        prng = BasicPRNG(seed)
        first_output = prng.rand_bytes()
        second_output = prng.rand_bytes()
        third_output = prng.rand_bytes()

        # Values taken from Rust implementation
        first_expected = "2c34ce1df23b838c5abf2a7f6437cca3d3067ed509ff25f11df6b11b582b51eb"
        second_expected = "b68f593141969cfeddf2011667ccdca92d2d22b414194bdf4ccbaa2833c85be2"
        third_expected = "74d8b89f49a16dd0a338f1dc90fe470f3137d7df12cf0b76c82b0b5f2fa9028b"

        self.assertEqual(first_expected, first_output.hex())
        self.assertEqual(second_expected, second_output.hex())
        self.assertEqual(third_expected, third_output.hex())

    def test_insert_100(self):
        """
        Test in batch steps of 100, if values are consistent across implementations
        """

        # Default seed is 32 zeroes
        seed = int(0).to_bytes(32, "little")
        prng = BasicPRNG(seed)

        num_batches = 1
        batch_size = 100

        got_roots = prng_test_helper(prng, batch_size, num_batches)

        expected = [
            "afb01df826bd42ddea9001551980f7cfa74f0ca7e0ba36a9079dea4062848600",
            "4cd6573f3602df0a1438c894e2f0f465e16537c4474e3ab35ee74d5b3afe180f",
            "1da1675938ba4ad2545fd163dc2053212cd75b54fc44e70f11fd20b05363650b",
            "bdad99347763dc06765e329da53ae85333a9d89fa9e06ef3fccf30c8c89cb804",
            "cf0b7ea967a755f6c09762aa4a650899bb79d21ef56f1fe6672621149e639905",
        ]
        for i in range(num_batches):
            got_root_hex = got_roots[i]
            self.assertEqual(expected[i], got_root_hex)

    def test_splitting_value_smoke(self):
        """
        Test zero and None are split differently
        """

        none_value = VerkleValue()
        low, high = none_value.low_high()
        self.assertEqual(low, 0)
        self.assertEqual(high, 0)

        zero_value = VerkleValue(0)
        low, high = zero_value.low_high()
        self.assertEqual(low, VALUE_EXISTS_MARKER)
        self.assertEqual(high, Fr(0))


if __name__ == '__main__':
    unittest.main()
