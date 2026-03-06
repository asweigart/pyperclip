Pyperclip is a cross-platform Python module for copy and paste clipboard functions. It works with Python 2 and 3.

Install on Windows: `pip install pyperclip`

Install on Linux/macOS: `pip3 install pyperclip`

Al Sweigart al@inventwithpython.com
BSD License

Example Usage
=============

    >>> import pyperclip
    >>> pyperclip.copy('The text to be copied to the clipboard.')
    >>> pyperclip.paste()
    'The text to be copied to the clipboard.'


Currently only handles plaintext.

On Windows, no additional modules are needed.

On Mac, this module makes use of the pbcopy and pbpaste commands, which should come with the os.

On Linux, this module makes use of the xclip, xsel, or wl-clipboard commands, which should come with the os. Otherwise run "sudo apt-get install xclip", "sudo apt-get install xsel", or "sudo apt-get install wl-clipboard" (for Wayland).

Otherwise on Linux, you will need the qtpy or PyQt5 modules installed.

If no GUI clipboard is available, Pyperclip will fallback to using the OSC 52 terminal escape sequence to copy text if it detects it is running in a terminal (e.g., over SSH). Note that pasting is not supported via OSC 52.

Support
-------

If you find this project helpful and would like to support its development, [consider donating to its creator on Patreon](https://www.patreon.com/AlSweigart).
