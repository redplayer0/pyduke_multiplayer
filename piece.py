from __future__ import annotations

from dataclasses import dataclass, field

import pyxel

from moves import Move, create_move


def load_pieces(filename):
    pieces = {}

    with open(filename, "r") as f:
        for line in f.readlines():
            parts = line.strip().split(":")
            name = parts[0].strip()
            parts = parts[1].strip().split("-")
            normal_moves = parts[0]
            flipped_moves = parts[1]

            pieces[name] = [normal_moves.split(), flipped_moves.split()]

    return pieces


TILE = 32
PIECES = load_pieces("game_pieces.txt")


@dataclass(slots=True)
class Piece:
    name: str
    is_own: bool = True
    is_flipped: bool = False
    normal_moves: list[Move] = field(default_factory=list)
    flipped_moves: list[Move] = field(default_factory=list)

    @property
    def tag(self):
        return self.name.upper()

    @property
    def moves(self):
        return self.flipped_moves if self.is_flipped else self.normal_moves

    def __post_init__(self):
        for move in PIECES[self.name][0]:
            self.normal_moves.append(create_move(move))
        for move in PIECES[self.name][1]:
            self.flipped_moves.append(create_move(move))

    def flip(self) -> Piece:
        self.is_flipped = not self.is_flipped
        return self

    def draw(self, x, y):
        t = TILE
        white = pyxel.COLOR_WHITE
        if self.is_own:
            pyxel.blt(x * t + 1, y * t + 1, 0, 0, 0, t - 1, t - 1)
        else:
            pyxel.blt(x * t + 1, y * t + 1, 0, 0, 32, t - 1, t - 1)
        for move in self.moves:
            dx = move.dx
            dy = move.dy
            if not self.is_own:
                dx = -dx
                dy = -dy
            if move.is_slide and move.is_jump:
                pyxel.rect(
                    x * t + 1 + 15 + dx * 5, y * t + 1 + 15 + dy * 5, 2, 2, white
                )
                pyxel.rectb(x * t + 1 + 14 + dx * 5, y * t + 1 + 14 + dy * 5, 4, 4, 0)
            elif move.is_jump:
                pyxel.rectb(x * t + 1 + 14 + dx * 5, y * t + 1 + 14 + dy * 5, 4, 4, 0)
            elif move.is_slide:
                pyxel.rect(
                    x * t + 1 + 15 + dx * 5, y * t + 1 + 15 + dy * 5, 2, 2, white
                )
            else:
                pyxel.rect(x * t + 1 + 15 + dx * 5, y * t + 1 + 15 + dy * 5, 2, 2, 0)
            pyxel.rectb(
                x * t + 1 + 15 + dx * 5 - 1, y * t + 1 + 15 + dy * 5 - 1, 4, 4, 0
            )

    def drag(self, x, y):
        white = pyxel.COLOR_WHITE
        if self.is_own:
            pyxel.blt(x, y, 0, 0, 0, TILE - 1, TILE - 1)
        else:
            pyxel.blt(x, y, 0, 0, 32, TILE - 1, TILE - 1)
        for move in self.moves:
            dx = move.dx
            dy = move.dy
            if not self.is_own:
                dx = -dx
                dy = -dy
            if move.is_slide and move.is_jump:
                pyxel.rect(x + 15 + dx * 5, y + 15 + dy * 5, 2, 2, white)
                pyxel.rectb(x + 14 + dx * 5, y + 14 + dy * 5, 4, 4, 0)
            elif move.is_jump:
                pyxel.rectb(x + 14 + dx * 5, y + 14 + dy * 5, 4, 4, white)
            elif move.is_slide:
                pyxel.rect(x + 15 + dx * 5, y + 15 + dy * 5, 2, 2, white)
            else:
                pyxel.rect(x + 15 + dx * 5, y + 15 + dy * 5, 2, 2, 0)
            pyxel.rectb(x + 15 + dx * 5 - 1, y + 15 + dy * 5 - 1, 4, 4, 0)
