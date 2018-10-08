import pyperclip
import time


def monitor(warm_start=False):

    last = pyperclip.paste() if not warm_start else None

    while 1:
        if pyperclip.paste() == last:
            time.sleep(0.1)
        else:
            last = pyperclip.paste()
            yield last
