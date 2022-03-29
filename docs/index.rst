.. Pyperclip documentation master file, created by
   sphinx-quickstart on Fri Aug 15 22:34:37 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. default-role:: code

Welcome to Pyperclip's documentation!
=====================================

Pyperclip provides a cross-platform Python module for copying and pasting text to the clipboard.

To copy text to the clipboard, pass a string to ``pyperclip.copy()``. To paste the text from the clipboard, call ``pyperclip.paste()`` and the text will be returned as a string value.

.. code:: python

    >>> import pyperclip
    >>> pyperclip.copy('Hello, world!')
    >>> pyperclip.paste()
    'Hello, world!'

Pyperclip also has a `pyperclip.waitForPaste()` function, which blocks and doesn't return until a non-empty text string is on the clipboard. It then returns this string. The `pyperclip.waitForNewPaste()` blocks until the text on the clipboard has changed:

.. code:: python

    >>> import pyperclip
    >>> pyperclip.waitForPaste()  # Doesn't return until non-empty text is on the clipboard.
    'Hello, world!'

    >>> pyperclip.copy('original text')
    >>> pyperclip.waitForNewPaste()  # Doesn't return until the clipboard has something other than "original text".
    'Hello, world!'

These functions also have a `timeout` argument to specify a number of seconds to check. If the timeout elapses without returning, the functions raise a `PyperclipTimeoutException` exception:

    >>> import pyperclip
    >>> pyperclip.waitForNewPaste(5)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\github\pyperclip\src\pyperclip\__init__.py", line 689, in waitForNewPaste
        raise PyperclipTimeoutException('waitForNewPaste() timed out after ' + str(timeout) + ' seconds.')
    pyperclip.PyperclipTimeoutException: waitForNewPaste() timed out after 5 seconds.


Not Implemented Error
=====================

You may get an error message that says: "Pyperclip could not find a copy/paste mechanism for your system. Please see https://pyperclip.readthedocs.io/en/latest/introduction.html#not-implemented-error for how to fix this."

In order to work equally well on Windows, Mac, and Linux, Pyperclip uses various mechanisms to do this. Currently, this error should only appear on Linux (not Windows or Mac). You can fix this by installing one of the copy/paste mechanisms:

- ``sudo apt-get install xsel`` to install the xsel utility.
- ``sudo apt-get install xclip`` to install the xclip utility.
- ``pip install gtk`` to install the gtk Python module.
- ``pip install PyQt4`` to install the PyQt4 Python module.

Pyperclip won't work on mobile operating systems such as Android or iOS, nor in browser-based interactive shells such as `replit.com <https://replit.com>`_, `pythontutor.com <http://pythontutor.com>`_, or `pythonanywhere.com <https://pythonanywhere.com>`_.
