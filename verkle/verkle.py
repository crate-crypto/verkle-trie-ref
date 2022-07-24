from crs.crs import CRS
from ecc import Banderwagon, Fr
from typing import Dict, List
from verkle.nodes import InnerNode, SuffixTree, VerkleValue
from .common_types import VerkleCommitment, bytes32

# Verkle trie parameters
# This is fixed just to make the algorithm simpler. It is possible to have a generic algorithm
# But we gain nothing from the added complexity
#
#  We should properly define terms such as node width etc
KEY_LENGTH = 256  # bits
WIDTH_BITS = 8
WIDTH = 2**WIDTH_BITS


def get_stem(key):
    return key[:31]


def get_suffix(key):
    return key[31]


# Returns a tuple of two elements
# - The first element is a list of the common elements in order
# that both lists share.
# [1,2] and [1,3] would have only 1 as a common element
# [1,2,3] and [3,2,1] would have no common ordered elements
# - The second element is a tuple of the first elements which the two lists
# do not agree at.
def path_diff(stem_a, stem_b):
    same_path = []
    for sa, sb in zip(stem_a, stem_b):
        if sa == sb:
            same_path.append(sa)
        else:
            return (same_path, (sa, sb))
    return (same_path, None)


class VerkleTrie():
    def __init__(self,  crs: CRS):
        self.crs = crs
        self.root_node = InnerNode.empty()

    def insert(self, key: bytes32, value: bytes32):
        current_node = self.root_node
        index = None
        path = []
        stem = get_stem(key)
        suffix = get_suffix(key)

        #  Iterate down the path given by the stem, stopping if the current_node/parent is a suffix tree or
        #  if the inner node does not have an element at the child which you will go to next
        while True:
            index = stem[len(path)]
            old_node_hash = current_node.commitment_to_field()
            path.append((index, old_node_hash, current_node))

            if current_node.contains_index(index) and isinstance(current_node, InnerNode):
                #  Keep traversing inner nodes
                current_node = current_node[index]
            else:
                break

        # The while loop can only be broken on two conditions
        # 1) We encountered a Suffix Tree
        # 2) The current index is not in the node. ie the child at that index is empty
        #
        # Case 1)
        # We have two sub-cases to consider:
        # 1a) The stem matches the suffix tree that we have come across
        # 1b) The stem does not match the suffix tree and we need to extend the path with inner nodes
        #
        # Case 2)
        # If the inner node was empty, then we can add a suffix tree at that index

        last_child_node_value_change = None
        # So this means that we have entered case 1
        # The suffix node at the end of the path, is the current node
        if isinstance(current_node, SuffixTree):
            # Case 1a, there are no other nodes to add to the path
            if current_node.stem == stem:
                index, old_node_hash, suffix_node = path.pop()
                old_node_hash = suffix_node.commitment_to_field()
                suffix_node.replace_child_element(
                    suffix, value, self.crs)
                new_node_hash = suffix_node.commitment_to_field()

                last_child_node_value_change = Fr(0).sub(
                    new_node_hash, old_node_hash)

            # We need to create intermediate inner nodes to add to the path
            # For the indices that the new stem and the old stem match on
            else:
                # We want to remove the old suffix tree from the path
                _, old_node_hash, old_suffix_tree = path.pop()
                child_index, _, parent_node = path[-1]

                # This is the inner node that replaces the old suffix tree
                # Note: Its `old node hash` will be the node hash for the old suffix tree
                suffix_replacement_node = InnerNode.empty()
                parent_node[child_index] = suffix_replacement_node
                parent_node = suffix_replacement_node

                # Stems are offsetted to the point that we are in the path
                old_stem_offset = old_suffix_tree.stem[len(path):]
                new_stem_offset = stem[len(path):]

                # Returns the indices that they both share and the first differing index
                # Since the stems are not the same (Case 1a), we are sure that there will be a differing index
                # We are also sure that there will be at least one index in the common_path, or else we would have triggered
                # a different case
                common_path, diff_index = path_diff(
                    old_stem_offset, new_stem_offset)

                # Create the intermediate inner nodes, for each matching stem index
                # Note: Apart from the suffix_replacement_node, all other nodes
                # will have an old root value of 0
                for same_index in common_path:
                    assert(isinstance(parent_node, InnerNode))

                    intermediate_node = InnerNode.empty()
                    parent_node[same_index] = intermediate_node
                    path.append(
                        (same_index, old_node_hash, parent_node))

                    parent_node = intermediate_node
                    old_node_hash = Fr(0)

                old_index, new_index = diff_index

                values = {suffix: VerkleValue(value)}
                parent_node[new_index] = SuffixTree(
                    stem, values)
                parent_node[old_index] = old_suffix_tree

                # We pop off the last inner node, so that we can compute its change in value
                # We know that this inner node, is an intermediate node
                # whose previous value was zero because the above for loop must have
                # looped at least once
                index, old_node_hash, last_node = path.pop()
                last_node.compute_commitment(self._commit_sparse)
                last_child_node_value_change = Fr(0).sub(
                    last_node.commitment_to_field(), old_node_hash)

        elif isinstance(current_node, InnerNode):
            # Here the index is not in the current node, so we can simply add a suffix tree here
            values = {suffix: VerkleValue(value)}
            suffix_tree = SuffixTree(stem, values)

            suffix_tree.compute_commitment(self._commit_sparse)
            last_child_node_value_change = suffix_tree.commitment_to_field()
            current_node[index] = suffix_tree

        else:
            raise Exception("Unknown node type. This is a bug.")

        # Now We should have a list of path elements (child_index, parent_node_hash_old, parent_node)
        # We iterate from the bottom of the path to the root_node, computing the difference in commitment value
        # for the parent, based on the change in the child's value
        for index, old_node_hash, node in reversed(path):

            # Compute the change in this nodes commitment according to the
            # change in its child at index `index`
            comm_delta = Banderwagon.identity()
            comm_delta.scalar_mul(
                self.crs[index], last_child_node_value_change)
            node.commitment().add_point(comm_delta)

            # Compute the new node_hash
            new_node_hash = node.commitment_to_field()
            last_child_node_value_change.sub(new_node_hash, old_node_hash)

    def _commit_sparse(self, values: Dict[int, Fr]) -> VerkleCommitment:
        return VerkleCommitment(self.crs.commit_sparse(values))

    def insert_batch(self, keys: List[bytes32], values: List[bytes32]):
        # TODO: Initially just make this call the insert method multiple times
        # It can be optimised by inserting the values first and then computing commitments after
        # For an empty tree its quite simple. For non-empty trees, we need to have a flag for which nodes have changed
        for key, value in zip(keys, values):
            self.insert(key, value)

    def create_proof(self, keys: List[bytes32]):
        pass

    def verify_proof(proof):
        pass

    # Returns the root of the trie
    # This is the serialised commitment of the root node
    def root(self):
        return self.root_node.commitment()._point.to_bytes()
