import pyperclip
import sys

if len(sys.argv) > 1 and sys.argv[1] in ('-c', '--copy'):
    pyperclip.copy(sys.stdin.read())
elif len(sys.argv) > 1 and sys.argv[1] in ('-p', '--paste'):
    sys.stdout.write(pyperclip.paste())
else:
    print('Usage: python -m pyperclip [-c | --copy] | [-p | --paste]')
    print()
    print('When copying, stdin will be placed on the clipboard.')
    print('When pasting, the clipboard will be written to stdout.')