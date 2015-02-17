"""
Pyperclip

A cross-platform clipboard module for Python. (only handles plain text for now)
By Al Sweigart al@inventwithpython.com
BSD License

Usage:
  import pyperclip
  pyperclip.copy('The text to be copied to the clipboard.')
  spam = pyperclip.paste()

On Windows, no additional modules are needed.
On Mac, this module makes use of the pbcopy and pbpaste commands, which should come with the os.
On Linux, this module makes use of the xclip or xsel commands, which should come with the os. Otherwise run "sudo apt-get install xclip" or "sudo apt-get install xsel"
  Otherwise on Linux, you will need the gtk or PyQt4 modules installed.

The gtk module is not available for Python 3, and this module does not work with PyGObject yet.
"""

__version__ = '1.5.8'

import platform, os
from subprocess import call, Popen, PIPE


PY2 = '2' == platform.python_version_tuple()[0]
text_type = unicode if PY2 else str


def _pasteWindows():
    CF_UNICODETEXT = 13
    d = ctypes.windll
    d.user32.OpenClipboard(0 if PY2 else None)
    handle = d.user32.GetClipboardData(CF_UNICODETEXT)
    data = ctypes.c_wchar_p(handle).value
    d.user32.CloseClipboard()
    return data


def _copyWindows(text):
    GMEM_DDESHARE = 0x2000
    CF_UNICODETEXT = 13
    d = ctypes.windll # cdll expects 4 more bytes in user32.OpenClipboard(0)
    if not isinstance(text, text_type):
        text = text.decode('mbcs')

    d.user32.OpenClipboard(0 if PY2 else None)

    d.user32.EmptyClipboard()
    hCd = d.kernel32.GlobalAlloc(GMEM_DDESHARE, len(text.encode('utf-16-le')) + 2)
    pchData = d.kernel32.GlobalLock(hCd)
    ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(pchData), text)
    d.kernel32.GlobalUnlock(hCd)
    d.user32.SetClipboardData(CF_UNICODETEXT, hCd)
    d.user32.CloseClipboard()


def _pasteCygwin():
    CF_UNICODETEXT = 13
    d = ctypes.cdll
    d.user32.OpenClipboard(0)
    handle = d.user32.GetClipboardData(CF_UNICODETEXT)
    data = ctypes.c_wchar_p(handle).value
    d.user32.CloseClipboard()
    return data


def _copyCygwin(text):
    GMEM_DDESHARE = 0x2000
    CF_UNICODETEXT = 13
    d = ctypes.cdll
    if not isinstance(text, text_type):
        text = text.decode('mbcs')
    d.user32.OpenClipboard(0)
    d.user32.EmptyClipboard()
    hCd = d.kernel32.GlobalAlloc(GMEM_DDESHARE, len(text.encode('utf-16-le')) + 2)
    pchData = d.kernel32.GlobalLock(hCd)
    ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(pchData), text)
    d.kernel32.GlobalUnlock(hCd)
    d.user32.SetClipboardData(CF_UNICODETEXT, hCd)
    d.user32.CloseClipboard()


def _copyOSX(text):
    text = str(text)
    p = Popen(['pbcopy', 'w'], stdin=PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


def _pasteOSX():
    p = Popen(['pbpaste', 'r'], stdout=PIPE, close_fds=True)
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
    p = Popen(['xclip', '-selection', 'c'], stdin=PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


def _pasteXclip():
    p = Popen(['xclip', '-selection', 'c', '-o'], stdout=PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    return bytes.decode(stdout)


def _copyXsel(text):
    p = Popen(['xsel', '-b', '-i'], stdin=PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


def _pasteXsel():
    p = Popen(['xsel', '-b', '-o'], stdout=PIPE, close_fds=True)
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
