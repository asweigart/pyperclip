import sys, subprocess, ctypes

PY2 = sys.version_info[0] == 2
text_type = unicode if PY2 else str


def init_windows_clipboard(cygwin=False):
    if cygwin:
        d = ctypes.cdll
    else:
        d = ctypes.windll

    CF_UNICODETEXT = 13
    GMEM_DDESHARE = 0x2000

    def copy_windows(text):
        if not isinstance(text, text_type):
            text = text.decode('mbcs')

        d.user32.OpenClipboard(0)
        d.user32.EmptyClipboard()
        hCd = d.kernel32.GlobalAlloc(GMEM_DDESHARE, len(text.encode('utf-16-le')) + 2)
        pchData = d.kernel32.GlobalLock(hCd)

        # Detects this error: "OSError: exception: access violation writing 0x0000000000000000"
        # if pchData == 0:
        #    assert False, 'GlobalLock() returned NULL. GetLastError() returned' + str(ctypes.GetLastError())

        ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(pchData), text)
        d.kernel32.GlobalUnlock(hCd)
        d.user32.SetClipboardData(CF_UNICODETEXT, hCd)
        d.user32.CloseClipboard()

    def paste_windows():
        d.user32.OpenClipboard(0)
        handle = d.user32.GetClipboardData(CF_UNICODETEXT)
        data = ctypes.c_wchar_p(handle).value
        d.user32.CloseClipboard()
        return data

    return copy_windows, paste_windows


def init_osx_clipboard():
    def copy_osx(text):
        p = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode('utf-8'))

    def paste_osx():
        p = subprocess.Popen(['pbpaste', 'r'], stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        return stdout.decode('utf-8')

    return copy_osx, paste_osx


def init_gtk_clipboard():
    import gtk

    def copy_gtk(text):
        global cb
        cb = gtk.Clipboard()
        cb.set_text(text)
        cb.store()

    def paste_gtk():
        clipboardContents = gtk.Clipboard().wait_for_text()  # for python 2, returns None if the clipboard is blank.
        if clipboardContents is None:
            return ''
        else:
            return clipboardContents

    return copy_gtk, paste_gtk


def init_qt_clipboard():
    # We must not import PyQt4 at the top,
    # because `import PyQt4` sys.exit()s if $DISPLAY is not set on unix systems.
    import PyQt4.QtGui

    # FIXME: This segfaults on one of my systems?
    app = PyQt4.QtGui.QApplication([])  # TODO: is this required?
    cb = PyQt4.QtGui.QApplication.clipboard()

    def copy_qt(text):
        cb.setText(text)

    def paste_qt():
        return str(cb.text())  # TODO: should str() be replaced with STRING_FUNCTION()?

    return copy_qt, paste_qt


def init_xclip_clipboard():
    def copy_xclip(text):
        p = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode('utf-8'))

    def paste_xclip():
        p = subprocess.Popen(['xclip', '-selection', 'c', '-o'], stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        return stdout.decode('utf-8')

    return copy_xclip, paste_xclip


def init_xsel_clipboard():
    def copy_xsel(text):
        p = subprocess.Popen(['xsel', '-b', '-i'], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode('utf-8'))

    def paste_xsel():
        p = subprocess.Popen(['xsel', '-b', '-o'], stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        return stdout.decode('utf-8')

    return copy_xsel, paste_xsel


def init_klipper_clipboard():
    def copy_klipper(text):
        p = subprocess.Popen(
            ['qdbus', 'org.kde.klipper', '/klipper', 'setClipboardContents', text.encode('utf-8')],
            stdin=subprocess.PIPE,
            close_fds=True
        )
        p.communicate(input=None)

    def paste_klipper():
        p = subprocess.Popen(
            ['qdbus', 'org.kde.klipper', '/klipper', 'getClipboardContents'],
            stdout=subprocess.PIPE,
            close_fds=True
        )
        stdout, stderr = p.communicate()

        # Apparently Klipper has a bug that adds a newline to the end. It was reported in Klipper version 0.20.3 but I've
        # seen it in 0.9.7. The bug is unfixed. This function will remove a newline if the string has one.
        # TODO: In the future, once Klipper is fixed, check the version number to decided whether or not to strip the
        # newline.
        # https://bugs.kde.org/show_bug.cgi?id=342874

        clipboardContents = stdout.decode('utf-8')
        assert len(clipboardContents) > 0  # even if blank, Klipper will append a newline at the end
        assert clipboardContents[-1] == '\n'  # make sure that newline is there
        if len(clipboardContents) and clipboardContents[-1] == '\n':
            clipboardContents = clipboardContents[:-1]
        return clipboardContents

    return copy_klipper, paste_klipper


def init_no_clipboard():
    class ClipboardUnavailable(object):
        def __call__(self, *args, **kwargs):
            raise RuntimeError(
                'Pyperclip could not find a copy/paste mechanism for your system. '
                'Please see https://pyperclip.readthedocs.org for how to fix this.'
            )

        if PY2:
            def __nonzero__(self):
                return False
        else:
            def __bool__(self):
                return False

    return ClipboardUnavailable(), ClipboardUnavailable()
