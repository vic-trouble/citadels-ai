from citadels.cards import Character, District, DistrictInfo
from citadels.game import Game, Player
from citadels import commands


def possible_actions():
    """ Normal per-turn actions: MYTURN-TAKE-OR-DRAW """
    return [commands.CashIn(2), commands.DrawCards(draw=2, keep=1)]


class CharacterWorkflow:
    def __init__(self, char: Character):
        compulsory = commands.Restriction.Compulsory
        self.abilities = {
            Character.Assassin: [commands.Kill()],
            Character.Thief: [commands.Rob()],
            Character.Magician: [commands.SwapHands(), commands.ReplaceHand()],
            #Character.King: [commands.TakeCrown(restriction=commands.Restriction.OnStartTurn|compulsory)], # TODO: ?
            Character.Merchant: [commands.CashIn(1, restriction=commands.Restriction.OnAfterAction|compulsory)],  # MERCHANT-GOLD
            Character.Architect: [commands.DrawCards(draw=2, keep=2, restriction=commands.Restriction.OnAfterAction|compulsory)],  # ARCHITECT-DRAW2
            Character.Warlord: [commands.Destroy(restriction=commands.Restriction.OnEndTurn)],
        }.get(char, [])


def how_much_cost_to_build(district: District, player: Player):
    return DistrictInfo(district).cost


def how_many_districts_can_build(player: Player):
    # ARCHITECT-BUILD3
    return 3 if player.char == Character.Architect else 1


def is_city_complete(player: Player):
    # END-BUILD8
    return len(player.city) == 8


def can_be_built(district: District, player: Player):
    # BUILD-NO-DUPS
    return district not in player.city


def can_be_destroyed(district: District, owner: Player):
    # BISHOP-PROTECT
    return owner.char != Character.Bishop
