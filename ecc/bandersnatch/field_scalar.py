from ..field import Field

# This is the scalar field assosciated with the bandersnatch curve
SCALAR_FIELD = 13108968793781547619861935127046491459309155893440570251786403306729687672801

# (p-1)/2
Q_MIN_ONE_DIV_2 = (SCALAR_FIELD - 1) // 2

BYTE_LEN = 32


class Fr(Field):
    def __init__(self, value=None, generic_field=None):
        if generic_field is not None:
            assert generic_field.modulus == SCALAR_FIELD
            super().__init__(generic_field.value, SCALAR_FIELD)
            return

        super().__init__(value, SCALAR_FIELD)

    def zero():
        return Fr(None, Field.zero(SCALAR_FIELD))

    def one():
        return Fr(None, Field.one(SCALAR_FIELD))

    def from_bytes(bytes):
        return Fr(None, Field.from_bytes(bytes, SCALAR_FIELD))

    def from_bytes_reduce(bytes):
        return Fr(None, Field.from_bytes_reduce(bytes, SCALAR_FIELD))

    def to_bytes(self):
        return super().to_bytes(BYTE_LEN)

    def lexographically_largest(x):
        return super().lexographically_largest(Q_MIN_ONE_DIV_2)

    def __add__(self, other):
        return Fr(None, super().__add__(other))

    def __sub__(self, other):
        return Fr(None, super().__sub__(other))

    def __mul__(self, other):
        return Fr(None, super().__mul__(other))

    def __neg__(self):
        return Fr(None, super().__neg__())

    def __truediv__(self, other):
        return Fr(None, super().__truediv__(other))
