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

    '''
    '''
    def __init__(self, warm_start=False):
        self.warm_start = warm_start

    def __iter__(self):

        last = pyperclip.paste() if not self.warm_start else None

        while True:
            if pyperclip.paste() == last:
                time.sleep(0.1)
            else:
                last = pyperclip.paste()
                yield last
