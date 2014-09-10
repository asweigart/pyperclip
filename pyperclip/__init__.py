# Pyperclip

# A cross-platform clipboard module for Python. (only handles plain text for now)
# By Al Sweigart al@inventwithpython.com
# BSD License

# Usage:
#   import pyperclip
#   pyperclip.copy('The text to be copied to the clipboard.')
#   spam = pyperclip.paste()

# On Windows, no additional modules are needed.
# On Mac, this module makes use of the pbcopy and pbpaste commands, which should come with the os.
# On Linux, this module makes use of the xclip or xsel commands, which should come with the os. Otherwise run "sudo apt-get install xclip" or "sudo apt-get install xsel"
#   Otherwise on Linux, you will need the gtk or PyQt4 modules installed.

# The gtk module is not available for Python 3, and this module does not work with PyGObject yet.


__version__ = '1.5.4'

import platform, os
from subprocess import call, Popen, PIPE

def _pasteWindows():
    ctypes.windll.user32.OpenClipboard(0)
    pcontents = ctypes.windll.user32.GetClipboardData(1) # 1 is CF_TEXT
    data = ctypes.c_char_p(pcontents).value
    #ctypes.windll.kernel32.GlobalUnlock(pcontents)
    ctypes.windll.user32.CloseClipboard()

    if type(data) == bytes:
        # Running on Python 3
        data = data.decode() # utf-8 by default, which is possibly not correct. TODO - check this
    return data


def _copyWindows(text):
    text = str(text)
    GMEM_DDESHARE = 0x2000
    ctypes.windll.user32.OpenClipboard(0)
    ctypes.windll.user32.EmptyClipboard()
    try:
        # works on Python 2 (bytes() only takes one argument)
        hCd = ctypes.windll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(text))+1)
    except TypeError:
        # works on Python 3 (bytes() requires an encoding)
        hCd = ctypes.windll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(text, 'ascii'))+1)
    pchData = ctypes.windll.kernel32.GlobalLock(hCd)
    try:
        # works on Python 2 (bytes() only takes one argument)
        ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(pchData), bytes(text))
    except TypeError:
        # works on Python 3 (bytes() requires an encoding)
        ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(pchData), bytes(text, 'ascii'))
    ctypes.windll.kernel32.GlobalUnlock(hCd)
    ctypes.windll.user32.SetClipboardData(1, hCd)
    ctypes.windll.user32.CloseClipboard()


def _pasteCygwin():
    ctypes.cdll.user32.OpenClipboard(0)
    pcontents = ctypes.cdll.user32.GetClipboardData(1) # 1 is CF_TEXT
    data = ctypes.c_char_p(pcontents).value
    #ctypes.cdll.kernel32.GlobalUnlock(pcontents)
    ctypes.cdll.user32.CloseClipboard()

    if type(data) == bytes:
        # Running on Python 3
        data = data.decode() # utf-8 by default, which is possibly not correct. TODO - check this
    return data


def _copyCygwin(text):
    text = str(text)
    GMEM_DDESHARE = 0x2000
    ctypes.cdll.user32.OpenClipboard(0)
    ctypes.cdll.user32.EmptyClipboard()
    try:
        # works on Python 2 (bytes() only takes one argument)
        hCd = ctypes.cdll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(text))+1)
    except TypeError:
        # works on Python 3 (bytes() requires an encoding)
        hCd = ctypes.cdll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(text, 'ascii'))+1)
    pchData = ctypes.cdll.kernel32.GlobalLock(hCd)
    try:
        # works on Python 2 (bytes() only takes one argument)
        ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(pchData), bytes(text))
    except TypeError:
        # works on Python 3 (bytes() requires an encoding)
        ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(pchData), bytes(text, 'ascii'))
    ctypes.cdll.kernel32.GlobalUnlock(hCd)
    ctypes.cdll.user32.SetClipboardData(1, hCd)
    ctypes.cdll.user32.CloseClipboard()


def _copyOSX(text):
    text = str(text)
    p = Popen(['pbcopy', 'w'], stdin=PIPE)
    try:
        # works on Python 3 (bytes() requires an encoding)
        p.communicate(input=bytes(text, 'utf-8'))
    except TypeError:
        # works on Python 2 (bytes() only takes one argument)
        p.communicate(input=bytes(text))


def _pasteOSX():
    p = Popen(['pbpaste', 'r'], stdout=PIPE)
    stdout, stderr = p.communicate()
    return bytes.decode(stdout)


def _pasteGtk():
    return gtk.Clipboard().wait_for_text()


def _copyGtk(text):
    global cb
    text = str(text)
    cb = gtk.Clipboard()
    cb.set_text(text)
    cb.store()


def _pasteQt():
    return str(cb.text())


def _copyQt(text):
    text = str(text)
    cb.setText(text)


def _copyXclip(text):
    p = Popen(['xclip', '-selection', 'c'], stdin=PIPE)
    try:
        # works on Python 3 (bytes() requires an encoding)
        p.communicate(input=bytes(text, 'utf-8'))
    except TypeError:
        # works on Python 2 (bytes() only takes one argument)
        p.communicate(input=bytes(text))


def _pasteXclip():
    p = Popen(['xclip', '-selection', 'c', '-o'], stdout=PIPE)
    stdout, stderr = p.communicate()
    return bytes.decode(stdout)


def _copyXsel(text):
    p = Popen(['xsel', '-i'], stdin=PIPE)
    try:
        # works on Python 3 (bytes() requires an encoding)
        p.communicate(input=bytes(text, 'utf-8'))
    except TypeError:
        # works on Python 2 (bytes() only takes one argument)
        p.communicate(input=bytes(text))


def _pasteXsel():
    p = Popen(['xsel', '-o'], stdout=PIPE)
    stdout, stderr = p.communicate()
    return bytes.decode(stdout)



# Determine the OS/platform and set the copy() and paste() functions accordingly.
if 'cygwin' in platform.system().lower():
    _functions = 'Cygwin' # for debugging
    import ctypes
    paste = _pasteCygwin
    copy = _copyCygwin
elif os.name == 'nt' or platform.system() == 'Windows':
    _functions = 'Windows' # for debugging
    import ctypes
    paste = _pasteWindows
    copy = _copyWindows
elif os.name == 'mac' or platform.system() == 'Darwin':
    _functions = 'OS X pbcopy/pbpaste' # for debugging
    paste = _pasteOSX
    copy = _copyOSX
elif os.name == 'posix' or platform.system() == 'Linux':
    # Determine which command/module is installed, if any.
    xclipExists = call(['which', 'xclip'],
                stdout=PIPE, stderr=PIPE) == 0

    xselExists = call(['which', 'xsel'],
            stdout=PIPE, stderr=PIPE) == 0

    gtkInstalled = False
    try:
        # Check it gtk is installed.
        import gtk
        gtkInstalled = True
    except ImportError:
        pass

    if not gtkInstalled:
        # Check if PyQt4 is installed.
        PyQt4Installed = False
        try:
            import PyQt4.QtCore
            import PyQt4.QtGui
            PyQt4Installed = True
        except ImportError:
            pass

    # Set one of the copy & paste functions.
    if xclipExists:
        _functions = 'xclip command' # for debugging
        paste = _pasteXclip
        copy = _copyXclip
    elif gtkInstalled:
        _functions = 'gtk module' # for debugging
        paste = _pasteGtk
        copy = _copyGtk
    elif PyQt4Installed:
        _functions = 'PyQt4 module' # for debugging
        app = PyQt4.QtGui.QApplication([])
        cb = PyQt4.QtGui.QApplication.clipboard()
        paste = _pasteQt
        copy = _copyQt
    elif xselExists:
        # TODO: xsel doesn't seem to work on Raspberry Pi (my test Linux environment). Putting this as the last method tried.
        _functions = 'xsel command' # for debugging
        paste = _pasteXsel
        copy = _copyXsel
    else:
        raise Exception('Pyperclip requires the xclip or xsel application, or the gtk or PyQt4 module.')
else:
    raise RuntimeError('pyperclip does not support your system.')
