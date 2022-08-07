from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
from crs.crs import CRS
from ecc import Fr, Banderwagon
from verkle.common_types import VerkleCommitment, bytes32, bytes16, bytes31, byte
from crs import commit
import copy


@dataclass
class VerkleValue:
    # A value is 32 bytes which cannot be uniquely represented in 32 bytes
    value: Optional[bytes32] = None

    def __init__(self, value=None):
        if value is None:
            self.value = value
        elif isinstance(value, bytes):
            if len(value) != 32:
                raise Exception("bytes array must contain 32 elements")
            self.value = value
        elif isinstance(value, int):
            # Check how many bits needed, should be less than 256
            if value.bit_length() > 256:
                raise Exception("cannot represent value in 32 bytes")
            self.value = value.to_bytes(32, 'little')
        elif isinstance(value, List):
            if len(value) != 32:
                raise Exception("list must contain 32 elements")
            # We do not check that the list contains solely integers. This is the
            # Job of the caller.
            self.value = bytes(value)
        else:
            raise Exception(
                "type cannot be converted to a verkle value", type(value))

    def low_high(self):
        # Splits the value into its low and high components
        # and adds the value exists marker to it, if the value exists
        #
        # Note that `from_bytes_reduce` is not being used. If the low and high 16 bytes when interpreted
        # as an integer, needs a reduction, then this is a bug.
        if self.value is None:
            return (0, 0)
        else:

            low, high = split_bytes32(self.value)

            low_fr = Fr.from_bytes(low) + VALUE_EXISTS_MARKER
            high_fr = Fr.from_bytes(high)

            return (low_fr, high_fr)


# TODO: We could create a bytes32 class which solely holds a 32 byte array and
# then add methods on top of it
def split_bytes32(byts: bytes32) -> Tuple[bytes16, bytes16]:
    assert len(byts) == 32
    return (byts[:16], byts[16:])


# Pedersen commitments have the feature that commitment to 0 is the same
# as not commitment to nothing. ie pedersen_commit(0)== pedersen_commit()
#
#  Note this is not true for other commitment functions such as sha256
# where sha256(0) != sha256()
#
#  We therefore use a value exists marker to distinguish these two cases.
#  Lets first clarify what the two cases are.
# 1. The value was zero
# 2. The value does not exist
# To fix, we simply added a marker to all values which existed.
# It is then clear that pedersen_commit(0 + VALUE_EXISTS_MARKER) != pedersen_commit()
#
# Note that due to us adding a value exists marker, then final number could be 257 bits
# instead of 256 bits.
# TODO: We should add a test case for this edge case, because we cannot add the marker
# TODO: before we have split the values. If this is done, then it is possible
# TODO: to overflow the modulus. We would also end up with a number that is different than if
# TODO:  we were to split first and then add the number to the low 128 bit
#
#  As a sidenote, we simply just need a way to encode whether all values exist or note
# An alternative strategy would have been to create a separate field element whose bits are
# set to one, if the value was present, and then add that to the commitment
#
#  Note: This is an internal detail of the verkle trie and so external users
# will not need or ever be aware of this marker
VALUE_EXISTS_MARKER = Fr(2**128)


@dataclass
class SuffixTree:
    # Stem. This is 31 bytes
    stem: bytes31
    # If we change this to Dict[byte, Value], we need to change this line:VerkleValue(self.values[child_idx])
    values: Dict[byte, VerkleValue]
    C1: VerkleCommitment = VerkleCommitment.empty()
    C2: VerkleCommitment = VerkleCommitment.empty()
    # Commitment to the extension
    extension_commitment: VerkleCommitment = VerkleCommitment.empty()

    # Computing suffix commitment consists of committing to
    # 256 values. Each of these values are 256 bytes.
    #
    # Because we are using pedersen commitments, this function has added complexity.
    #
    # These complexities disappear, if we use sha256 as the commitment function,
    # however sha256 is not snark friendly.
    # Note: It may be the case that sha256 is good enough, if proofs will only be made
    # by powerful entities, like block builders. (TODO: More investigation will be needed here to justify)
    #
    # Now since we are using pedersen commitments, the values will need to be interpreted as field elements
    # This essentially means that the value will be taken modulo an odd prime.
    # This causes problems if the value is more than the prime because then two different values may
    # not produce different commitments.
    #
    #  As an example, imagine our prime was 5, and we are given two values 4 and 9.
    # 4 mod 5 is 4, and 9 mod 5 is 4, so these two values will be seen as the same field element.
    # To fix this, we simply need to ensure that our values are never more than the prime number.
    # Then each value has a unique representation.
    #
    # In our case, the prime is ~255 bits and our values can be 256 bits.
    # To ensure that no value is more than prime, we split each value into 128 bit values
    # ie we split the value into its low 128 bits v_lo and its high 128 bit v_high.
    # We then interpret v_low and v_high as separate field elements which cannot be larger than
    # the prime, since the prime is ~255 bits.
    # TODO: rename to compute_metadata?
    def compute_commitment(self, committer: Callable[[Dict[byte, Fr]], VerkleCommitment]):
        values_c1 = {}
        values_c2 = {}

        for index, value in self.values.items():
            val_low, val_high = value.low_high()

            idx_low = (2 * index) % 256
            idx_high = (2 * index + 1) % 256

            if index < 128:
                values_c1[idx_low] = val_low
                values_c1[idx_high] = val_high
            else:
                values_c2[idx_low] = val_low
                values_c2[idx_high] = val_high

        self.C1 = committer(values_c1)
        self.C2 = committer(values_c2)

        c1_field = self.C1.commitment_to_field()
        c2_field = self.C2.commitment_to_field()

        self.extension_commitment = committer({
            0: Fr.one(),
            1: Fr.from_bytes(self.stem),
            2: c1_field,
            3: c2_field})

        self.extension_commitment.commitment_to_field()

    # This means that we need to update one of the child nodes
    def replace_child_element(self, child_idx: byte, _new_value: bytes32, crs: CRS):
        if _new_value is None:
            raise Exception(
                "Updating a child with None (removing the node). This type of (deletion) is not a supported action.")

        # First fetch the old value, if it was present
        # Will be none if it was not
        old_value = VerkleValue()
        if child_idx in self.values:
            old_value = self.values[child_idx]

        old_val_lower, old_val_higher = old_value.low_high()
        new_value = VerkleValue(_new_value)
        new_val_lower, new_val_higher = new_value.low_high()

        # TODO: Use node width instead of hardcoded 256
        comm_index_lower = (2 * child_idx) % 256
        comm_index_higher = (2 * child_idx + 1) % 256

        comm_lower = crs[comm_index_lower]
        comm_higher = crs[comm_index_higher]

        delta_lower_change = new_val_lower - old_val_lower
        delta_higher_change = new_val_higher - old_val_higher

        commitment_change = commit([comm_lower, comm_higher], [
                                   delta_lower_change, delta_higher_change])

        # Now need to update C1 or C2
        # TODO: Use node width / 2 instead of hardcoded 128
        # This value is determined by halving the number of possible values for a stem
        if child_idx < 128:
            self._update_c1(commitment_change, crs)
        else:
            self._update_c2(commitment_change, crs)

    def _update_c1(self, commitment_change: Banderwagon, crs: CRS):
        C1_INDEX = 2
        self._update_c1_or_c2(commitment_change, self.C1, crs[C1_INDEX])

    def _update_c2(self, commitment_change: Banderwagon, crs: CRS):
        C2_INDEX = 3
        self._update_c1_or_c2(commitment_change, self.C2, crs[C2_INDEX])

    def _update_c1_or_c2(self, commitment_change: Banderwagon, C_commitment: VerkleCommitment, C_group_element: Banderwagon):

        old_c_field = C_commitment.commitment_to_field()
        C_commitment.add_point(commitment_change)
        new_c_field = C_commitment.commitment_to_field()

        delta_c_change = new_c_field - old_c_field
        commitment_change = C_group_element * delta_c_change

        self.extension_commitment.add_point(commitment_change)

    # TODO: rename to node_hash
    def commitment_to_field(self):
        return copy.deepcopy(self.extension_commitment.commitment_to_field())

    # TODO: rename to node_commitment
    def commitment(self):
        return copy.deepcopy(self.extension_commitment)

    def __getitem__(self, index):
        return self.values[index]

    def __setitem__(self, i, elem):
        if isinstance(elem, VerkleValue) == False:
            raise Exception("element is not a verkle value", elem)
        self.values[i] = elem

    def contains_index(self, index):
        if index in self.values:
            return True
        return False
