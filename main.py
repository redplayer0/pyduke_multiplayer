from game import Game
from core import decode_opponent_piece_positions
from client import Client

client = Client(is_game=True)
game = Game()
game.attach(client)


@client.command("/rooms")
def room_info(client: Client, data: str):
    client.game.rooms = data.split(",")


@client.command("/uid")
def room_info(client: Client, uid: str):
    client.uid = uid


@client.command("/name")
def room_info(client: Client, name: str):
    client.game.name = name


@client.command("/room")
def room_info(client: Client, room: str):
    client.game.room = room


@client.command("/info")
def notify(client: Client, data: str):
    client.game.notifications.insert(0, data)


@client.command("/room_ready")
def room_full(client: Client, data: str):
    client.game.board_setup()


@client.command("/positions")
def opponent_turn(client: Client, data: str):
    pieces = decode_opponent_piece_positions(data)
    client.game.opponent_setup = pieces


@client.command("/move")
def make_move(client: Client, opponent_move: str):
    if opponent_move:
        client.game.board.move_opponent(opponent_move)

    client.game.resume()


@client.command("/won")
def make_move(client: Client, opponent_move: str):
    client.game.wins += 1
    # client.game.state.phase = "won"
    client.game.resume()


if __name__ == "__main__":
    game.start()
