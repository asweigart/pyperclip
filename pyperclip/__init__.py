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

NOTE: The _functions variable contains a string describing which copy/paste functions are being used:
    - Windows
    - Cygwin
    - OS X pbcopy/pbpaste
    - xclip command
    - (KDE Klipper) - qdbus (external)
    - gtk module
    - PyQt4 module
    - xsel command
"""

__version__ = '1.5.17'

import platform, os
from subprocess import call, Popen, PIPE

PY2 = '2' == platform.python_version_tuple()[0]
STRING_FUNCTION = unicode if PY2 else str

# constants for copy/paste function types
CYGWIN = 'cygwin'
WINDOWS = 'windows'
PBCOPY_PBPASTE = 'pbcopy/pbpaste'
XCLIP = 'xclip'
XSEL = 'xsel'
KLIPPER = 'klipper'
PYQT4 = 'pyqt4'
GTK = 'gtk'


def _pasteWindows():
    CF_UNICODETEXT = 13
    d = ctypes.windll
    d.user32.OpenClipboard(0)
    handle = d.user32.GetClipboardData(CF_UNICODETEXT)
    data = ctypes.c_wchar_p(handle).value
    d.user32.CloseClipboard()
    return data


def _copyWindows(text):
    GMEM_DDESHARE = 0x2000
    CF_UNICODETEXT = 13
    d = ctypes.windll # cdll expects 4 more bytes in user32.OpenClipboard(0)
    if not isinstance(text, STRING_FUNCTION):
        text = text.decode('mbcs')

    d.user32.OpenClipboard(0)

    d.user32.EmptyClipboard()
    hCd = d.kernel32.GlobalAlloc(GMEM_DDESHARE, len(text.encode('utf-16-le')) + 2)
    pchData = d.kernel32.GlobalLock(hCd)

    # Detects this error: "OSError: exception: access violation writing 0x0000000000000000"
    #if pchData == 0:
    #    assert False, 'GlobalLock() returned NULL. GetLastError() returned' + str(ctypes.GetLastError())

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
    if not isinstance(text, STRING_FUNCTION):
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
    p = Popen(['pbcopy', 'w'], stdin=PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


def _pasteOSX():
    p = Popen(['pbpaste', 'r'], stdout=PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    return stdout.decode('utf-8')


def _pasteGtk():
    clipboardContents = gtk.Clipboard().wait_for_text() # for python 2, returns None if the clipboard is blank.
    if clipboardContents is None:
        return ''
    else:
        return clipboardContents


def _copyGtk(text):
    global cb
    cb = gtk.Clipboard()
    cb.set_text(text)
    cb.store()


def _pasteQt():
    return str(cb.text()) # TODO: should str() be replaced with STRING_FUNCTION()?


def _copyQt(text):
    cb.setText(text)


def _copyXclip(text):
    p = Popen(['xclip', '-selection', 'c'], stdin=PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


def _pasteXclip():
    p = Popen(['xclip', '-selection', 'c', '-o'], stdout=PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    return stdout.decode('utf-8')


def _copyXsel(text):
    p = Popen(['xsel', '-b', '-i'], stdin=PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


def _pasteXsel():
    p = Popen(['xsel', '-b', '-o'], stdout=PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    return stdout.decode('utf-8')


def _copyKlipper(text):
    p = Popen(['qdbus', 'org.kde.klipper', '/klipper',
            'setClipboardContents', text.encode('utf-8')],
             stdin=PIPE, close_fds=True)
    p.communicate(input=None)


def _pasteKlipper():
    p = Popen(['qdbus', 'org.kde.klipper', '/klipper',
            'getClipboardContents'], stdout=PIPE, close_fds=True)
    stdout, stderr = p.communicate()

    # Apparently Klipper has a bug that adds a newline to the end. It was reported in Klipper version 0.20.3 but I've
    # seen it in 0.9.7. The bug is unfixed. This function will remove a newline if the string has one.
    # TODO: In the future, once Klipper is fixed, check the version number to decided whether or not to strip the
    # newline.
    # https://bugs.kde.org/show_bug.cgi?id=342874

    clipboardContents = stdout.decode('utf-8')
    assert len(clipboardContents) > 0 # even if blank, Klipper will append a newline at the end
    assert clipboardContents[-1] == '\n' # make sure that newline is there
    if len(clipboardContents) and clipboardContents[-1] == '\n':
        clipboardContents = clipboardContents[:-1]
    return clipboardContents


def _noCopy(text):
    raise NotImplementedError('Pyperclip could not find a copy/paste mechanism for your system. Please see https://pyperclip.readthedocs.org for how to fix this.')


def _noPaste():
    raise NotImplementedError('Pyperclip could not find a copy/paste mechanism for your system. Please see https://pyperclip.readthedocs.org for how to fix this.')


def setFunctions(functionSet):
    global copy, paste, _functions, app, cb, ctypes, PyQt4, gtk

    if functionSet == CYGWIN:
        import ctypes
        copy = _copyCygwin
        paste = _pasteCygwin
    elif functionSet == WINDOWS:
        import ctypes
        copy = _copyWindows
        paste = _pasteWindows
    elif functionSet == PBCOPY_PBPASTE:
        copy = _copyOSX
        paste = _pasteOSX
    elif functionSet == XCLIP:
        xclipExists = call(['which', 'xclip'],
                    stdout=PIPE, stderr=PIPE) == 0
        assert xclipExists, 'The xclip command could not be found.'
        copy = _copyXclip
        paste = _pasteXclip
    elif functionSet == XSEL:
        xselExists = call(['which', 'xsel'],
                stdout=PIPE, stderr=PIPE) == 0
        assert xselExists, 'The xsel command could not be found.'
    elif functionSet == KLIPPER:
        copy = _copyKlipper
        paste = _pasteKlipper
    elif functionSet == PYQT4:
        import PyQt4.QtCore
        import PyQt4.QtGui
        app = PyQt4.QtGui.QApplication([])
        cb = PyQt4.QtGui.QApplication.clipboard()
        copy = _copyQt
        paste = _pasteQt
    elif functionSet == GTK:
        import gtk
        copy = _copyGtk
        paste = _pasteGtk
    elif functionSet is None:
        copy = _noCopy
        paste = _noPaste
    else:
        assert False, 'There is no function set called "%s".' % (functionSet)

    _functions = functionSet


def determineFunctionSet():
    global gtk, PyQt4

    # Determine the OS/platform and set the copy() and paste() functions accordingly.
    if 'cygwin' in platform.system().lower():
        return CYGWIN
    elif os.name == 'nt' or platform.system() == 'Windows':
        return WINDOWS
    elif os.name == 'mac' or platform.system() == 'Darwin':
        return PBCOPY_PBPASTE
    elif os.name == 'posix' or platform.system() == 'Linux':
        # Determine which command/module is installed, if any.
        try:
            import gtk  # check if gtk is installed
            return GTK
        except ImportError:
            pass

        try:
            import PyQt4.QtCore # check if PyQt4 is installed
            import PyQt4.QtGui
            return PYQT4
        except ImportError:
            pass

        xclipExists = call(['which', 'xclip'],
                    stdout=PIPE, stderr=PIPE) == 0
        if xclipExists:
            return XCLIP

        xselExists = call(['which', 'xsel'],
                stdout=PIPE, stderr=PIPE) == 0
        if xselExists:
            return XSEL

        xklipperExists = (call(['which', 'klipper'],
                stdout=PIPE, stderr=PIPE) == 0 and
                call(['which', 'qdbus'], stdout=PIPE, stderr=PIPE) == 0)
        if xklipperExists:
            return KLIPPER

        return None # will set the functions to _noCopy and _noPaste
    else:
        return None # will set the functions to _noCopy and _noPaste

# Set the appropriate copy/paste functions
setFunctions(determineFunctionSet())
