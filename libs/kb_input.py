import msvcrt
import threading
import time


SPECIAL_KEY_KEYCODE = b'\xe0'
KEYCODE_ACTIONS = {
    b'K': 'TRANSLATE_LEFT',
    b'M': 'TRANSLATE_RIGHT',
    b'P': 'TRANSLATE_DOWN',
    b'H': 'ROTATE_RIGHT',
    b'\x1b': 'QUIT',
}


class InputListenerThread(threading.Thread):
    """
    Thread to listen for keyboard inputs.
    """

    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stopped = False
        self.callback = callback

    def run(self):
        """
        Continously checks for and records keyboard input, if the thread was
        not signalled to stop. Initiates a callback based on the input if
        valid.
        """
        #TODO: Consider abstracting and allowing UNIX/MacOS inputs.
        while not self.stopped:
            if msvcrt.kbhit():
                input_char = msvcrt.getch()
                if input_char == SPECIAL_KEY_KEYCODE:
                    input_char = msvcrt.getch()
                try:
                    self.callback(KEYCODE_ACTIONS[input_char])
                except KeyError:
                    continue
            time.sleep(0.01)

    def stop(self):
        """
        Signals the thread to stop listening for keyboard input.
        """
        self.stopped = True


class AsyncInputHandler:
    """
    Handler for keyboard input listener.
    """

    def __init__(self, callback):
        """
        Creates a keyboard input listener.
        """
        self.callback = callback
        self.input_thread = InputListenerThread(callback)

    def __enter__(self):
        """
        Starts a keyboard input listener on a separate thread.
        """
        self.input_thread.start()
        return self

    def __exit__(self, *args, **kwargs):
        """
        Closes the keyboard input listener thread.
        """
        self.input_thread.stop()
        self.input_thread.join()
        self.input_thread = None
