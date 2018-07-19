Pyperclip is a cross-platform Python module for copy and paste clipboard functions. It works with Python 2 and 3.

`pip install pyperclip`

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

On Linux, this module makes use of the xclip or xsel commands, which should come with the os. Otherwise run "sudo apt-get install xclip" or "sudo apt-get install xsel" (Note: xsel does not always seem to work.)

Otherwise on Linux, you will need the gtk or PyQt4 modules installed.
