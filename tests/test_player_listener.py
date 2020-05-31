from unittest.mock import Mock
import pytest

from citadels.cards import Character, District
from citadels.game import Player

from fixtures import game, player


@pytest.fixture
def listener(player):
    listener = Mock()
    player.add_listener(listener)
    return listener


def test_cashed_in(player, listener):
    # assert
    cashed_in_amount = None

    def save_cashed_in(player: Player, amount: int, source: str):
        nonlocal cashed_in_amount
        cashed_in_amount = amount

    listener.cashed_in = Mock(side_effect=save_cashed_in)

    # act
    player.cash_in(10)

    # assert
    assert cashed_in_amount == 10


def test_withdrawn(player, listener):
    # assert
    withdrawn_amount = None

    def save_withdrawn(player: Player, amount: int):
        nonlocal withdrawn_amount
        withdrawn_amount = amount

    listener.withdrawn = Mock(side_effect=save_withdrawn)

    player.cash_in(10)

    # act
    player.withdraw(5)

    # assert
    assert withdrawn_amount == 5


def test_picked_char(player, listener):
    # arrange
    picked_char = None

    def save_picked_char(player, char):
        nonlocal picked_char
        picked_char = char

    listener.picked_char = Mock(side_effect=save_picked_char)

    # act
    player.char = Character.King

    # assert
    assert picked_char == Character.King


def test_taken_card(player, listener):
    # arrange
    taken_card = None

    def save_taken_card(player, card):
        nonlocal taken_card
        taken_card = card

    listener.taken_card = Mock(side_effect=save_taken_card)

    # act
    player.take_card(District.Watchtower)

    # assert
    assert taken_card == District.Watchtower


def test_removed_card(player, listener):
    # arrange
    removed_card = None

    def save_removed_card(player, card):
        nonlocal removed_card
        removed_card = card

    listener.removed_card = Mock(side_effect=save_removed_card)

    player.take_card(District.Watchtower)

    # act
    player.remove_card(District.Watchtower)

    # assert
    assert removed_card == District.Watchtower


def test_district_built(player, listener):
    # arrange
    built_district = None

    def save_built_district(player, district):
        nonlocal built_district
        built_district  = district

    listener.district_built = Mock(side_effect=save_built_district)

    # act
    player.build_district(District.Watchtower)

    # assert
    built_district == District.Watchtower


def test_district_lost(player, listener):
    # arrange
    destroyed_district = None

    def save_destroyed_district(player, district):
        nonlocal destroyed_district
        destroyed_district = district

    listener.district_lost = Mock(side_effect=save_destroyed_district)

    player.build_district(District.Watchtower)

    # act
    player.destroy_district(District.Watchtower)

    # assert
    destroyed_district == District.Watchtower
