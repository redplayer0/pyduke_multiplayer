from dataclasses import dataclass, field
from random import randint

from piece import Piece


def gen_initial_pieces():
    return [
        Piece("foot"),
        Piece("foot"),
        Piece("duke"),
    ]


@dataclass(slots=True)
class Player:
    initial_pieces: list[Piece] = field(default_factory=gen_initial_pieces)
    bag: list[Piece] = field(default_factory=list)

    def give_pieces(self, pieces: list[str]):
        for piece in pieces:
            self.bag.append(Piece(piece))

    def get_initial_piece(self):
        return self.initial_pieces.pop()

    def pull_piece(self) -> Piece | None:
        if len(self.bag) > 0:
            i = randint(0, len(self.bag) - 1)
            return self.bag.pop(i)
        else:
            return None
