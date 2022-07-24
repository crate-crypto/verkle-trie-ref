import unittest
from twedards import BandersnatchAffinePoint
from field_scalar import Fr


class TestBandersnatchTwedwardsMethods(unittest.TestCase):

    def test_addition(self):

        result_add = BandersnatchAffinePoint.identity()
        gen = BandersnatchAffinePoint.generator()
        result_add.add(gen, gen)

        result_double = BandersnatchAffinePoint.identity()
        result_double.double(gen)

        assert result_add == result_double

    def test_eq(self):

        neg_gen = BandersnatchAffinePoint.identity()
        gen = BandersnatchAffinePoint.generator()
        neg_gen.neg(gen)

        assert gen == gen
        assert gen != neg_gen

    def test_neg(self):

        gen = BandersnatchAffinePoint.generator()
        result = BandersnatchAffinePoint.generator()
        neg_gen = BandersnatchAffinePoint.generator()

        neg_gen.neg(gen)

        result.add(neg_gen, gen)

        expected = BandersnatchAffinePoint.identity()

        assert expected == result

    def test_serialise_gen(self):
        gen = BandersnatchAffinePoint.generator()
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
        gen = BandersnatchAffinePoint.generator()
        result = BandersnatchAffinePoint.identity()

        scalar = Fr(2)
        result.scalar_mul(gen, scalar)

        twoG = BandersnatchAffinePoint.generator()
        twoG.double(gen)

        assert twoG.to_bytes().hex() == result.to_bytes().hex()

    def test_scalar_mul_minus_one(self):

        gen = BandersnatchAffinePoint.generator()
        result = BandersnatchAffinePoint.identity()

        integer = -1

        scalar = Fr(integer)
        result.scalar_mul(gen, scalar)

        assert "e951ad5d98e7181e99d76452e0e343281295e38d90c602bf824892fd86742c4a" == result.to_bytes().hex()


if __name__ == '__main__':
    unittest.main()
