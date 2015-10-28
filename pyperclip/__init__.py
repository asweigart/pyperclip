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

__version__ = '1.5.16'

import platform, os, re
from subprocess import call, Popen, PIPE


PY2 = '2' == platform.python_version_tuple()[0]
text_type = unicode if PY2 else str


class HtmlClipboard(object):
    """
    Parsed clipboard from the raw byte string "HTML Format" clipboard
    """
    def __init__(self, raw):
        def read_value(name):
            match = re.search(r'\s{0}:(\d+)\s'.format(name), raw)
            return int(match.groups()[0])
        self.raw = raw
        self.header = {}
        start = read_value('StartHTML')
        if start == -1:
            start = read_value('StartFragment')
        for line in raw[:start].splitlines():
            key, val = line.split(':', 1)
            self.header[key] = int(val) if val.isdigit() else val
        if not 'StartSelection' in self.header:
            self.header['StartSelection'] = self.header['StartFragment']
            self.header['EndSelection'] = self.header['EndFragment']

    @property
    def html(self):
        "The selection plus all parent tags and the head"
        return self.raw[self.header['StartHTML']:self.header['EndHTML']].decode('utf-8')

    @property
    def fragment(self):
        "The Selection plus added opening and closing tags"
        return self.raw[self.header['StartFragment']:self.header['EndFragment']].decode('utf-8')

    @property
    def selection(self):
        "The copied selection"
        return self.raw[self.header['StartSelection']:self.header['EndSelection']].decode('utf-8')

    @property
    def source(self):
        "Source URL"
        return self.header.get('SourceURL')

    if PY2:
        def __str__(self):
            return self.fragment.encode('utf-8')

        def __unicode__(self):
            return self.fragment
    else:
        def __str__(self):
            return self.fragment


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

def _paste_as_htmlWindows():
    """
    Get Clipboard data in the HTML Format, if available

    It is supported by: All web browsers, MS Office and many other software.

    Properties:
        html
            The selection plus all parent tags and the head
        fragment
            The Selection plus added opening and closing tags
        selection
            "The copied selection
        source
            Source URL (optional)

        raw
            The raw clipboard data in the "HTML Format" as described in
            https://msdn.microsoft.com/en-us/library/aa767917%28v=vs.85%29.aspx
    """
    d = ctypes.windll
    wu = d.user32
    if not d.user32.OpenClipboard(0):
        raise OSError("Clipboard is locked by other app")
    data = None
    u_format = wu.EnumClipboardFormats(None)
    while u_format:
        buf = ctypes.create_unicode_buffer(100)
        _st_len = wu.GetClipboardFormatNameW(u_format, ctypes.byref(buf), len(buf))
        if buf.value == 'HTML Format':
            handle = d.user32.GetClipboardData(u_format)
            size = d.kernel32.GlobalSize(handle)
            data = ctypes.c_char_p(handle).value
            # The data from web browsers are null terminated but not from ms office,
            # so it is size or size-1 characters long.
            data = HtmlClipboard(data[:size])
            break
        u_format = wu.EnumClipboardFormats(u_format)
    wu.CloseClipboard()
    return data


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
    paste_as_html = _paste_as_htmlWindows
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
