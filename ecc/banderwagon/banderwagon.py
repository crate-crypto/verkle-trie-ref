from __future__ import annotations
from ..bandersnatch.field_base import Fp
import copy
from ..bandersnatch.field_scalar import Fr
from typing import List
from ..bandersnatch.twedards import BandersnatchAffinePoint, A as A_COEFF


class Banderwagon():
    def __init__(self, serialised_bytes_big_endian=None, unsafe_bandersnatch_point=None):
        # Since python does not have the concept of a private constructor
        # We need to use this for points which we internally do not need to check
        # External users of the library SHOULD NEVER use this codepath
        # Inspect below, that it is used to initialise the identity and generator point
        if unsafe_bandersnatch_point is not None:
            self.point = unsafe_bandersnatch_point
            return

        if serialised_bytes_big_endian is None:
            raise Exception(
                "Cannot initialise a banderwagon point without its serialisation")

        xy = Banderwagon.from_bytes(serialised_bytes_big_endian)
        if xy is None:
            return None
        x, y = xy

        self.point = BandersnatchAffinePoint(x, y)

    def __eq__(self, other):
        if isinstance(other, Banderwagon):
            # The equals method is different for the quotient group
            #
            # Check for the (0,0) point, which is _possible_
            # given that you do not need to use the constructor to construct points
            x1 = self.point.x
            y1 = self.point.y
            x2 = other.point.x
            y2 = other.point.y

            if x1.is_zero() and y1.is_zero():
                return False
            if x2.is_zero() and y2.is_zero():
                return False

            lhs = Fp(0)
            lhs.mul(x1, y2)
            rhs = Fp(0)
            rhs.mul(x2, y1)

            return lhs == rhs

        return NotImplemented

    def generator():
        return Banderwagon(None, BandersnatchAffinePoint.generator())

    def neg(self, p):
        self.point.neg(p.point)
        return self

    def add(self, p, q):
        self.point.add(p.point, q.point)
        return self

    # TODO: prepend underscore to let others know that this method is not a part of the public api
    def from_bytes(serialised_bytes_big_endian: bytes):
        # banderwagon can only be instantiated with serialised bytes
        # TODO: we are still using big endian here, so we reverse
        serialised_bytes_little_endian = bytearray(serialised_bytes_big_endian)
        serialised_bytes_little_endian.reverse()

        # Will error if the bytes are not canonical
        x = Fp.from_bytes(serialised_bytes_little_endian)
        if x is None:
            return None

        # Will error if the point is not on the curve
        y = BandersnatchAffinePoint.get_y_coordinate(x, True)
        if y is None:
            return None

        # Will error if x coordinate not a quadratic residue
        if Banderwagon.subgroup_check(x) != 1:
            return None

        return (x, y)

    def map_to_field_bytes(self):
        return self._map_to_field().to_bytes()

    def _map_to_field(self):
        # The map to field function for banderwagon is x/y
        x = self.point.x.dup()
        y = self.point.y.dup()

        x.div(x, y)

        return x

    def subgroup_check(x: Fp):
        # Compute 1 - aX^2 and check its legendre symbol
        res = Fp.zero()
        res.mul(x, x)
        res.mul(res, A_COEFF)
        res.neg(res)
        res.add(res, Fp.one())

        return res.legendre()

    def to_bytes(self):
        x = self.point.x.dup()
        if self.point.y.lexographically_largest() == False:
            x.neg(x)
        bytes_little_endian = x.to_bytes()

        bytes_big_endian = bytearray(bytes_little_endian)
        bytes_big_endian.reverse()

        return bytes_big_endian

    def double(self, p):
        self.point.double(p.point)
        return self

    def is_on_curve(self):
        return self.point.is_on_curve()

    def dup(self):
        return copy.deepcopy(self)

    def scalar_mul(self, element, scalar: Fr):
        self.point.scalar_mul(element.point, scalar)
        return self

    def identity():
        return Banderwagon(None, BandersnatchAffinePoint.identity())

    def two_torsion_point():
        minus_one = Fp.one()
        minus_one.neg(minus_one)
        return Banderwagon(None, BandersnatchAffinePoint(Fp.zero(), minus_one))

    # Multi scalar multiplication
    def msm(points: List[Banderwagon], scalars: List[Fr]):
        res = Banderwagon.identity()
        for scalar, point in zip(scalars, points):
            partial_res = Banderwagon.identity()
            partial_res.scalar_mul(point, scalar)
            res.add(res, partial_res)
        return res
