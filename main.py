from client import Client, make_decorator
from core import decode_opponent_piece_positions
from game import Game

game = Game()
client = Client(is_game=True)
game.attach(client)

handle = make_decorator(game, client)


@handle
def rooms(game: Game, client: Client, data: str):
    game.rooms = data.split(",")


@handle
def uid(game: Game, client: Client, uid: str):
    client.uid = uid


@handle
def name(game: Game, client: Client, name: str):
    game.name = name


@handle
def room(game: Game, client: Client, room: str):
    game.room = room


@handle
def info(game: Game, client: Client, data: str):
    game.notifications.insert(0, data)


@handle
def room_ready(game: Game, client: Client, data: str):
    game.board_setup()


@handle
def positions(game: Game, client: Client, data: str):
    pieces = decode_opponent_piece_positions(data)
    game.opponent_setup = pieces


@handle
def move(game: Game, client: Client, opponent_move: str):
    if opponent_move:
        game.board.move_opponent(opponent_move)

    game.resume()


@handle
def spawn_opponent(game: Game, client: Client, opponent_move: str):
    if opponent_move:
        game.board.spawn_opponent(opponent_move)
    game.resume()


@handle
def won(game: Game, client: Client, opponent_move: str):
    game.wins += 1
    game.status = "won"


@handle
def lost(game: Game, client: Client, opponent_move: str):
    game.loses += 1
    game.status = "lost"


if __name__ == "__main__":
    game.start()
