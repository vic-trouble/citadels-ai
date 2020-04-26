from citadels import commands


def possible_actions():
    """ Normal per-turn actions: MYTURN-TAKE-OR-DRAW """
    return [commands.CashIn(2), commands.DrawCards(draw=2, keep=1)]
