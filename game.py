from dataclasses import dataclass, field
from typing import Any

import pyxel

from board import Board
from client import Client
from piece import Piece
from player import Player
from states import MenuState, PlayerTurnState, SetupState

TILE = 32


@dataclass(slots=True)
class Game:
    board: Board = field(default_factory=Board)
    state: Any = None
    room: str = None
    rooms: list[str] = field(default_factory=list)
    client: Client = None

    notifications: list[str] = field(default_factory=list)
    wins: int = 0
    loses: int = 0
    status: str = None

    player: Player = field(default_factory=Player)
    in_hand: Piece = None
    active: Piece = None

    opponent_setup: dict[tuple[int, int], Piece] = field(default_factory=dict)

    is_waiting: bool = False

    def start(self):
        # pyxel stuff
        pyxel.init(240, 240)
        pyxel.load("my_resource.pyxres")
        pyxel.mouse(True)

        self.state = MenuState(self)
        self.client.send("/uid")

        pyxel.run(self.update, self.draw)

    def reset(self):
        self.board: Board = Board()
        self.state: Any = MenuState(self)
        self.room: str = None
        self.player: Player = Player()
        self.in_hand: Piece = None
        self.active: Piece = None
        self.opponent_setup = {}

        self.is_waiting = False
        self.notifications = []
        self.status = None
        self.client.send("/exit_room")

    def attach(self, client: Client):
        self.client = client
        self.client.game = self
        self.client.connect()
        self.client.send("/get_rooms")

    def wait(self):
        self.is_waiting = True

    def resume(self):
        self.is_waiting = False

    def board_setup(self):
        self.resume()
        self.state = SetupState(self)

    def finish_setup(self):
        self.player.give_pieces(["seer", "priest"])
        self.state = PlayerTurnState(self)

    def update(self):
        self.state.update()

    def draw(self):
        pyxel.cls(pyxel.COLOR_WHITE)

        self.state.draw()

        if self.is_waiting:
            pyxel.text(200, 0, "WAITING...", pyxel.COLOR_RED)

        # for i in range(0, 3):
        #     pyxel.text(
        #         0, 240 - (i + 1) * 6, self.notifications[i], pyxel.COLOR_LIGHT_BLUE
        #     )

        if self.notifications:
            pyxel.text(0, 234, self.notifications[0], pyxel.COLOR_LIGHT_BLUE)

        # debug info
        # x = pyxel.mouse_x // 32
        # y = pyxel.mouse_y // 32
        # piece = self.board.get_piece(x, y)
        # pyxel.text(
        #     0,
        #     0,
        #     f"active: {self.active.name if self.active else ''}",
        #     pyxel.COLOR_BLACK,
        # )
        # pyxel.text(
        #     0,
        #     10,
        #     f"under mouse: {piece.name if piece else ''}",
        #     pyxel.COLOR_BLACK,
        # )

        # # grid position
        # pyxel.text(0, 20, f"x: {x} y: {y}", pyxel.COLOR_BLACK)


if __name__ == "__main__":
    game = Game()
    game.start()
