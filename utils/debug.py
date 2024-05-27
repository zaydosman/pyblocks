import os


def print_board(board):
    """
    Clears the terminal and prints the game board to it.

    Parameters
    ----------
    board: Board()
        Game board instance.
    """
    buffer=[]
    buffer.append('-------------------------------\n')
    for row in board.board_list:
        line = '|'
        for col in row:
            if col:
                line += u"\u25A2 "
            else:
                line += '  '
            line += '|'
        buffer.append(f'{line}\n')
        buffer.append('-------------------------------\n')
    os.system('cls')
    print(f'SCORE: {board.score}')
    print(''.join(buffer))
