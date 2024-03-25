from dataclasses import dataclass


@dataclass(slots=True)
class Move:
    dx: int
    dy: int
    is_slide: bool = False
    is_jump: bool = False
    is_strike: bool = False
    is_command: bool = False
    is_shield: bool = False


MOVES = {
    # ORTHO MOVES
    "UP": Move(0, -1),
    "DOWN": Move(0, 1),
    "LEFT": Move(-1, 0),
    "RIGHT": Move(1, 0),
    "UP2": Move(0, -2),
    # DIAG MOVES
    "UP_LEFT": Move(-1, -1),
    "DOWN_LEFT": Move(-1, 1),
    "UP_RIGHT": Move(1, -1),
    "DOWN_RIGHT": Move(1, 1),
    # ORTHO JUMPS
    "JUMP_UP": Move(0, -2, is_jump=True),
    "JUMP_DOWN": Move(0, 2, is_jump=True),
    "JUMP_LEFT": Move(-2, 0, is_jump=True),
    "JUMP_RIGHT": Move(2, 0, is_jump=True),
    # ORTHO SLIDES
    "SLIDE_UP": Move(0, -1, is_slide=True),
    "SLIDE_DOWN": Move(0, 1, is_slide=True),
    "SLIDE_LEFT": Move(-1, 0, is_slide=True),
    "SLIDE_RIGHT": Move(1, 0, is_slide=True),
}

SPAWN_POSITIONS = [
    MOVES["UP"],
    MOVES["DOWN"],
    MOVES["LEFT"],
    MOVES["RIGHT"],
]


def create_move(raw_move):
    move = Move(0, 0)

    if "u" in raw_move:
        move.dy -= 1
    if "d" in raw_move:
        move.dy += 1
    if "l" in raw_move:
        move.dx -= 1
    if "r" in raw_move:
        move.dx += 1

    if "s" in raw_move:
        move.is_slide = True
    if "j" in raw_move:
        move.is_jump = True
    if "k" in raw_move:
        move.is_strike = True
    if "c" in raw_move:
        move.is_command = True
    if "h" in raw_move:
        move.is_shield = True

    if "2" in raw_move:
        move.dx = move.dx * 2
        move.dy = move.dy * 2

    return move
