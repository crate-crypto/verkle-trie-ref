
# Alias for different byte sizes that we use
from dataclasses import dataclass
from typing import Optional
from ecc import Fr, Banderwagon
from ssz import Byte
import copy

bytes31 = bytes
bytes32 = bytes
bytes16 = bytes
byte = Byte


@dataclass
class VerkleCommitment:
    _point: Banderwagon
    _point_as_field: Optional[Fr] = None

    def empty():
        return copy.deepcopy(VerkleCommitment(Banderwagon.identity()))

    # TODO: should we call this compute_hash?
    def commitment_to_field(self) -> Fr:
        if self._point_as_field is None:
            # Map the point to base field and then take the field's serialisation modulo the scalar field
            map_to_bytes = self._point.map_to_field_bytes()
            self._point_as_field = Fr.from_bytes_reduce(map_to_bytes)
        return self._point_as_field

    def add_point(self, point:  Banderwagon):
        self._point.add(self._point, point)
        self._point_as_field = None
        self.commitment_to_field()
