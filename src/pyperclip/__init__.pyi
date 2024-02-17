# Type signature stub file for pyperclip,
#
# Pyperclip is delibarately backwards compatable with
# python 2.6, and so type annotation within the source
# directly are not an option.

from typing import Callable, Optional

# All and only those functions listed in __all__ are given
# type annotated signatures here. 


def copy(text: str) -> None: ...


def paste() -> str: ...


# timeout will typically be an int, but floats work.
def waitForPaste(timeout: Optional[float] = None) -> str: ...


def waitForNewPaste(timeout: Optional[float] = None) -> str: ...


def set_clipboard(clipboard: str) -> None: ...


def determine_clipboard() -> tuple[
        Callable[[str], None],
        Callable[[], str]
    ]: ...
