from copy import deepcopy

from citadels.cards import Card, Deck
from citadels.game import Game, Player, PlayersProxy, Turn


class ShadowTurn:
    """ Read-only copy of Turn hiding all private info for passing into bot's controller """

    def __init__(self, turn: Turn):
        self.unused_chars = turn.unused_chars
        self.killed_char = turn.killed_char
        self.robbed_char = turn.robbed_char


class ShadowPlayer:
    """ Read-only copy of Player hiding all private info for passing into bot's controller """

    def __init__(self, player: Player, me=False):
        self.player_id = player.player_id
        self.gold = player.gold
        self.name = player.name
        self.hand = [district if me else Card(district).facedown for district in player.hand]
        self.char = player.char
        self.city = player.city

    def __eq__(self, other):
        if not isinstance(other, ShadowPlayer) and not isinstance(other, Player):
            return False
        return (self.player_id, self.gold, self.name, self.hand, self.char, self.city) == \
            (other.player_id, other.gold, other.name, other.hand, other.char, other.city)

    def __repr__(self):
        return 'ShadowPlayer("{}")'.format(self.name)


class ShadowGame:
    """ Read-only copy of Game hiding all private info for passing into bot's controller """

    def __init__(self, game: Game):
        shadow_players = [ShadowPlayer(p) for p in game.players]
        crowned_index = game.players.crowned_index
        self.crowned_player = shadow_players[crowned_index] if crowned_index != -1 else None
        self.players = PlayersProxy(shadow_players, self.crowned_player)
        self.turn = ShadowTurn(game.turn)
        self.districts = Deck([Card(district).facedown for district in game.districts])
