import pytest

from ai.naive_bot import NaiveBotController
from citadels.cards import Character, District, standard_chars
from citadels import commands
from citadels.gameplay import CommandsSink

from fixtures import *


def standard_chars_but(char: Character):
    return tuple(ch for ch in standard_chars() if ch != char)


@pytest.fixture
def bot():
    return NaiveBotController()


def test_action_is_cash_in_if_low_on_gold(bot, game, king):
    # act
    sink = CommandsSink(king, game)
    command = bot.decide(king, game, sink)

    # assert
    assert isinstance(command, commands.CashIn)


def test_action_is_draw_cards_if_high_on_gold(bot, game, king):
    # arrange
    king.cash_in(6)

    # act
    sink = CommandsSink(king, game)
    command = bot.decide(king, game, sink)

    # assert
    assert isinstance(command, commands.DrawSomeCards)


def test_action_is_cash_in_if_architect(bot, game, architect):
    # arrange
    architect.cash_in(6)

    # act
    sink = CommandsSink(architect, game)
    command = bot.decide(architect, game, sink)

    # assert
    assert isinstance(command, commands.CashIn)


def test_rob_merchant_by_default(bot, game, thief):
    # arrange
    context = bot.create_context(thief, game)

    # act
    sink = CommandsSink(thief, game)
    command = bot.rob(sink.possible_abilities, context, thief, game)

    # assert
    assert command == commands.Rob(char=Character.Merchant)


def test_destroy_lead_player_district(bot, game, warlord, king, thief):
    # arrange
    for _ in range(6):
        king.build_district(District.Docks)

    for _ in range(7):
        thief.build_district(District.Docks)

    context = bot.create_context(warlord, game)

    sink = CommandsSink(warlord, game)
    sink.execute(sink.possible_actions[0])
    assert sink.possible_abilities

    # act
    command = bot.destroy(sink.possible_abilities, context, warlord, game)

    # assert
    assert command == commands.Destroy(target=thief, card=District.Docks)


def test_kill_lead_player_if_he_has_color_bias(bot, game, assassin, player1, player2):
    # arrange
    player1.build_district(District.Cathedral)

    player2.build_district(District.Watchtower)
    player2.build_district(District.Battlefield)
    player2.build_district(District.Fortress)
    player2.build_district(District.Docks)

    context = bot.create_context(assassin, game)

    sink = CommandsSink(assassin, game)

    # act
    command = bot.kill(sink.possible_abilities, context, assassin, game)

    # assert
    assert command == commands.Kill(char=Character.Warlord)


def test_kill_architect_if_lead_player_is_low_on_cards(bot, game, assassin, player1, player2):
    # arrange
    player1.build_district(District.Cathedral)

    player2.build_district(District.Watchtower)
    player2.build_district(District.Docks)
    player2.build_district(District.Cathedral)

    context = bot.create_context(assassin, game)

    sink = CommandsSink(assassin, game)

    # act
    command = bot.kill(sink.possible_abilities, context, assassin, game)

    # assert
    assert command == commands.Kill(char=Character.Architect)


def test_kill_architect_if_anybody_is_low_on_cards(bot, game, assassin, player1, player2):
    # arrange
    player1.take_card(District.Docks)
    player1.take_card(District.Cathedral)
    player1.take_card(District.Watchtower)
    player1.cash_in(3)

    player2.take_card(District.Watchtower)
    player2.cash_in(3)

    context = bot.create_context(assassin, game)

    sink = CommandsSink(assassin, game)

    # act
    command = bot.kill(sink.possible_abilities, context, assassin, game)

    # assert
    assert command == commands.Kill(char=Character.Architect)


def test_kill_merchant_if_anybody_is_low_on_gold(bot, game, assassin, player1, player2):
    # arrange
    player1.cash_in(4)

    context = bot.create_context(assassin, game)

    sink = CommandsSink(assassin, game)

    # act
    command = bot.kill(sink.possible_abilities, context, assassin, game)

    # assert
    assert command == commands.Kill(char=Character.Merchant)


def test_pick_thief_if_everybody_else_has_some_gold(bot, game, player1, player2, player3):
    # arrange
    player1.cash_in(2)
    player2.cash_in(3)

    # act
    char = bot.pick_char(standard_chars(), player3, game)

    # assert
    assert char == Character.Thief


def test_pick_assassin_if_there_is_leader(bot, game, player1, player2, player3):
    # arrange
    for _ in range(6):
        player1.build_district(District.Docks)

    # act
    char = bot.pick_char(standard_chars(), player3, game)

    # assert
    assert char == Character.Assassin


def test_pick_warlord_if_there_is_leader_and_assassin_is_not_available(bot, game, player1, player2, player3):
    # arrange
    for _ in range(6):
        player1.build_district(District.Docks)

    # act
    char = bot.pick_char(standard_chars_but(Character.Assassin), player3, game)

    # assert
    assert char == Character.Warlord


def test_pick_bishop_if_one_district_left_to_build(bot, game, player1):
    # arrange
    for _ in range(7):
        player1.build_district(District.Docks)

    # act
    char = bot.pick_char(standard_chars(), player1, game)

    # assert
    assert char == Character.Bishop


def test_pick_colored_char_if_color_bias(bot, game, player1):
    # arrange
    player1.build_district(District.Docks)
    player1.build_district(District.Watchtower)
    player1.build_district(District.Watchtower)
    player1.build_district(District.Watchtower)

    # act
    char = bot.pick_char([Character.Merchant, Character.King, Character.Warlord, Character.Bishop], player1, game)

    # assert
    assert char == Character.Warlord


def test_pick_architect_if_low_on_cards(bot, game, player1):
    # arrange
    player1.cash_in(2)

    # act
    char = bot.pick_char(standard_chars(), player1, game)

    # assert
    assert char == Character.Architect


def test_pick_magician_if_low_on_cards_and_architect_unavailable(bot, game, player1):
    # arrange
    player1.cash_in(2)

    # act
    char = bot.pick_char(standard_chars_but(Character.Architect), player1, game)

    # assert
    assert char == Character.Magician


def test_do_tricks_swaps_hands_with_the_leader(bot, game, magician, player1, player2):
    # arrange
    for _ in range(6):
        player1.take_card(District.Docks)

    for _ in range(5):
        player2.take_card(District.Docks)
    for _ in range(6):
        player2.build_district(District.Watchtower)

    magician.take_card(District.Cathedral)
    magician.take_card(District.Cathedral)

    context = bot.create_context(magician, game)

    sink = CommandsSink(magician, game)

    # act
    swap_hands = bot.do_tricks(sink.possible_abilities, context, magician, game)

    # assert
    assert swap_hands == commands.SwapHands(target=player2)


def test_do_tricks_swaps_hands_with_the_hoarder_low_on_cards(bot, game, magician, player1):
    # arrange
    for _ in range(6):
        player1.take_card(District.Docks)

    magician.take_card(District.Cathedral)

    context = bot.create_context(magician, game)

    sink = CommandsSink(magician, game)

    # act
    swap_hands = bot.do_tricks(sink.possible_abilities, context, magician, game)

    # assert
    assert swap_hands == commands.SwapHands(target=player1)


def test_do_tricks_replces_hand_if_nothing_to_build(bot, game, magician):
    # arrange
    magician.cash_in(1)

    magician.take_card(District.Palace)
    magician.take_card(District.TownHall)
    magician.take_card(District.Battlefield)

    context = bot.create_context(magician, game)

    sink = CommandsSink(magician, game)

    # act
    replace_hand = bot.do_tricks(sink.possible_abilities, context, magician, game)

    # assert
    assert replace_hand == commands.ReplaceHand(cards=[District.Palace, District.TownHall])
