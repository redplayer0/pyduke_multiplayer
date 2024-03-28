from board import Board
from moves import SPAWN_POSITIONS
from piece import Piece, PIECES


def decode_opponent_piece_positions(msg):
    pieces = {}
    raw_pieces = msg.split("-")
    for raw_piece in raw_pieces:
        name, raw_posflip = raw_piece.split()
        x, y, flip = raw_posflip.split(",")
        pos = (int(x), int(y))
        flipped = bool(flip)
        pieces[pos] = Piece(name, is_own=False, is_flipped=flipped)

    return pieces


def calculate_spawn_positions(piece: Piece, board: Board):
    array = []
    if piece.tag == "DUKE":
        return [(2, 5), (3, 5)]
    else:
        duke_pos = board.duke_position
        for move in SPAWN_POSITIONS:
            x = duke_pos[0] + move.dx
            y = duke_pos[1] + move.dy
            if 0 <= x < 6 and 0 <= y < 6:
                if not board.get_piece(x, y):
                    array.append((x, y))

    return array


def calculate_moves(px, py, piece: Piece, board: Board):
    array = []

    for move in piece.moves:
        dx = move.dx
        dy = move.dy
        if move.is_slide:
            x = px + dx
            y = py + dy
            while 0 <= x < 6 and 0 <= y < 6:
                pos_piece = board.get_piece(x, y)
                if not pos_piece:
                    array.append((x, y))
                    x += dx
                    y += dy
                elif not pos_piece.is_own:
                    array.append((x, y))
                    break
                else:
                    break
        else:
            x = px + dx
            y = py + dy
            if 0 <= x < 6 and 0 <= y < 6:
                pos_piece = board.get_piece(x, y)
                if not pos_piece:
                    array.append((x, y))
                elif not pos_piece.is_own:
                    array.append((x, y))

    return array
