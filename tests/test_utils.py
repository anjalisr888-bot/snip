from app.utils import encode, decode


def test_encode_zero():
    assert encode(0) == "0"


def test_encode_61():
    assert encode(61) == "Z"


def test_encode_62():
    assert encode(62) == "10"


def test_round_trip():
    for n in [0, 1, 61, 62, 125, 1_000_000, 10**12]:
        assert decode(encode(n)) == n
        