from citadels.rules import score


def per_player_evaluate(player, game):
    return score(player, game) + \
           player.gold


def evaluate(player, game):
    return per_player_evaluate(player, game) - max(per_player_evaluate(p, game) for p in game.players if p.player_id != player.player_id)
