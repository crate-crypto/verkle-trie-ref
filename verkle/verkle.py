from crs import commit
from crs.crs import CRS
from ecc import Banderwagon, Fr
from typing import Dict, List
from verkle.nodes import InnerNode, SuffixTree, VerkleValue
from .common_types import VerkleCommitment

# Verkle trie parameters
# This is fixed just to make the algorithm simpler. It is possible to have a generic algorithm
# But we gain nothing from the added complexity
#
#  We should properly define terms such as node width etc
KEY_LENGTH = 256  # bits
WIDTH_BITS = 8
WIDTH = 2**WIDTH_BITS

# A verkle trie struct which stores all of the logic for the trie


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
# TODO: we can put this on a stem class
def path_diff(stem_a, stem_b):
    same_path = []
    for sa, sb in zip(stem_a, stem_b):
        if sa == sb:
            same_path.append(sa)
        else:
            return (same_path, (sa, sb))
    return (same_path, None)


# There are two different ways to use the verkle trie api
#  and so there will be two different APIs.
#
#  The first method is for when you want to update a large batch of keys
#  It may be advantageous here, to only update the commitments once all of the new keys have been inserted into the
# trie. This may only be advantageous if one is starting from an empty trie.
#
# The second method is for when you want to update a moderate or small number of keys
# For this we can use the delta commitment to update the specific spots in which the keys were updated


class VerkleTrie():
    # TODO: We could probably get rid of the commit_sparse function and replace group_elements with the SRS struct
    def __init__(self,  crs: CRS):
        self.crs = crs
        self.root_node = InnerNode.empty()

    # This is the same as the update verkle tree method
    def insert_old(self, key, value):
        current_node = self.root_node
        index = None
        path = []
        stem = get_stem(key)
        suffix = get_suffix(key)
        # TODO: have a thing here which does while index in current_node and its an inner node, we traverse down the tree
        while True:
            index = stem[len(path)]
            path.append((index, current_node))

            if current_node.contains_index(index) and isinstance(current_node, InnerNode):
                #  Keep traversing inner nodes
                current_node = current_node[index]
            else:
                break

        # Check if the index is in the current node, which means it is an insert and not an update
        value_change = None

        # Check whether the current node is a suffix tree
        # If so, we are either going to:
        # 1) update the value in it, if the stems match
        # 2) or we are going to add inner nodes to extend the trie, for where the stems match
        if isinstance(current_node, SuffixTree):
            # Case 1
            if current_node.stem == stem:
                print("CASE 1")

                # Pop off the suffix tree node from the path because we are going to process it here in place
                # Hence, there will be no need to process it in the for loop below
                # TODO: Is there a better alternative, as this seems quite ad-hoc
                # TODO: Maybe we can merge everything into the for loop below?
                path.pop()

                old_extension_field_value = current_node.commitment_to_field()
                current_node.replace_child_element(
                    suffix, value, self.crs)
                new_extension_field_value = current_node.commitment_to_field()

                value_change = Fr(0).sub(
                    new_extension_field_value, old_extension_field_value)

            # Case 2
            else:
                # We want to remove the suffix tree and
                path.pop()
                index, current_node = path[-1]

                # TODO : NEED to look over this and put it in a separate method like suffix tree has
                old_node = current_node[index]
                old_node_field = old_node.commitment_to_field()
                old_index = old_node.stem[index]

                new_inner_node = InnerNode.empty()
                new_index = stem[index]

                current_node[index] = new_inner_node
                inserted_path = []
                current_node = new_inner_node
                while old_index == new_index:

                    index = new_index
                    next_inner_node = InnerNode.empty()
                    current_node[index] = next_inner_node
                    inserted_path.append((index, current_node))
                    new_index = stem[len(path) + len(inserted_path)]
                    old_index = old_node.stem[len(
                        path) + len(inserted_path)]
                    current_node = next_inner_node

                values = {suffix: VerkleValue(value)}
                current_node[new_index] = SuffixTree(
                    stem, values)
                current_node[old_index] = old_node

                # Reverse up the tree for the nodes we just extended
                current_node.compute_commitment(self.commit_sparse)
                for index, node in reversed(inserted_path):
                    node.compute_commitment(self.commit_sparse)

                value_change = Fr(0).sub(
                    new_inner_node.commitment_to_field(), old_node_field)

        elif isinstance(current_node, InnerNode):

            # This should not be possible due to the while loop above
            assert(current_node.contains_index(index) == False)

            # Here the index is not in the current node, so we can simply add a suffix tree here
            values = {suffix: VerkleValue(value)}
            suffix_tree = SuffixTree(stem, values)

            suffix_tree.compute_commitment(self.commit_sparse)
            value_change = suffix_tree.commitment_to_field()
            current_node[index] = suffix_tree

        for index, node in reversed(path):
            old_field = node.commitment_to_field()

            comm_delta = Banderwagon.identity()
            comm_delta.scalar_mul(self.crs[index], value_change)
            node.commitment().add_point(comm_delta)

            new_field = node.commitment_to_field()

            value_change.sub(new_field, old_field)

    def insert(self, key, value):
        current_node = self.root_node
        index = None
        path = []
        stem = get_stem(key)
        suffix = get_suffix(key)

        #  Iterate down the path given by the stem, stopping if the current_node/parent is a suffix tree or
        #  if the inner node does not have an element at the child which you will go to next
        # TODO: have a thing here which does while index in current_node and its an inner node, we traverse down the tree
        while True:
            index = stem[len(path)]
            old_root_value = current_node.commitment_to_field()
            path.append((index, old_root_value, current_node))

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

        # TODO: better name, last_child_node_value_change?
        last_node_value_change = None
        # So this means that we have entered case 1
        # The suffix node at the end of the path, is the current node
        if isinstance(current_node, SuffixTree):
            # Case 1a, there are no other nodes to add to the path
            if current_node.stem == stem:
                index, old_root_value, suffix_node = path.pop()
                old_root_value = suffix_node.commitment_to_field()
                suffix_node.replace_child_element(
                    suffix, value, self.crs)
                new_root_value = suffix_node.commitment_to_field()

                last_node_value_change = Fr(0).sub(
                    new_root_value, old_root_value)

            # We need to create intermediate inner nodes to add to the path
            # For the indices that the new stem and the old stem match on
            else:
                # We want to remove the old suffix tree from the path
                _, old_root_val, old_suffix_tree = path.pop()
                child_index, _, parent_node = path[-1]

                # This is the inner node that replaces the old suffix tree
                # Note: Its old root value will be the root value for the suffix tree
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
                        (same_index, old_root_val, parent_node))

                    parent_node = intermediate_node
                    old_root_val = Fr(0)

                old_index, new_index = diff_index

                values = {suffix: VerkleValue(value)}
                parent_node[new_index] = SuffixTree(
                    stem, values)
                parent_node[old_index] = old_suffix_tree

                # We pop off the last inner node, so that we can compute its change in value
                # We know that this inner node, is an intermediate node
                # whose previous value was zero because the above for loop must have
                # looped at least once
                index, old_root_value, last_node = path.pop()
                last_node.compute_commitment(self.commit_sparse)
                last_node_value_change = Fr(0).sub(
                    last_node.commitment_to_field(), old_root_value)

        elif isinstance(current_node, InnerNode):
            # Here the index is not in the current node, so we can simply add a suffix tree here
            values = {suffix: VerkleValue(value)}
            suffix_tree = SuffixTree(stem, values)

            suffix_tree.compute_commitment(self.commit_sparse)
            last_node_value_change = suffix_tree.commitment_to_field()
            current_node[index] = suffix_tree

        else:
            raise Exception("Unknown node type. This is a bug.")

        # Now We should have a list of path elements (child_index, old_parent_root_value, parent_node)
        # We iterate from the bottom of the path to the root_node, computing the difference in commitment value
        # for the parent, based on the change in the child's value
        for index, old_root_value, node in reversed(path):

            # Compute the change in this nodes commitment according to the
            # change in its child at index `index`
            comm_delta = Banderwagon.identity()
            comm_delta.scalar_mul(
                self.crs[index], last_node_value_change)
            node.commitment().add_point(comm_delta)

            # Compute the new "hash" or commitment_to_field value
            new_root_value = node.commitment_to_field()
            last_node_value_change.sub(new_root_value, old_root_value)

    # TODO: This doesn't belong here, we want to eventually only import the CRS
    def commit_sparse(self, values: Dict[int, Fr]) -> VerkleCommitment:
        return VerkleCommitment(self.crs.commit_sparse(values))

    def insert_batch(self, keys, values):
        # TODO: Initially just make this call the insert method multiple times
        # It can be optimised by inserting the values first and then computing commitments after
        # For an empty tree its quite simple. For non-empty trees, we need to have a flag for which nodes have changed
        for key, value in zip(keys, values):
            self.insert(key, value)

    def insert_batch_from_empty(keys, values):
        pass

    def create_proof(keys, values):
        pass

    def verify_proof(proof):
        pass

    def _is_empty(self):
        return len(self.root_node.children.values()) == 0

    def root(self):
        # TODO: This does not look like a good way to access this.
        # TODO: Can we make this nicer?
        return self.root_node.commitment()._point.to_bytes()
