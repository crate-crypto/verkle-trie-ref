import unittest
from .twedards import BandersnatchExtendedPoint
from .field_scalar import Fr


class TestBandersnatchTwedwardsMethods(unittest.TestCase):

    def test_addition(self):

        gen = BandersnatchExtendedPoint.generator()
        result_add = gen + gen

        result_double = BandersnatchExtendedPoint.identity()
        result_double.double(gen)

        assert result_add == result_double

    def test_eq(self):

        gen = BandersnatchExtendedPoint.generator()
        neg_gen = - gen

        assert gen == gen
        assert gen != neg_gen

    def test_neg(self):

        gen = BandersnatchExtendedPoint.generator()
        expected = BandersnatchExtendedPoint.identity()

        neg_gen = -gen
        result = neg_gen + gen

        assert expected == result

    def test_serialise_gen(self):
        gen = BandersnatchExtendedPoint.generator()
        serialised_point = gen.to_bytes()

        # test vector taken from the rust code
        # To reproduce:
        # [dependencies]
        # bandersnatch = "0.1.1"
        # use ark_ec::ProjectiveCurve
        # use ark_serialize::CanonicalSerialize
        # let generator = bandersnatch::EdwardsProjective::prime_subgroup_generator()
        # let mut bytes = [0u8;32]
        # generator.serialize(&mut bytes[..]).unwrap()
        # hex::encode(&bytes)
        expected = "18ae52a26618e7e1658499ad22c0792bf342be7b77113774c5340b2ccc32c129"
        assert serialised_point.hex() == expected

    def test_scalar_mul_smoke(self):
        gen = BandersnatchExtendedPoint.generator()

        scalar = Fr(2)
        result = gen * scalar

        twoG = BandersnatchExtendedPoint.generator()
        twoG.double(gen)

        assert twoG == result

    def test_scalar_mul_minus_one(self):

        gen = BandersnatchExtendedPoint.generator()

        integer = -1

        scalar = Fr(integer)
        result = gen * scalar

        assert "e951ad5d98e7181e99d76452e0e343281295e38d90c602bf824892fd86742c4a" == result.to_bytes().hex()


if __name__ == '__main__':
    unittest.main()
