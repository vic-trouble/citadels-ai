from citadels.cards import Deck


def test_take_from_top():
    # arrange
    deck = Deck([0, 1, 2, 3])

    # act
    card = deck.take_from_top()

    # assert
    assert card == 0
    assert deck.cards == [1, 2, 3]


def test_put_on_bottom():
    # arrange
    deck = Deck([0, 1, 2, 3])

    # act
    deck.put_on_bottom(4)

    # assert
    assert deck.cards == [0, 1, 2, 3, 4]


def test_shuffle():
    # arrange
    deck = Deck([0, 1, 2, 3])

    # act
    deck.shuffle()

    # assert
    assert deck.cards != [0, 1, 2, 3]
    assert sorted(deck.cards) == [0, 1, 2, 3]
