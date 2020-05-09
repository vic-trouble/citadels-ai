import pickle
import pytest

from citadels.cards import Character, Deck, District, simple_districts, standard_chars
from citadels.game import Game


@pytest.fixture
def game():
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())
    return Game(characters, districts)


def test_save_load(game):
    # arrange
    player = game.add_player('Player1')
    player.char = Character.King
    player.cash_in(10)
    player.take_card(District.Docks)
    player.build_district(District.Keep)

    # act
    dump = pickle.dumps(game)

    # assert
    restored = pickle.loads(dump)
    assert len(restored.players) == 1

    r_player = restored.players[0]
    assert r_player.name == 'Player1'
    assert r_player.gold == 10
    assert r_player.hand == (District.Docks,)
    assert r_player.city == (District.Keep,)
