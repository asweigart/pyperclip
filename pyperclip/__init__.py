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

__version__ = '1.5.15'

import platform, os
from subprocess import call, Popen, PIPE


PY2 = '2' == platform.python_version_tuple()[0]
text_type = unicode if PY2 else str


def _setWindowsArgs():
    import ctypes.wintypes as wt
    
    u32 = ctypes.windll.user32
    
    u32.OpenClipboard.restype = wt.BOOL
    u32.OpenClipboard.argtypes = [wt.HWND]
    
    u32.EmptyClipboard.restype = wt.BOOL
    u32.EmptyClipboard.argtypes = []
    
    u32.SetClipboardData.restype = wt.HANDLE
    u32.SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
    
    u32.GetClipboardData.restype = wt.HANDLE
    u32.GetClipboardData.argtypes = [wt.UINT]
    
    u32.CloseClipboard.restype = wt.BOOL
    u32.CloseClipboard.argtypes = []

    k32 = ctypes.windll.kernel32

    k32.GlobalAlloc.restype = wt.HGLOBAL
    k32.GlobalAlloc.argtypes = [wt.UINT, ctypes.c_void_p]

    k32.GlobalLock.restype = wt.LPVOID
    k32.GlobalLock.argtypes = [wt.HGLOBAL]

    k32.GlobalUnlock.restype = wt.BOOL
    k32.GlobalUnlock.argtypes = [wt.HGLOBAL]


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
    if not isinstance(text, text_type):
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
    p = Popen(['pbcopy', 'w'], stdin=PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


def _pasteOSX():
    p = Popen(['pbpaste', 'r'], stdout=PIPE, close_fds=True)
    stdout, stderr = p.communicate()
    return stdout.decode('utf-8')


def _pasteGtk():
    return gtk.Clipboard().wait_for_text()


def _copyGtk(text):
    global cb
    cb = gtk.Clipboard()
    cb.set_text(text)
    cb.store()


def _pasteQt():
    return str(cb.text())


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
    return stdout.decode('utf-8')

# Determine the OS/platform and set the copy() and paste() functions accordingly.
if 'cygwin' in platform.system().lower():
    _functions = 'Cygwin' # for debugging
    import ctypes
    paste = _pasteCygwin
    copy = _copyCygwin
elif os.name == 'nt' or platform.system() == 'Windows':
    _functions = 'Windows' # for debugging
    import ctypes
    _setWindowsArgs()
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

    xklipperExists = (call(['which', 'klipper'],
            stdout=PIPE, stderr=PIPE) == 0 and
            call(['which', 'qdbus'], stdout=PIPE, stderr=PIPE) == 0)

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
    elif xklipperExists:
        _functions = '(KDE Klipper) - qdbus (external)' # for debugging
        paste = _pasteKlipper
        copy = _copyKlipper
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
