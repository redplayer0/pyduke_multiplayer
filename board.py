from __future__ import annotations

from dataclasses import dataclass, field

import pyxel

from piece import Piece

TILE = 32


def gen_board():
    return [[None for _ in range(6)] for _ in range(6)]


@dataclass(slots=True)
class Board:
    rows: int = 6
    cols: int = 6
    line_length = rows * TILE
    positions: list[Piece] = field(default_factory=gen_board)

    @property
    def piece_positions(self):
        msg = ""
        for x in range(self.rows):
            for y in range(self.cols):
                if piece := self.positions[x][y]:
                    if piece.is_own:
                        msg += (
                            f"{piece.name} {x},{y},{'f' if piece.is_flipped else ''}-"
                        )

        return msg[:-1]

    @property
    def duke_position(self):
        for x in range(self.rows):
            for y in range(self.cols):
                if piece := self.positions[x][y]:
                    if piece.tag == "DUKE" and piece.is_own:
                        return (x, y)

    def get_piece(self, x, y) -> Piece:
        return self.positions[x][y]

    def place_piece(self, x, y, piece):
        self.positions[x][y] = piece

    def clear_opponent(self):
        for x in range(self.rows):
            for y in range(self.cols):
                if piece := self.positions[x][y]:
                    if not piece.is_own:
                        self.positions[x][y] = None

    def update_opponent(self, pieces: list[Piece]):
        self.clear_opponent()
        for pos, piece in pieces.items():
            x, y = pos
            self.positions[5 - x][5 - y] = piece

    def move_opponent(self, move: str):
        raw_pre, raw_after = move.split("->")
        px, py = [int(v) for v in raw_pre.split(",")]
        x, y = [int(v) for v in raw_after.split(",")]
        self.positions[5 - x][5 - y] = self.positions[5 - px][5 - py].flip()
        self.positions[5 - px][5 - py] = None

    def spawn_opponent(self, move: str):
        print(move)
        piece_name, raw_pos = move.split("->")
        x, y = [int(v) for v in raw_pos.split(",")]
        self.positions[5 - x][5 - y] = Piece(piece_name, is_own=False)

    def draw_pieces(self):
        for x, row in enumerate(self.positions):
            for y, piece in enumerate(row):
                if piece:
                    piece.draw(x, y)

    def draw(self):
        t = TILE
        ln = self.line_length
        nr = self.rows
        nc = self.cols
        dblue = pyxel.COLOR_DARK_BLUE
        for r in range(self.rows):
            for c in range(self.cols):
                # row
                pyxel.line(r * t, c * t, r * t, ln, dblue)
                # col
                pyxel.line(r * t, c * t, ln, c * t, dblue)
        pyxel.line(nr * t, 0, ln, nc * t, dblue)
        pyxel.line(0, nc * t, nr * t, ln, dblue)

        self.draw_pieces()
