from citadels.cards import Character, District, DistrictInfo, all_colors
from citadels.game import Game, Player
from citadels import commands


def possible_actions(game: Game):
    """ Normal per-turn actions: MYTURN-TAKE-OR-DRAW """
    actions = [commands.CashIn(2)]
    if len(game.districts) >= 2:
        actions.append(commands.DrawSomeCards(draw=2, keep=1))
    return actions


class CharacterWorkflow:
    def __init__(self, char: Character):
        compulsory = commands.Restriction.Compulsory
        self.abilities = {
            Character.Assassin: [commands.Kill()],
            Character.Thief: [commands.Rob()],
            Character.Magician: [commands.SwapHands(), commands.ReplaceHand()],
            #Character.King: [commands.TakeCrown(restriction=commands.Restriction.OnStartTurn|compulsory)], # TODO: ?
            Character.Merchant: [commands.CashIn(1, restriction=commands.Restriction.OnAfterAction|compulsory)],  # MERCHANT-GOLD
            Character.Architect: [commands.DrawCards(2, restriction=commands.Restriction.OnAfterAction|compulsory)],  # ARCHITECT-DRAW2
            Character.Warlord: [commands.Destroy(restriction=commands.Restriction.OnEndTurn)],
        }.get(char, [])


def how_much_cost_to_build(district: District, player: Player):
    return DistrictInfo(district).cost


def how_much_cost_to_destroy(district: District, player: Player):
    return DistrictInfo(district).cost - 1


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


def score(player: Player, game: Game, with_bonuses=True):
    # SCORE-1
    score = sum(DistrictInfo(district).cost for district in player.city)

    if not with_bonuses:
        return score

    # SCORE-2
    built_colors = set()
    for district in player.city:
        built_colors.add(DistrictInfo(district).color)
    if built_colors == set(all_colors):
        score += 3

    # SCORE-3, SCORE-4
    if is_city_complete(player):
        if game.turn.first_completer == player:
            score += 4
        else:
            score += 2

    return score
