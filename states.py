from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pyxel

from core import calculate_moves, calculate_spawn_positions

if TYPE_CHECKING:
    from game import Game

TILE = 32


@dataclass
class MenuState:
    game: Game
    room: str = ""

    @property
    def prompt(self):
        return f"ENTER ROOM NAME: {self.room.upper()}"

    def update(self):
        if pyxel.btnp(pyxel.KEY_F5):
            self.game.client.send("get_rooms:")

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.room = self.room[:-1]
            return

        if pyxel.btnp(pyxel.KEY_RETURN):
            self.game.room = self.room
            if self.room:
                self.game.client.send(f"room:{self.room}")
                self.game.wait()

        for k in range(97, 122):
            if pyxel.btnp(k):
                self.room += chr(k)
                break

    def draw(self):
        pyxel.text(0, 0, self.prompt, 0)
        for y, room in enumerate(self.game.rooms):
            pyxel.text(0, 12 + y * 6, room, 0)


@dataclass
class SetupState:
    game: Game
    possible_positions: tuple[int, int] = field(default_factory=list)
    is_finished: bool = False

    def update(self):
        game = self.game

        if self.is_finished and game.opponent_setup:
            game.board.update_opponent(game.opponent_setup)
            game.client.send("ready:")
            game.finish_setup()
            return

        if game.is_waiting:
            return

        if game.player.initial_pieces == [] and not game.in_hand:
            self.is_finished = True
            game.client.send(f"positions:{game.board.piece_positions}")
            game.wait()
            return

        if game.in_hand is None:
            game.in_hand = game.player.get_initial_piece()

        if game.in_hand:
            self.possible_positions = calculate_spawn_positions(
                game.in_hand, game.board
            )

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and game.in_hand:
            x = pyxel.mouse_x // 32
            y = pyxel.mouse_y // 32
            if (x, y) in self.possible_positions:
                game.board.place_piece(x, y, game.in_hand)
                game.in_hand = None
                self.possible_positions = []

    def draw(self):
        game = self.game

        game.board.draw()
        # draw possible positions
        for tile in self.possible_positions:
            pyxel.rect(
                tile[0] * TILE + 1,
                tile[1] * TILE + 1,
                TILE - 1,
                TILE - 1,
                pyxel.COLOR_LIGHT_BLUE,
            )
        # draw piece in hand
        if game.in_hand:
            game.in_hand.drag(pyxel.mouse_x, pyxel.mouse_y)


class PlayerTurnState:
    def __init__(self, game):
        self.game = game
        self.possible_positions = []
        self.highlight = None
        self.target = None
        self.phase = "standby"
        self.phases = [
            "standby",
            "spawning",
            "acting",
        ]
        self.gameover = False

    def clamp(self, value, min_val, max_val):
        return max(min(value, max_val), min_val)

    def update(self):
        game = self.game
        board = self.game.board
        x = self.clamp(pyxel.mouse_x // 32, 0, 5)
        y = self.clamp(pyxel.mouse_y // 32, 0, 5)

        piece = game.board.get_piece(x, y)

        if game.status:
            if pyxel.btnp(pyxel.KEY_RETURN):
                game.reset()

        if game.is_waiting:
            return

        if not game.board.duke_position and not self.gameover:
            game.loses += 1
            print("got here")
            game.client.send("lost:")
            self.gameover = True
            game.wait()
            return

        match self.phase:
            case "standby":
                # RIGHT CLICK
                if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
                    game.in_hand = game.player.pull_piece()
                    if game.in_hand:
                        self.possible_positions = calculate_spawn_positions(
                            game.in_hand, game.board
                        )
                        self.phase = "spawning"
                        return
                    else:
                        return

                # LEFT CLICK
                if (
                    pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
                    and not game.active
                    and piece
                    and piece.is_own
                ):
                    self.possible_positions = calculate_moves(x, y, piece, board)
                    if len(self.possible_positions) > 0:
                        game.active = piece
                        self.highlight = (x, y)
                        self.phase = "acting"
                        return

            case "spawning":
                if (
                    pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
                    and (x, y) in self.possible_positions
                ):
                    board.place_piece(x, y, game.in_hand)
                    piece_name = game.in_hand.name
                    game.in_hand = None
                    self.possible_positions = []
                    self.phase = "standby"
                    # send piece name and position in spawned
                    game.client.send(f"spawn_opponent:{piece_name}->{x},{y}")
                    game.wait()
                    return

            case "acting":
                if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                    if (x, y) in self.possible_positions:
                        # TODO make this better
                        board.place_piece(x, y, game.active)
                        game.active.flip()
                        board.positions[self.highlight[0]][self.highlight[1]] = None
                        # send previous and next position of moved piece
                        game.client.send(
                            f"move:{self.highlight[0]},{self.highlight[1]}->{x},{y}"
                        )

                        self.highlight = None
                        game.active = None
                        self.possible_positions = []
                        self.phase = "standby"
                        # TODO here wait
                        game.wait()
                        return
                    else:
                        game.active = None
                        self.highlight = None
                        self.possible_positions = []
                        self.phase = "standby"
                        return

    def draw(self):
        game = self.game
        t = TILE

        game.board.draw()
        # draw possible positions
        for tile in self.possible_positions:
            piece = game.board.get_piece(tile[0], tile[1])
            if piece and piece.is_own != game.active.is_own:
                pyxel.rectb(
                    tile[0] * t,
                    tile[1] * t,
                    t + 1,
                    t + 1,
                    pyxel.COLOR_YELLOW,
                )
            else:
                pyxel.rect(
                    tile[0] * t + 1,
                    tile[1] * t + 1,
                    t - 1,
                    t - 1,
                    pyxel.COLOR_LIGHT_BLUE,
                )
        # draw highlight
        if self.highlight:
            pyxel.rectb(
                self.highlight[0] * t + 1,
                self.highlight[1] * t + 1,
                t - 1,
                t - 1,
                pyxel.COLOR_YELLOW,
            )

        if game.status == "lost":
            pyxel.text(0, 0, "YOU LOST", pyxel.COLOR_RED)

        if game.status == "won":
            pyxel.text(0, 0, "YOU WON", pyxel.COLOR_RED)

        # draw piece in hand
        if game.in_hand:
            game.in_hand.drag(pyxel.mouse_x, pyxel.mouse_y)
