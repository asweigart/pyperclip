"""
Pyperclip

A cross-platform clipboard module for Python. (only handles plain text for now)
By Al Sweigart al@inventwithpython.com
BSD License

Usage:
  import pyperclip
  pyperclip.copy('The text to be copied to the clipboard.')
  spam = pyperclip.paste()

  if not pyperclip.is_available():
    print("Copy functionality unavailable!")

On Windows, no additional modules are needed.
On Mac, the module uses pbcopy and pbpaste, which should come with the os.
On Linux, install xclip or xsel via package manager. For example, in Debian:
sudo apt-get install xclip

Otherwise on Linux, you will need the gtk or PyQt4 modules installed.

gtk and PyQt4 modules are not available for Python 3,
and this module does not work with PyGObject yet.
"""
__version__ = '1.5.27'

import platform
import os
import subprocess
import warnings
from .clipboards import (init_osx_clipboard,
                         init_gtk_clipboard, init_qt_clipboard,
                         init_xclip_clipboard, init_xsel_clipboard,
                         init_klipper_clipboard, init_no_clipboard)
from .windows import init_windows_clipboard

# `import PyQt4` sys.exit()s if DISPLAY is not in the environment.
# Thus, we need to detect the presence of $DISPLAY manually
# and not load PyQt4 if it is absent.
HAS_DISPLAY = os.getenv("DISPLAY", False)
CHECK_CMD = "where" if platform.system() == "Windows" else "which"


def _executable_exists(name):
    return subprocess.call([CHECK_CMD, name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0


class _PyperclipBackend(object):
    """
    A singleton class to manage the clipboard backend.

    This class lazilly initializes the clipboard manager which allows the user
    to attempt to set the clipboard without automatically importing modules
    like PyQt4 or gtk.
    """
    def __init__(self):
        self.clipboard = None
        self.copy = self._first_copy
        self.paste = self._first_paste

    def _lazy_init(self):
        if self.clipboard is None:
            self._determine_clipboard()

    def _determine_clipboard(self):
        clipboard = self._find_valid_backend()
        self._set_clipboard(clipboard)

    def _find_valid_backend(self):
        # Determine the OS/platform and set
        # the copy() and paste() functions accordingly.
        if 'cygwin' in platform.system().lower():
            # FIXME: pyperclip currently does not support Cygwin,
            warnings.warn('pyperclip currently does not support Cygwin,'
                          'see https://github.com/asweigart/pyperclip/issues/55')
        elif os.name == 'nt' or platform.system() == 'Windows':
            return 'windows'
        if os.name == 'mac' or platform.system() == 'Darwin':
            return 'osx'
        if HAS_DISPLAY:
            # Determine which command/module is installed, if any.
            try:
                import gtk  # check if gtk is installed
            except ImportError:
                pass
            else:
                return 'gtk'

            try:
                import PyQt4  # check if PyQt4 is installed
            except ImportError:
                pass
            else:
                return 'qt'

            if _executable_exists("xclip"):
                return 'xclip'
            if _executable_exists("xsel"):
                return 'xsel'
            if _executable_exists("klipper") and _executable_exists("qdbus"):
                return 'klipper'

        return 'no'

    def _first_copy(self, text):
        # If the backend hasn't been initialized determine a valid clipboard
        self._lazy_init()
        self.copy(text)

    def _first_paste(self):
        # If the backend hasn't been initialized determine a valid clipboard
        self._lazy_init()
        return self.paste()

    def _set_clipboard(self, clipboard):
        self.clipboard = clipboard
        clipboard_types = {'osx': init_osx_clipboard,
                           'gtk': init_gtk_clipboard,
                           'qt': init_qt_clipboard,
                           'xclip': init_xclip_clipboard,
                           'xsel': init_xsel_clipboard,
                           'klipper': init_klipper_clipboard,
                           'windows': init_windows_clipboard,
                           'no': init_no_clipboard}
        self.copy, self.paste = clipboard_types[clipboard]()


# Create a global singleton backend instance
_backend = _PyperclipBackend()


def is_available():
    """
    Checks if clipboard functionality is available

    Returns:
        bool: True if a valid backend exists
    """
    _backend._lazy_init()
    return bool(_backend.copy)


def determine_clipboard():
    """
    Initializes the clipboard backend

    Returns:
        tuple: the copy and paste function
    """
    _backend._lazy_init()
    return _backend.copy, _backend.paste


def set_clipboard(clipboard):
    """
    Sets the current clipboard backend

    Args:
        clipboard (str): one of the following values
            'osx', 'gtk', 'qt', 'xclip', 'xsel', 'klipper', 'windows', or 'no'
    """
    _backend._set_clipboard(clipboard)


def get_clipboard():
    """
    Returns the current clipboard backend

    Returns:
        str: the clipboard backend
    """
    return _backend.clipboard


def copy(text):
    """
    Populates the clipboard

    Args:
        text (str): string to copy into the clipboard
    """
    _backend.copy(text)


def paste():
    """
    Get the current text in the clipboard

    Returns:
        str: the current content of the clipboard
    """
    return _backend.paste()


__all__ = ["copy", "paste"]
