"""
Pyperclip

A cross-platform clipboard module for Python, with copy & paste functions for plain text.
By Al Sweigart al@inventwithpython.com
BSD License

Usage:
  import pyperclip
  pyperclip.copy('The text to be copied to the clipboard.')
  spam = pyperclip.paste()

  if not pyperclip.is_available():
    print("Copy functionality unavailable!")

On Windows, no additional modules are needed.
On Mac, the pyobjc module is used, falling back to the pbcopy and pbpaste cli
    commands. (These commands should come with OS X.).
On Linux, install xclip or xsel via package manager. For example, in Debian:
    sudo apt-get install xclip
    sudo apt-get install xsel

Otherwise on Linux, you will need the gtk or PyQt5/PyQt4 modules installed.

gtk and PyQt4 modules are not available for Python 3,
and this module does not work with PyGObject yet.

Note: There seems to be a way to get gtk on Python 3, according to:
    https://askubuntu.com/questions/697397/python3-is-not-supporting-gtk-module

Cygwin is currently not supported.

Security Note: This module runs programs with these names:
    - which
    - where
    - pbcopy
    - pbpaste
    - xclip
    - xsel
    - klipper
    - qdbus
A malicious user could rename or add programs with these names, tricking
Pyperclip into running them with whatever permissions the Python process has.

"""
__version__ = '1.7.0'

import contextlib
import ctypes
import os
import platform
import subprocess
import sys
import time
import warnings

from ctypes import c_size_t, sizeof, c_wchar_p, get_errno, c_wchar

# `import PyQt4` sys.exit()s if DISPLAY is not in the environment.
# Thus, we need to detect the presence of $DISPLAY manually
# and not load PyQt4 if it is absent.
HAS_DISPLAY = os.getenv("DISPLAY", False)

EXCEPT_MSG = """
    Pyperclip could not find a copy/paste mechanism for your system.
    For more information, please visit: 
    https://pyperclip.readthedocs.io/en/latest/introduction.html#not-implemented-error """

PY2 = sys.version_info[0] == 2

STR_OR_UNICODE = unicode if PY2 else str  # For paste(): Python 3 uses str, Python 2 uses unicode.

ENCODING = 'utf-8'

# The "which" unix command finds where a command is.
if platform.system() == 'Windows':
    WHICH_CMD = 'where'
else:
    WHICH_CMD = 'which'


def _executable_exists(name):
    return subprocess.call([WHICH_CMD, name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0


# Exceptions
class PyperclipException(RuntimeError):
    pass


class PyperclipWindowsException(PyperclipException):
    def __init__(self, message):
        message += " (%s)" % ctypes.WinError()
        super(PyperclipWindowsException, self).__init__(message)


def _stringifyText(text):
    if PY2:
        acceptedTypes = (unicode, str, int, float, bool)
    else:
        acceptedTypes = (str, int, float, bool)
    if not isinstance(text, acceptedTypes):
        raise PyperclipException(
            'only str, int, float, and bool values can be copied to the clipboard, not %s' % text.__class__.__name__)
    return STR_OR_UNICODE(text)


def init_osx_pbcopy_clipboard():
    def copy_osx_pbcopy(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        p = subprocess.Popen(['pbcopy', 'w'],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))

    def paste_osx_pbcopy():
        p = subprocess.Popen(['pbpaste', 'r'],
                             stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        return stdout.decode(ENCODING)

    return copy_osx_pbcopy, paste_osx_pbcopy


def init_osx_pyobjc_clipboard():
    def copy_osx_pyobjc(text):
        """Copy string argument to clipboard"""
        text = _stringifyText(text)  # Converts non-str values to str.
        newStr = Foundation.NSString.stringWithString_(text).nsstring()
        newData = newStr.dataUsingEncoding_(Foundation.NSUTF8StringEncoding)
        board = AppKit.NSPasteboard.generalPasteboard()
        board.declareTypes_owner_([AppKit.NSStringPboardType], None)
        board.setData_forType_(newData, AppKit.NSStringPboardType)

    def paste_osx_pyobjc():
        """Returns contents of clipboard"""
        board = AppKit.NSPasteboard.generalPasteboard()
        content = board.stringForType_(AppKit.NSStringPboardType)
        return content

    return copy_osx_pyobjc, paste_osx_pyobjc


def init_gtk_clipboard():
    global gtk
    import gtk

    def copy_gtk(text):
        global cb
        text = _stringifyText(text)  # Converts non-str values to str.
        cb = gtk.Clipboard()
        cb.set_text(text)
        cb.store()

    def paste_gtk():
        clipboardContents = gtk.Clipboard().wait_for_text()
        # for python 2, returns None if the clipboard is blank.
        if clipboardContents is None:
            return ''
        else:
            return clipboardContents

    return copy_gtk, paste_gtk


def init_qt_clipboard():
    global QApplication
    # $DISPLAY should exist

    # Try to import from qtpy, but if that fails try PyQt5 then PyQt4
    try:
        from qtpy.QtWidgets import QApplication
    except:
        try:
            from PyQt5.QtWidgets import QApplication
        except:
            from PyQt4.QtGui import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    def copy_qt(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        cb = app.clipboard()
        cb.setText(text)

    def paste_qt():
        cb = app.clipboard()
        return STR_OR_UNICODE(cb.text())

    return copy_qt, paste_qt


def init_xclip_clipboard():
    DEFAULT_SELECTION = 'c'
    PRIMARY_SELECTION = 'p'

    def copy_xclip(text, primary=False):
        text = _stringifyText(text)  # Converts non-str values to str.
        selection = DEFAULT_SELECTION
        if primary:
            selection = PRIMARY_SELECTION
        p = subprocess.Popen(['xclip', '-selection', selection],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))

    def paste_xclip(primary=False):
        selection = DEFAULT_SELECTION
        if primary:
            selection = PRIMARY_SELECTION
        p = subprocess.Popen(['xclip', '-selection', selection, '-o'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
        stdout, stderr = p.communicate()
        # Intentionally ignore extraneous output on stderr when clipboard is empty
        return stdout.decode(ENCODING)

    return copy_xclip, paste_xclip


def init_xsel_clipboard():
    DEFAULT_SELECTION = '-b'
    PRIMARY_SELECTION = '-p'

    def copy_xsel(text, primary=False):
        text = _stringifyText(text)  # Converts non-str values to str.
        selection_flag = DEFAULT_SELECTION
        if primary:
            selection_flag = PRIMARY_SELECTION
        p = subprocess.Popen(['xsel', selection_flag, '-i'],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))

    def paste_xsel(primary=False):
        selection_flag = DEFAULT_SELECTION
        if primary:
            selection_flag = PRIMARY_SELECTION
        p = subprocess.Popen(['xsel', selection_flag, '-o'],
                             stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        return stdout.decode(ENCODING)

    return copy_xsel, paste_xsel


def init_klipper_clipboard():
    def copy_klipper(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        p = subprocess.Popen(
            ['qdbus', 'org.kde.klipper', '/klipper', 'setClipboardContents',
             text.encode(ENCODING)],
            stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=None)

    def paste_klipper():
        p = subprocess.Popen(
            ['qdbus', 'org.kde.klipper', '/klipper', 'getClipboardContents'],
            stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()

        # Workaround for https://bugs.kde.org/show_bug.cgi?id=342874
        # TODO: https://github.com/asweigart/pyperclip/issues/43
        clipboardContents = stdout.decode(ENCODING)
        # even if blank, Klipper will append a newline at the end
        assert len(clipboardContents) > 0
        # make sure that newline is there
        assert clipboardContents.endswith('\n')
        if clipboardContents.endswith('\n'):
            clipboardContents = clipboardContents[:-1]
        return clipboardContents

    return copy_klipper, paste_klipper


def init_dev_clipboard_clipboard():
    def copy_dev_clipboard(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        if text == '':
            warnings.warn('Pyperclip cannot copy a blank string to the clipboard on Cygwin. '
                          'This is effectively a no-op.')
        if '\r' in text:
            warnings.warn('Pyperclip cannot handle \\r characters on Cygwin.')

        fo = open('/dev/clipboard', 'wt')
        fo.write(text)
        fo.close()

    def paste_dev_clipboard():
        fo = open('/dev/clipboard', 'rt')
        content = fo.read()
        fo.close()
        return content

    return copy_dev_clipboard, paste_dev_clipboard


def init_no_clipboard():
    class ClipboardUnavailable(object):

        def __call__(self, *args, **kwargs):
            raise PyperclipException(EXCEPT_MSG)

        if PY2:
            def __nonzero__(self):
                return False
        else:
            def __bool__(self):
                return False

    return ClipboardUnavailable(), ClipboardUnavailable()


# Windows-related clipboard functions:
class CheckedCall(object):
    def __init__(self, f):
        super(CheckedCall, self).__setattr__("f", f)

    def __call__(self, *args):
        ret = self.f(*args)
        if not ret and get_errno():
            raise PyperclipWindowsException("Error calling " + self.f.__name__)
        return ret

    def __setattr__(self, key, value):
        setattr(self.f, key, value)


def init_windows_clipboard():
    global HGLOBAL, LPVOID, DWORD, LPCSTR, INT, HWND, HINSTANCE, HMENU, BOOL, UINT, HANDLE
    global CF_BITMAP, CF_DIB, CF_DIBV5, CF_DIF, CF_DSPBITMAP, CF_DSPENHMETAFILE, CF_DSPMETAFILEPICT, CF_DSPTEXT
    global CF_ENHMETAFILE, CF_GDIOBJFIRST, CF_GDIOBJLAST, CF_HDROP, CF_LOCALE, CF_METAFILEPICT, CF_OEMTEXT
    global CF_OWNERDISPLAY, CF_PALETTE, CF_PENDATA, CF_PRIVATEFIRST, CF_PRIVATELAST, CF_RIFF, CF_SYLK, CF_TEXT
    global CF_TIFF, CF_UNICODETEXT, CF_WAVE, CF_ALL, TEXT_FORMATS_NEEDING_ENCONDING

    from ctypes.wintypes import (HGLOBAL, LPVOID, DWORD, LPCSTR, INT, HWND,
                                 HINSTANCE, HMENU, BOOL, UINT, HANDLE, CHAR)
    from ctypes import string_at

    windll = ctypes.windll
    msvcrt = ctypes.CDLL('msvcrt')

    safeCreateWindowExA = CheckedCall(windll.user32.CreateWindowExA)
    safeCreateWindowExA.argtypes = [DWORD, LPCSTR, LPCSTR, DWORD, INT, INT,
                                    INT, INT, HWND, HMENU, HINSTANCE, LPVOID]
    safeCreateWindowExA.restype = HWND

    safeDestroyWindow = CheckedCall(windll.user32.DestroyWindow)
    safeDestroyWindow.argtypes = [HWND]
    safeDestroyWindow.restype = BOOL

    OpenClipboard = windll.user32.OpenClipboard
    OpenClipboard.argtypes = [HWND]
    OpenClipboard.restype = BOOL

    safeCloseClipboard = CheckedCall(windll.user32.CloseClipboard)
    safeCloseClipboard.argtypes = []
    safeCloseClipboard.restype = BOOL

    safeEnumClipboardFormats = CheckedCall(windll.user32.EnumClipboardFormats)
    safeEnumClipboardFormats.argtypes = [INT]
    safeEnumClipboardFormats.restype = UINT

    safeGetClipboardFormatName = CheckedCall(windll.user32.GetClipboardFormatNameW)
    safeGetClipboardFormatName.argtypes = [INT, LPCSTR]
    safeGetClipboardFormatName.restype = UINT

    safeEmptyClipboard = CheckedCall(windll.user32.EmptyClipboard)
    safeEmptyClipboard.argtypes = []
    safeEmptyClipboard.restype = BOOL

    safeGetClipboardData = CheckedCall(windll.user32.GetClipboardData)
    safeGetClipboardData.argtypes = [UINT]
    safeGetClipboardData.restype = HANDLE

    safeSetClipboardData = CheckedCall(windll.user32.SetClipboardData)
    safeSetClipboardData.argtypes = [UINT, HANDLE]
    safeSetClipboardData.restype = HANDLE

    safeGlobalAlloc = CheckedCall(windll.kernel32.GlobalAlloc)
    safeGlobalAlloc.argtypes = [UINT, c_size_t]
    safeGlobalAlloc.restype = HGLOBAL

    safeGlobalLock = CheckedCall(windll.kernel32.GlobalLock)
    safeGlobalLock.argtypes = [HGLOBAL]
    safeGlobalLock.restype = LPVOID

    safeGlobalUnlock = CheckedCall(windll.kernel32.GlobalUnlock)
    safeGlobalUnlock.argtypes = [HGLOBAL]
    safeGlobalUnlock.restype = BOOL

    safeGlobalSize = CheckedCall(windll.kernel32.GlobalSize)
    safeGlobalSize.argtypes = [HGLOBAL]
    safeGlobalSize.restyoe = UINT

    wcslen = CheckedCall(msvcrt.wcslen)
    wcslen.argtypes = [c_wchar_p]
    wcslen.restype = UINT

    GMEM_MOVEABLE = 0x0002

    # Standard Clipboard Formats in Windows
    # Constant = value          # Description
    CF_BITMAP = 2  # A handle to a bitmap (HBITMAP).
    CF_DIB = 8  # A memory object containing a BITMAPINFO structure followed by the bitmap bits.
    CF_DIBV5 = 17  # A memory object containing a BITMAPV5HEADER structure followed by the bitmap color
    #              space information and the bitmap bits.
    CF_DIF = 5  # Software Arts' Data Interchange Format.
    CF_DSPBITMAP = 0x0082  # Bitmap display format associated with a private format. The hMem parameter must be a
    #                      handle to data that can be displayed in bitmap format in lieu of the privately
    #                      formatted data.
    CF_DSPENHMETAFILE = 0x008E  # Enhanced metafile display format associated with a private format.
    #                           The hMem parameter must be a handle to data that can be displayed in enhanced metafile
    #                           format in lieu of the privately formatted data.
    CF_DSPMETAFILEPICT = 0x0083  # Metafile-picture display format associated with a private format. The hMem parameter
    #                            must be a handle to data that can be displayed in metafile-picture format in lieu of
    #                            the privately formatted data.
    CF_DSPTEXT = 0x0081  # Text display format associated with a private format. The hMem parameter must be a
    #                    handle to data that can be displayed in text format in lieu of the privately formatted data.
    CF_ENHMETAFILE = 14  # A handle to an enhanced metafile (HENHMETAFILE).
    CF_GDIOBJFIRST = 0x0300  # Start of a range of integer values for application-defined GDI object clipboard
    #                        formats. The end of the range is CF_GDIOBJLAST.
    #                        Handles associated with clipboard formats in this range are not automatically deleted
    #                        using the GlobalFree function when the clipboard is emptied. Also, when using values
    #                        in this range, the hMem parameter is not a handle to a GDI object, but is a handle
    #                        allocated by the GlobalAlloc function with the GMEM_MOVEABLE flag.
    CF_GDIOBJLAST = 0x03FF  # See CF_GDIOBJFIRST.
    CF_HDROP = 15  # A handle to type HDROP that identifies a list of files. An application can retrieve
    #              information about the files by passing the handle to the DragQueryFile function.
    CF_LOCALE = 16  # The data is a handle to the locale identifier associated with text in the clipboard.
    #                When you close the clipboard, if it contains CF_TEXT data but no CF_LOCALE data, the
    #                system automatically sets the CF_LOCALE format to the current input language. You can
    #                use the CF_LOCALE format to associate a different locale with the clipboard text.
    #                An application that pastes text from the clipboard can retrieve this format to
    #                determine which character set was used to generate the text.
    #                Note that the clipboard does not support plain text in multiple character sets.
    #                To achieve this, use a formatted text data type such as RTF instead.
    #                The system uses the code page associated with CF_LOCALE to implicitly convert from
    #                CF_TEXT to CF_UNICODETEXT. Therefore, the correct code page table is used for the
    #                conversion.
    CF_METAFILEPICT = 3  # Handle to a metafile picture format as defined by the METAFILEPICT structure. When
    #                    passing a CF_METAFILEPICT handle by means of DDE, the application responsible for
    #                    deleting hMem should also free the metafile referred to by the CF_METAFILEPICT handle.
    CF_OEMTEXT = 7  # Text format containing characters in the OEM character set. Each line ends with a
    #               carriage return/linefeed (CR-LF) combination. A null character signals the end of the
    #               data.
    CF_OWNERDISPLAY = 0x0080  # Owner-display format. The clipboard owner must display and update the clipboard viewer
    #                         window, and receive the WM_ASKCBFORMATNAME, WM_HSCROLLCLIPBOARD, WM_PAINTCLIPBOARD,
    #                         WM_SIZECLIPBOARD, and WM_VSCROLLCLIPBOARD messages. The hMem parameter must be NULL.
    CF_PALETTE = 9  # Handle to a color palette. Whenever an application places data in the clipboard that
    #               depends on or assumes a color palette, it should place the palette on the clipboard as
    #               well.
    #               If the clipboard contains data in the CF_PALETTE (logical color palette) format, the
    #               application should use the SelectPalette and RealizePalette functions to realize
    #               (compare) any other data in the clipboard against that logical palette.
    #               When displaying clipboard data, the clipboard always uses as its current palette any
    #               object on the clipboard that is in the CF_PALETTE format.
    CF_PENDATA = 10  # Data for the pen extensions to the Microsoft Windows for Pen Computing.
    CF_PRIVATEFIRST = 0x0200  # Start of a range of integer values for private clipboard formats. The range ends with
    #                         CF_PRIVATELAST. Handles associated with private clipboard formats are not freed
    #                         automatically; the clipboard owner must free such handles, typically in response to
    #                         the WM_DESTROYCLIPBOARD message.
    CF_PRIVATELAST = 0x02FF  # See CF_PRIVATEFIRST.
    CF_RIFF = 11  # Represents audio data more complex than can be represented in a CF_WAVE standard wave format.
    CF_SYLK = 4  # Microsoft Symbolic Link (SYLK) format.
    CF_TEXT = 1  # Text format. Each line ends with a carriage return/linefeed (CR-LF) combination.
    #            A null character signals the end of the data. Use this format for ANSI text.
    CF_TIFF = 6  # Tagged-image file format.
    CF_UNICODETEXT = 13  # Unicode text format. Each line ends with a carriage return/linefeed (CR-LF)
    #                    combination. A null character signals the end of the data.
    CF_WAVE = 12  # Represents audio data in one of the standard wave formats, such as 11 kHz or
    #             22 kHz PCM.

    CF_ALL = []  # If passing an iterable to the paste function, it will retrieve all available formats

    STANDARD_FORMAT_DESCRIPTION = {
        # Identifier: "Descriptor",
        CF_BITMAP: "BITMAP",
        CF_DIB: "DIB",
        CF_DIBV5: "DIBV5",
        CF_DIF: "DIF",
        CF_DSPBITMAP: "DSP BITMAP",
        CF_DSPENHMETAFILE: "DSP ENHMETAFILE",
        CF_DSPMETAFILEPICT: "DSP METAFILEPICT",
        CF_DSPTEXT: "DSP TEXT",
        CF_ENHMETAFILE: "ENHMETAFILE",
        CF_GDIOBJFIRST: "GDIOBJ FIRST",
        CF_GDIOBJLAST: "GDIOBJ LAST",
        CF_HDROP: "Handle Drag and DROP",
        CF_LOCALE: "LOCALE",
        CF_METAFILEPICT: "METAFILE PICT",
        CF_OEMTEXT: "OEM TEXT",
        CF_OWNERDISPLAY: "OWNER DISPLAY",
        CF_PALETTE: "PALETTE",
        CF_PENDATA: "Microsoft PEN DATA",
        CF_PRIVATEFIRST: "PRIVATE FIRST",
        CF_PRIVATELAST: "PRIVATE LAST",
        CF_RIFF: "RIFF",
        CF_SYLK: "SYLK",
        CF_TEXT: "TEXT",
        CF_TIFF: "TIFF",
        CF_UNICODETEXT: "UNICODE TEXT",
        CF_WAVE: "WAVE",
    }
    TEXT_FORMATS_NEEDING_ENCONDING = (CF_TEXT, CF_DSPTEXT)

    @contextlib.contextmanager
    def window():
        """
        Context that provides a valid Windows hwnd.
        """
        # we really just need the hwnd, so setting "STATIC"
        # as predefined lpClass is just fine.
        hwnd = safeCreateWindowExA(0, b"STATIC", None, 0, 0, 0, 0, 0,
                                   None, None, None, None)
        try:
            yield hwnd
        finally:
            safeDestroyWindow(hwnd)

    @contextlib.contextmanager
    def clipboard(hwnd):
        """
        Context manager that opens the clipboard and prevents
        other applications from modifying the clipboard content.
        """
        # We may not get the clipboard handle immediately because
        # some other application is accessing it (?)
        # We try for at least 500ms to get the clipboard.
        t = time.time() + 0.5
        success = False
        while time.time() < t:
            success = OpenClipboard(hwnd)
            if success:
                break
            time.sleep(0.01)
        if not success:
            raise PyperclipWindowsException("Error calling OpenClipboard")

        try:
            yield
        finally:
            safeCloseClipboard()

    def copy_windows(text_or_dict, clip_format=CF_UNICODETEXT):
        # This function is heavily based on
        # http://msdn.com/ms649016#_win32_Copying_Information_to_the_Clipboard

        if isinstance(text_or_dict, dict):
            text_dict = text_or_dict
        else:
            text_dict = {clip_format: text_or_dict}

        with window() as hwnd:
            # http://msdn.com/ms649048
            # If an application calls OpenClipboard with hwnd set to NULL,
            # EmptyClipboard sets the clipboard owner to NULL;
            # this causes SetClipboardData to fail.
            # => We need a valid hwnd to copy something.
            with clipboard(hwnd):
                safeEmptyClipboard()

                for clip_format, text in text_dict.items():
                    if (not PY2) and (not isinstance(text, bytes)):
                        text = _stringifyText(text)  # Converts non-str values to str.
                        if clip_format in TEXT_FORMATS_NEEDING_ENCONDING:
                            text = text.encode(ENCODING)

                    if text:
                        # http://msdn.com/ms649051
                        # If the hMem parameter identifies a memory object,
                        # the object must have been allocated using the
                        # function with the GMEM_MOVEABLE flag.
                        if (not PY2) and isinstance(text, bytes):  # This passes in an 8 bit format.
                            count = len(text) + 1
                            handle = safeGlobalAlloc(GMEM_MOVEABLE,
                                                     count * sizeof(CHAR))
                            locked_handle = safeGlobalLock(handle)
                            ctypes.memmove(LPCSTR(locked_handle), LPCSTR(text), count * sizeof(CHAR))

                            safeGlobalUnlock(handle)
                            safeSetClipboardData(clip_format, handle)
                        else:
                            count = wcslen(text) + 1
                            handle = safeGlobalAlloc(GMEM_MOVEABLE,
                                                     count * sizeof(c_wchar))
                            locked_handle = safeGlobalLock(handle)
                            ctypes.memmove(c_wchar_p(locked_handle), c_wchar_p(text), count * sizeof(c_wchar))

                            safeGlobalUnlock(handle)
                            safeSetClipboardData(clip_format, handle)

    def paste_windows(clip_format=CF_UNICODETEXT):
        """If passing a clip format it will get the """
        with clipboard(None):
            if isinstance(clip_format, (list, tuple)):
                answer = {}
                if len(clip_format) == 0:
                    # Will retrieve the list of available formats
                    clip_formats = []
                    clip_format = safeEnumClipboardFormats(0)
                    while clip_format:
                        clip_formats.append(clip_format)
                        clip_format = safeEnumClipboardFormats(clip_format)
                else:
                    clip_formats = [clip_format, ]  # Make it iterable

                for clip_format in clip_formats:
                    handle = safeGetClipboardData(clip_format)
                    if not handle:
                        answer[clip_format] = None
                    else:
                        if clip_format in (CF_UNICODETEXT,):
                            text = c_wchar_p(handle).value
                        else:
                            size = safeGlobalSize(handle)
                            text = string_at(safeGlobalLock(handle), size)
                            safeGlobalUnlock(handle)
                            if clip_format in TEXT_FORMATS_NEEDING_ENCONDING:
                                text.decode(ENCODING)
                        answer[clip_format] = text
                        # answer[clip_format] = c_wchar_p(handle).value.encode('UTF-16')
                return answer
            else:
                handle = safeGetClipboardData(clip_format)
                if not handle:
                    # GetClipboardData may return NULL with errno == NO_ERROR
                    # if the clipboard is empty.
                    # (Also, it may return a handle to an empty buffer,
                    # but technically that's not empty)
                    return ""
                if clip_format in (CF_UNICODETEXT,):
                    return c_wchar_p(handle).value
                else:
                    size = safeGlobalSize(handle)
                    text = string_at(safeGlobalLock(handle), size)
                    safeGlobalUnlock(handle)
                    if clip_format in TEXT_FORMATS_NEEDING_ENCONDING:
                        text.decode(ENCODING)
                    return text

    return copy_windows, paste_windows


def init_wsl_clipboard():
    def copy_wsl(text):
        text = _stringifyText(text)  # Converts non-str values to str.
        p = subprocess.Popen(['clip.exe'],
                             stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode(ENCODING))

    def paste_wsl():
        p = subprocess.Popen(['powershell.exe', '-command', 'Get-Clipboard'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
        stdout, stderr = p.communicate()
        # WSL appends "\r\n" to the contents.
        return stdout[:-2].decode(ENCODING)

    return copy_wsl, paste_wsl


# Automatic detection of clipboard mechanisms and importing is done in deteremine_clipboard():
def determine_clipboard():
    """
    Determine the OS/platform and set the copy() and paste() functions
    accordingly.
    """

    global Foundation, AppKit, gtk, qtpy, PyQt4, PyQt5

    # Setup for the CYGWIN platform:
    if 'cygwin' in platform.system().lower():  # Cygwin has a variety of values returned by platform.system(),
        #                                      such as 'CYGWIN_NT-6.1'
        # FIXME: pyperclip currently does not support Cygwin,
        # see https://github.com/asweigart/pyperclip/issues/55
        if os.path.exists('/dev/clipboard'):
            warnings.warn(
                'Pyperclip\'s support for Cygwin is not perfect, see https://github.com/asweigart/pyperclip/issues/55')
            return init_dev_clipboard_clipboard()

    # Setup for the WINDOWS platform:
    elif os.name == 'nt' or platform.system() == 'Windows':
        return init_windows_clipboard()

    if platform.system() == 'Linux':
        with open('/proc/version', 'r') as f:
            if "Microsoft" in f.read():
                return init_wsl_clipboard()

    # Setup for the MAC OS X platform:
    if os.name == 'mac' or platform.system() == 'Darwin':
        try:
            import Foundation  # check if pyobjc is installed
            import AppKit
        except ImportError:
            return init_osx_pbcopy_clipboard()
        else:
            return init_osx_pyobjc_clipboard()

    # Setup for the LINUX platform:
    if HAS_DISPLAY:
        try:
            import gtk  # check if gtk is installed
        except ImportError:
            pass  # We want to fail fast for all non-ImportError exceptions.
        else:
            return init_gtk_clipboard()

        if _executable_exists("xsel"):
            return init_xsel_clipboard()
        if _executable_exists("xclip"):
            return init_xclip_clipboard()
        if _executable_exists("klipper") and _executable_exists("qdbus"):
            return init_klipper_clipboard()

        try:
            # qtpy is a small abstraction layer that lets you write applications using a single api call to either
            # PyQt or PySide.
            # https://pypi.python.org/pypi/QtPy
            import qtpy  # check if qtpy is installed
        except ImportError:
            # If qtpy isn't installed, fall back on importing PyQt4.
            try:
                import PyQt5  # check if PyQt5 is installed
            except ImportError:
                try:
                    import PyQt4  # check if PyQt4 is installed
                except ImportError:
                    pass  # We want to fail fast for all non-ImportError exceptions.
                else:
                    return init_qt_clipboard()
            else:
                return init_qt_clipboard()
        else:
            return init_qt_clipboard()

    return init_no_clipboard()


def set_clipboard(clipboard):
    """
    Explicitly sets the clipboard mechanism. The "clipboard mechanism" is how
    the copy() and paste() functions interact with the operating system to
    implement the copy/paste feature. The clipboard parameter must be one of:
        - pbcopy
        - pbobjc (default on Mac OS X)
        - gtk
        - qt
        - xclip
        - xsel
        - klipper
        - windows (default on Windows)
        - no (this is what is set when no clipboard mechanism can be found)
    """
    global copy, paste

    clipboard_types = {'pbcopy': init_osx_pbcopy_clipboard,
                       'pyobjc': init_osx_pyobjc_clipboard,
                       'gtk': init_gtk_clipboard,
                       'qt': init_qt_clipboard,  # TODO - split this into 'qtpy', 'pyqt4', and 'pyqt5'
                       'xclip': init_xclip_clipboard,
                       'xsel': init_xsel_clipboard,
                       'klipper': init_klipper_clipboard,
                       'windows': init_windows_clipboard,
                       'no': init_no_clipboard}

    if clipboard not in clipboard_types:
        raise ValueError('Argument must be one of %s' % (', '.join([repr(_) for _ in clipboard_types.keys()])))

    # Sets pyperclip's copy() and paste() functions:
    copy, paste = clipboard_types[clipboard]()


def lazy_load_stub_copy(text):
    """
    A stub function for copy(), which will load the real copy() function when
    called so that the real copy() function is used for later calls.

    This allows users to import pyperclip without having determine_clipboard()
    automatically run, which will automatically select a clipboard mechanism.
    This could be a problem if it selects, say, the memory-heavy PyQt4 module
    but the user was just going to immediately call set_clipboard() to use a
    different clipboard mechanism.

    The lazy loading this stub function implements gives the user a chance to
    call set_clipboard() to pick another clipboard mechanism. Or, if the user
    simply calls copy() or paste() without calling set_clipboard() first,
    will fall back on whatever clipboard mechanism that determine_clipboard()
    automatically chooses.
    """
    global copy, paste
    copy, paste = determine_clipboard()
    return copy(text)


def lazy_load_stub_paste(make_it_pass_in_the_first_run=None):
    """
    A stub function for paste(), which will load the real paste() function when
    called so that the real paste() function is used for later calls.

    This allows users to import pyperclip without having determine_clipboard()
    automatically run, which will automatically select a clipboard mechanism.
    This could be a problem if it selects, say, the memory-heavy PyQt4 module
    but the user was just going to immediately call set_clipboard() to use a
    different clipboard mechanism.

    The lazy loading this stub function implements gives the user a chance to
    call set_clipboard() to pick another clipboard mechanism. Or, if the user
    simply calls copy() or paste() without calling set_clipboard() first,
    will fall back on whatever clipboard mechanism that determine_clipboard()
    automatically chooses.
    """
    global copy, paste
    copy, paste = determine_clipboard()
    if make_it_pass_in_the_first_run is not None:
        return paste(make_it_pass_in_the_first_run)
    return paste()


def is_available():
    return copy != lazy_load_stub_copy and paste != lazy_load_stub_paste


# Initially, copy() and paste() are set to lazy loading wrappers which will
# set `copy` and `paste` to real functions the first time they're used, unless
# set_clipboard() or determine_clipboard() is called first.
copy, paste = lazy_load_stub_copy, lazy_load_stub_paste

__all__ = ['copy', 'paste', 'set_clipboard', 'determine_clipboard']
