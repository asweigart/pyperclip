import sys
import subprocess
from .exceptions import PyperclipException

PY2 = sys.version_info[0] == 2


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
        if text is '':
            return

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
        # Obtain the version from the cli bin.
        version = Popen(['klipper', '--version'], stdout=PIPE, close_fds=True)
    
        version = version.communicate(input=None)
        version = version[0]
        version = version[8:] # Remove klipper from the string.
        version = version[:-1] # Remove \n from the string.
        
        stdout, stderr = p.communicate()
    
        if version == '0.20.3' or version == '0.9.7':
            return _klipper_fix_newline(stdout.decode('utf-8'))

        return stdout.decode('utf-8')

    return copy_klipper, paste_klipper

def _klipper_fix_newline(text):
    # Apparently Klipper has a bug that adds a newline to the end. It was reported in Klipper version 0.20.3 but I've
    # seen it in 0.9.7. The bug is unfixed. This function will remove a newline if the string has one.
    # https://bugs.kde.org/show_bug.cgi?id=342874

    clipboardContents = text
    if len(clipboardContents) and clipboardContents[-1] == '\n':
        clipboardContents = clipboardContents[:-1]
    return clipboardContents


def init_no_clipboard():
    class ClipboardUnavailable(object):
        def __call__(self, *args, **kwargs):
            raise PyperclipException(
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
