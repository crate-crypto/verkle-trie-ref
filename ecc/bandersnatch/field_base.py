from ..field import Field

# This is the basefield assosciated with the bandersnatch curve
BASE_FIELD = 52435875175126190479447740508185965837690552500527637822603658699938581184513

# (p-1)/2
Q_MIN_ONE_DIV_2 = (BASE_FIELD - 1) // 2

BYTE_LEN = 32


class Fp(Field):
    def __init__(self, value=None, generic_field=None):
        if generic_field is not None:
            assert generic_field.modulus == BASE_FIELD
            super().__init__(generic_field.value, BASE_FIELD)
            return

        super().__init__(value, BASE_FIELD)

    def zero():
        return Fp(None, Field.zero(BASE_FIELD))

    def one():
        return Fp(None, Field.one(BASE_FIELD))

    def from_bytes(bytes):
        return Fp(None, Field.from_bytes(bytes, BASE_FIELD))

    def from_bytes_reduce(bytes):
        return Fp(None, Field.from_bytes_reduce(bytes, BASE_FIELD))

    def to_bytes(self):
        return super().to_bytes(BYTE_LEN)

    def lexographically_largest(self):
        return super().lexographically_largest(Q_MIN_ONE_DIV_2)

    def multi_inv(values):
        result = []
        inverses = Field.multi_inv(values)
        for inv in inverses:
            result.append(Fp(None, inv))
        return result

    def __add__(self, other):
        return Fp(None, super().__add__(other))

    def __sub__(self, other):
        return Fp(None, super().__sub__(other))

    def __mul__(self, other):
        return Fp(None, super().__mul__(other))

    def __neg__(self):
        return Fp(None, super().__neg__())

    def __truediv__(self, other):
        return Fp(None, super().__truediv__(other))
