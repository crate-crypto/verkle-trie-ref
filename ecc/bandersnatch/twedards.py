from dataclasses import dataclass
from .field_base import Fp
import copy

from .field_scalar import Fr

A = Fp(-5)

d_num = Fp(138827208126141220649022263972958607803)
d_den = Fp(171449701953573178309673572579671231137)
d_den.inv(d_den)

D = d_num * d_den


# Bandersnatch using affine co-ordinates
@dataclass
class BandersnatchAffinePoint():
    x: Fp
    y: Fp

    def __init__(self,  gx, gy):
        if isinstance(gx, Fp) == False:
            raise Exception(
                "coordinates must have type basefield, please check the x coordinate")
        if isinstance(gy, Fp) == False:
            raise Exception(
                "coordinates must have type basefield, please check the y coordinate")

        self.x = gx
        self.y = gy
        if self.is_on_curve() == False:
            raise Exception("point not on curve")

    def __eq__(self, other):
        if isinstance(other, BandersnatchAffinePoint):
            return self.x.value == other.x.value and self.y.value == other.y.value
        return NotImplemented

    def generator():
        # Generator point was taken from the bandersnatch paper: https://ia.cr/2021/1152
        yTe = Fp(0x2a6c669eda123e0f157d8b50badcd586358cad81eee464605e3167b6cc974166)
        xTe = Fp(0x29c132cc2c0b34c5743711777bbe42f32b79c022ad998465e1e71866a252ae18)
        return BandersnatchAffinePoint(xTe, yTe)

    def neg(self, p):
        self.y = p.y
        self.x = -p.x

    def add(self, p, q):

        x1 = p.x
        y1 = p.y
        x2 = q.x
        y2 = q.y

        one = Fp(1)

        x1y2 = x1 * y2

        y1x2 = y1 * x2
        ax1x2 = x1 * x2 * A
        y1y2 = y1 * y2

        dx1x2y1y2 = x1y2 * y1x2 * D

        x_num = x1y2 + y1x2

        x_den = one + dx1x2y1y2

        y_num = y1y2 - ax1x2

        y_den = one - dx1x2y1y2

        x = x_num / x_den

        y = y_num / y_den

        self.x = x
        self.y = y

        return self

    def double(self, p):
        return self.add(p, p)  # TODO: add dedicated doubling formula

    def is_on_curve(self):
        x_sq = self.x * self.x
        y_sq = self.y * self.y

        dxy_sq = x_sq * y_sq * D
        a_x_sq = A * x_sq

        one = Fp(1)

        rhs = one + dxy_sq
        lhs = a_x_sq + y_sq

        return lhs == rhs

    def to_bytes(self):
        # This is here to test that we have the correct generator element
        # banderwagon uses a different serialisation algorithm
        mCompressedNegative = 0x80
        mCompressedPositive = 0x00

        x_bytes = bytearray(self.x.to_bytes())

        mask = mCompressedPositive
        if self.y.lexographically_largest():
            mask = mCompressedNegative

        x_bytes[31] |= mask

        return bytes(x_bytes)

    def from_bytes(self):
        # This is not needed, see `to_bytes`
        return NotImplemented

    def dup(self):
        return copy.deepcopy(self)

    def scalar_mul(self, point, scalar: Fr):
        # using double and add : https://en.wikipedia.org/wiki/Elliptic_curve_point_multiplication#Double-and-add
        scalar_bits = format(scalar.value, 'b')

        result = BandersnatchAffinePoint.identity()
        temp = point.dup()

        num_bits = len(scalar_bits)

        for i in reversed(range(num_bits)):
            if scalar_bits[i] == str(1):
                result.add(result, temp)
            temp.double(temp)

        self.x = result.x
        self.y = result.y

        return self

    def identity():
        zero = Fp(0)
        one = Fp(1)
        return BandersnatchAffinePoint(zero, one)

    def get_y_coordinate(x, return_positive_y):

        one = Fp.one()

        num = x * x

        den = (num * D) - one

        num = (num * A) - one

        y = num / den  # y^2

        # This can only be None if the denominator is zero
        if y is None:
            return None

        y.sqrt(y)
        # This means that the square root does not exist
        if y is None:
            return None

        is_largest = y.lexographically_largest()
        if return_positive_y == is_largest:
            return y
        else:
            return -y

# # TODO add the extended formulas for better efficiency


# class ExtendedProjPoint():
#     def __init__(self, curve_params, gx, gy) -> None:
#         pass

#     def from_affine(self, affine):
#         pass

#     def identity(self):
#         return super().identity()
