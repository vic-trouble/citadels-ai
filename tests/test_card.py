import pytest

from citadels.cards import Card


class Payload:
    def __init__(self, data):
        self.data = data


def test_card_should_wrap_containee():
    # arrange
    payload = Payload(42)

    # act
    card = Card(payload)

    # assert
    assert card.data == 42

    card.data = 43
    assert card.data == 43


def test_card_should_nullify_containee_when_facedown():
    # arrange
    payload = Payload(42)

    # act
    card = Card(payload).facedown

    # assert
    assert card.data is None


def test_card_should_still_raise_on_unknown_attr_when_facedown():
    # arrange
    payload = Payload(42)

    # act
    card = Card(payload).facedown

    # assert
    with pytest.raises(AttributeError):
        card.something


def test_card_should_wrap_primitive_type():
    # arrange
    s = 'str'

    # act
    card = Card(s).facedown

    # assert
    assert not card


def test_card_faceup_equality():
    assert Card(42) == Card(42)
    assert Card(42) != Card(43)


def test_card_facedown_equality():
    assert Card(42).facedown != Card(42)
    assert Card(42).facedown == Card(43).facedown
