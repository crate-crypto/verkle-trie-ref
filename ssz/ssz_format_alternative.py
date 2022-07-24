
# See: https://notes.ethereum.org/Si5tEWlMTYerkhG3fOIAMQ
# This is the alternative version with bitfield
#
from ssz import Container
# TODO: When should one use uint8 vs Byte?
from ssz import bytes32, ByteVector, Byte, List, Vector, uint8, Bitvector, Bitlist
from typing import Union

bytes31 = ByteVector(31)
Stem = bytes31

BandersnatchGroupElement = bytes32
BandersnatchFieldElement = bytes32
Stem = bytes31

MAX_STEMS = 2**16
MAX_COMMITMENTS_PER_STEM = 33  # = 31 for inner nodes + 2 (C1/C2)
VERKLE_WIDTH = 256
IPA_PROOF_DEPTH = 8  # = log2(VERKLE_WIDTH)


class SuffixStateDiff(Container):
    suffix: Byte

    # None means not currently present
    current_value: Union[None, bytes32]

    # None means value not updated
    new_value: Union[None, bytes32]


class StemStateDiff(Container):
    stem: Stem

    # Suffixes can be either a list of bytes or a Bitvector
    # List of bytes MUST be used if <=31 suffixes are present.
    # The list MUST be sorted starting with the smallest index
    suffixes: Union[List[Byte, 31], Bitvector[VERKLE_WIDTH]]

    # Each bit in the bitlist represents one of the suffixes in `suffixes`
    # 0: The suffix is currently not present/has never been written
    # 1: The suffix is present.
    current_values_present: Bitlist[VERKLE_WIDTH]
    # Values for all the present suffixes
    current_values: List[bytes32, VERKLE_WIDTH]

    # Each bit in the bitlist represents one of the suffixes in `suffixes`
    # 0: The value for the suffix was not updated
    # 1: The value for the suffix was updated
    values_updated: Bitlist[VERKLE_WIDTH]
    # New values for all suffixes that were updated
    new_values: List[bytes32, VERKLE_WIDTH]

    suffix_diffs: List[SuffixStateDiff, VERKLE_WIDTH]


# Valid only if list is sorted by stems
StateDiff = List[StemStateDiff, MAX_STEMS]


class IpaProof(Container):
    C_L = Vector[BandersnatchGroupElement, IPA_PROOF_DEPTH]
    C_R = Vector[BandersnatchGroupElement, IPA_PROOF_DEPTH]
    final_evaluation = BandersnatchFieldElement


class VerkleProof(Container):
    other_stems: List[bytes32, MAX_STEMS]
    depth_extension_present: List[uint8, MAX_STEMS]
    commitments_by_path: List[BandersnatchGroupElement,
                              MAX_STEMS * MAX_COMMITMENTS_PER_STEM]
    D: BandersnatchGroupElement
    ipa_proof: IpaProof


class ExecutionWitness(Container):
    state_diff: StateDiff
    verkle_proof: VerkleProof
