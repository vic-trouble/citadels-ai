from citadels.cards import Character, District, DistrictInfo
from citadels.game import Game, Player
from citadels import commands


def possible_actions():
    """ Normal per-turn actions: MYTURN-TAKE-OR-DRAW """
    return [commands.CashIn(2), commands.DrawCards(draw=2, keep=1)]


class CharacterWorkflow:
    def __init__(self, char: Character):
        self.abilities = {
            Character.Assassin: [commands.Kill()],
            Character.Thief: [commands.Rob()],
            Character.Magician: [commands.SwapHands(), commands.ReplaceHand()],
            Character.Warlord: [commands.Destroy()],
        }.get(char, [])

        self.final = {
            Character.Warlord: [commands.Destroy()],
        } .get(char, [])

        self.after_action_command = {
            Character.Merchant: commands.CashIn(1), # MERCHANT-GOLD
            Character.Architect: commands.DrawCards(draw=2, keep=2), # ARCHITECT-DRAW2
        }.get(char, None)


def how_much_cost_to_build(district: District, player: Player):
    return DistrictInfo(district).cost


def how_many_districts_can_build(player: Player):
    # ARCHITECT-BUILD3
    return player.char == 3 if Character.Architect else 1


def is_city_complete(player: Player):
    # END-BUILD8
    return len(player.city) == 8


def can_be_built(district: District, player: Player):
    # BUILD-NO-DUPS
    return district not in player.city


def can_be_destroyed(district: District, owner: Player):
    # BISHOP-PROTECT
    return owner.char != Character.Bishop
