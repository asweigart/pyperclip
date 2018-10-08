# -*- coding: utf-8 -*-
"""
Pyperclip Monitor

Utility for monitoring the clipboard based on Pyperclip

Usage:
    from pyperclip.monitor import Monitor

    for entry in Monitor():
        print("Added to clipboard: {}".format(entry))

"""

import pyperclip
import time


class Monitor(object):
    """Main clipboard monitor class.

    Used as an iterable, yields the clipboard content when changes.

    """

    def __init__(self, warm_start=False):
        """__init__ method.

        Args:
            warm_start (boolean): Determines whether the clipboard content when its iterated should be taken into account

        """
        self._warm_start = warm_start

    def __iter__(self):
        """__iter__ method.

        Yields the clibpoard content when changes.

        """
        last = pyperclip.paste() if not self._warm_start else None

        while True:
            if pyperclip.paste() == last:
                time.sleep(0.1)
            else:
                last = pyperclip.paste()
                yield last
