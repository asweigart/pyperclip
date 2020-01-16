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

On Windows, no additional modules are needed. It also allows to access other clipboard formats other than the CF_UNICODETEXT.
It does so while maintaining compatibility with the usage described above.

    >>> import pyperclip
    >>> pyperclip.copy(html_text, 49460)  # The HTML Format
    >>> html_in_clipboard = pyperclip.paste(49460)

Also, multiple formats can be copied if using

    >>> pyperclip.copy({CF_UNICODETEXT: "this is the unicode text",
                        CF_TEXT: b"This is the ascii text",
                        CF_BITMAP: bitmap_image})
    >>> paste_dict = pyperclip.paste([CF_TEXT, CF_UNICODETEXT])  # Pastes only these two
    >>> paste_all = pyperclip.paste([])  # This pastes all available formats into a dictionary

On Mac, this module makes use of the pbcopy and pbpaste commands, which should come with the os.

On Linux, this module makes use of the xclip or xsel commands, which should come with the os. Otherwise run "sudo apt-get install xclip" or "sudo apt-get install xsel" (Note: xsel does not always seem to work.)

Otherwise on Linux, you will need the gtk or PyQt4 modules installed.
