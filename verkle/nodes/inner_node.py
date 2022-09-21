from __future__ import annotations
from ast import Bytes
from dataclasses import dataclass
from typing import Callable, Dict, Union
from ecc import Fr
from verkle.common_types import VerkleCommitment
from verkle.nodes.suffix_tree import SuffixTree
import copy


@dataclass
class InnerNode:
    children: Dict[Bytes, Node]
    node_commitment: VerkleCommitment = VerkleCommitment.empty()

    def empty():
        # Without this deepcopy, python will assign all inner nodes whom
        # are instantiated with this empty function, the same address.
        # This is extremely unintuitive behavior and broke tests.
        return copy.deepcopy(InnerNode({}))

    def compute_commitment(self, committer: Callable[[Dict[Bytes, Fr]], VerkleCommitment]):
        child_values = {}

        for child_idx, node in self.children.items():
            node.compute_commitment(committer)
            child_val = node.commitment_to_field()
            child_values[child_idx] = child_val

        self.node_commitment = committer(child_values)
        self.node_commitment.commitment_to_field()

    def __getitem__(self, index):
        return self.children[index]

    def __setitem__(self, i, elem):
        self.children[i] = elem

    def contains_index(self, index):
        if index in self.children:
            return True
        return False

    def is_inner_node(self):
        return True

    # TODO: rename to node_hash
    def commitment_to_field(self):
        return self.node_commitment.commitment_to_field()

    # TODO: rename to node_commitment
    def commitment(self):
        return self.node_commitment


Node = Union[SuffixTree, InnerNode]
