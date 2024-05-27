""" Main game file. """
import time
import random
import contextlib
import threading
import libs.kb_input as kb_input
import utils.debug as debug


@contextlib.contextmanager
def bounds_manager():
    """
    A context manager to be used via the `with` statement. Allows wrapped code
    to continue running if IndexError is raised.
    """
    try:
        yield
    except IndexError:
        pass


class Quad:
    """
    Class representing a piece made of 4 blocks. Stores its coordinates and
    calculates its potential location after a move in any direction.
    """

    # Spawn coordinates for each Quad piece.
    QUAD_SPAWNS = {
    'LINE': [[3, 0], [4, 0], [5, 0], [6, 0]],
    'SQUARE': [[4, 0], [5, 0], [4, 1], [5, 1]],
    'L': [[3, 1], [4, 1], [5, 1], [5, 0]],
    'J': [[3, 1], [4, 1], [5, 1], [3, 0]],
    'S': [[3, 1], [4, 1], [4, 0], [5, 0]],
    'Z': [[3, 0], [4, 0], [4, 1], [5, 1]],
    'T': [[3, 1], [4, 0], [4, 1], [5, 1]],
    }

    def __init__(self, type):
        """
        Initialise spawn coordinates, based Quad type, and 'action' function
        pointers.

        Parameters
        ----------
        type: str
            Type of Quad piece.
            One of: 'LINE', 'SQUARE', 'L', 'J', 'S', 'Z', 'T'.
        """
        self.type = type
        self.coords = self.QUAD_SPAWNS[self.type]
        self.actions = {
            'TRANSLATE_DOWN': self.if_translate_down,
            'TRANSLATE_LEFT': self.if_translate_left,
            'TRANSLATE_RIGHT': self.if_translate_right,
            'ROTATE_RIGHT': self.if_rotate_right,
        }

    @classmethod
    def get_new_quad(cls):
        """
        Returns an instance of the next Quad piece that should spawn.
        """
        #TODO: - Implement bag of 7
        #      - Display next three pieces
        quad_type = random.choice(list(cls.QUAD_SPAWNS.keys()))
        return Quad(quad_type)

    def update_coords(self, updated_coords):
        """
        Update the coordinates of the Quad piece.

        Parameters
        ----------
        updated_coords: list[list[int, int]]
            New coordinates of the Quad piece.
        """
        for legal_coord in self.actions.values():
            if updated_coords == legal_coord():
                self.coords = updated_coords
                return
        raise ValueError(f"Illegal new coords. Attempted to move from "
                         f"{self.coords} to {updated_coords}.")

    def if_translate_down(self):
        """
        Returns the coordinates of the Quad piece if it had to move down.
        """
        return [[coord[0], coord[1] + 1] for coord in self.coords]

    def if_translate_left(self):
        """
        Returns the coordinates of the Quad piece if it had to move left.
        """
        return [[coord[0] - 1, coord[1]] for coord in self.coords]

    def if_translate_right(self):
        """
        Returns the coordinates of the Quad piece if it had to move right.
        """
        return [[coord[0] + 1, coord[1]] for coord in self.coords]

    def if_rotate_right(self):
        """
        Returns the coordinates of the Quad piece if it had to rotate 90
        degrees clockwise.
        """
        # Calculate the centroid of the coordinates
        #TODO: Make intrinsic to piece
        centroid_x = round(
            sum(coord[0] for coord in self.coords) / len(self.coords)
        )
        centroid_y = round(
            sum(coord[1] for coord in self.coords) / len(self.coords)
        )

        potential_coords = []
        for i in range(len(self.coords)):
            x, y = self.coords[i][0], self.coords[i][1]
            # Translate point to origin (centroid)
            translated_x = x - centroid_x
            translated_y = y - centroid_y
            # Rotate point 90 degrees clockwise
            rotated_x = -translated_y
            rotated_y = translated_x
            # Translate point back to the centroid
            final_x =  rotated_x + centroid_x
            final_y =  rotated_y + centroid_y
            # Update the coordinate in place
            potential_coords.append([final_x, final_y])

        return potential_coords


class Board:
    """
    Class representing the game board.
    """

    def __init__(self):
        """
        Initialise the 2D board.
        """
        self.board_list = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        self.board_lock = threading.Lock()
        self.active_quad = None
        self.game_over = False
        self.score = 0
        # Initialise the input handler and pass it a callback function pointer.
        self.input_handler = kb_input.AsyncInputHandler(
            self.update_active_quad)
        self.stack = contextlib.ExitStack()

    def __enter__(self):
        """
        Start the input handler.
        """
        try:
            self.stack.enter_context(self.input_handler)
        except Exception as error:
            self.__exit__(type(error), error, error.__traceback__)
            raise
        return self

    def __exit__(self, *args, **kwargs):
        self.stack.__exit__(*args, **kwargs)

    def _coords_available(self, coords):
        """
        Checks if a list of coordinates are unset.

        Parameters
        ----------
        coords: list[list[int, int]]
            List of coordinates.

        Returns
        -------
        bool
            True if all coordinates in `coords` are unset, otherwise False.
        """
        with bounds_manager():
            for coord in coords:
                if coord[0] < 0 or coord[1] < 0:
                    return False
                if self.board_list[coord[1]][coord[0]]:
                    return False
            return True
        return False

    def _update_board_list(self, add_coords, remove_coords=[]):
        """
        Update coordinates on the board, either setting or unsetting them.

        NOTE: Do NOT use on its own. Before using this function:
              - Use `_coords_available()` on all input coordinates.
              - Acquire `self.board_lock()`.

        Parameters
        ----------
        add_coords: list[list[int, int]]
            List of unset coordinates to set.

        remove_coords: list[list[int, int]]
            List of set coordinates to unset.
        """
        for coord in add_coords:
            if self.board_list[coord[1]][coord[0]]:
                raise RuntimeError(f'Attempted to set a set coord '
                                   f'({coord[0]}, {coord[1]}).')
            self.board_list[coord[1]][coord[0]] = 1

        for coord in remove_coords:
            if not self.board_list[coord[1]][coord[0]]:
                raise RuntimeError(f'Attempted to unset an unset coord '
                                   f'({coord[0]}, {coord[1]}).')
            self.board_list[coord[1]][coord[0]] = 0

    def _update_line_filled(self):
        """
        Clears any fully set row on the board and adds an empty one to the top.

        NOTE: Do NOT use on its own. Before using this function:
              - Acquire `self.board_lock()`.
        """
        #TODO: Consider implementing linked list.
        for row_idx in range(len(self.board_list)):
            if all(self.board_list[row_idx]):
                del self.board_list[row_idx]
                self.board_list.insert(0, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                #TODO: Update scoring to increase when:
                #      - A line is filled for consecutive Quads.
                #      - Multiple lines are filled with one active Quad.
                #      - Level up?
                self.score += 1
        debug.print_board(self)

    def spawn_quad(self):
        """
        Gets a new Quad piece and sets the active Quad to it.
        """
        with self.board_lock:
            if self.active_quad:
                raise RuntimeError(
                    'Attempted to spawn a quad when one was already active.'
                )
            self.active_quad = Quad.get_new_quad()
            if self._coords_available(self.active_quad.coords):
                self._update_board_list(self.active_quad.coords)
                return
            self.game_over = True

    def update_active_quad(self, action):
        """
        Updates the active quad coordinates on the board based on the `action`.
        Marks the active Quad as inactive if it can't move down.

        NOTE: This is called by the main game thread and the input handler
              thread.

        Parameters
        ----------
        action: str
            Action describing how to move the active Quad.
        """
        if action == 'QUIT':
            self.game_over = True
            return

        if not self.active_quad:
            return

        if action not in self.active_quad.actions.keys():
            raise RuntimeError(
                f'Unrecognised action {action}. Accepted actions are: '
                f'{self.active_quad.actions.keys()}'
            )

        with self.board_lock:
            updated_coords = self.active_quad.actions[action]()
            new_coords = [coord for coord in updated_coords
                          if coord not in self.active_quad.coords]
            remove_coords = [coord for coord in self.active_quad.coords
                             if coord not in updated_coords]

            if self._coords_available(new_coords):
                self._update_board_list(new_coords,
                                        remove_coords=remove_coords)
                self.active_quad.update_coords(updated_coords)
                debug.print_board(self)
                return

            if action == 'TRANSLATE_DOWN':
                # Could not move down means piece becomes set in board.
                self.active_quad = None
                self._update_line_filled()


    def try_update_state(self):
        """
        Spawns an active Quad if there isn't one. Translates it down every
        second.
        """
        if not self.game_over:
            if not self.active_quad:
                self.spawn_quad()
            self.update_active_quad('TRANSLATE_DOWN')
            #TODO: Implement leveling up based on score, and decrease delay
            #      for auto down translate.
            time.sleep(1)

        return not self.game_over


class GameInstance:
    """
    Class representing a Pyblocks game instance.
    """

    def __init__(self):
        self.board = Board()
        self.stack = contextlib.ExitStack()

    def __enter__(self):
        self.stack.enter_context(self.board)
        return self

    def __exit__(self, *args, **kwargs):
        self.stack.__exit__(*args, **kwargs)

    def game_loop(self):
        """
        The infinite main Game Loop. Continously updates the game state.
        Exits the game if the state can't be updated.
        """
        while True:
            if not self.board.try_update_state():
                print(f"Game Over! Your score was {self.board.score}")
                return


if __name__ == "__main__":
    # TODO: Implement splitscreen, consider networked multiplayer.
    with GameInstance() as new_game:
        new_game.game_loop()
