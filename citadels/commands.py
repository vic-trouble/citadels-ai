from citadels.game import Game, Player


class Command:
    def apply(self, player: Player, game: Game):
        raise NotImplementedError()


class CashIn(Command):
    def __init__(self, amount):
        self._amount = amount

    def apply(self, player: Player, game: Game):
        player.cash_in(self._amount)


class DrawCards(Command):
    def __init__(self, draw=2, keep=1):
        self._draw = draw
        self._keep = keep  # TODO: not implemented :(

    def apply(self, player: Player, game: Game):
        for _ in range(self._draw):
            player.hand.append(game.districts.take_from_top())
