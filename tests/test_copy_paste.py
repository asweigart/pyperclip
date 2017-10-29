# coding: utf-8
import string
import unittest
import random
import os
import platform
import subprocess

import sys
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
os.environ['PATH'] = os.path.join(project_root, 'bin') + os.pathsep + os.environ['PATH']

import pyperclip
from pyperclip import _executable_exists, HAS_DISPLAY
from pyperclip.clipboards import (init_osx_pbcopy_clipboard, init_osx_pyobjc_clipboard,
                                  init_gtk_clipboard, init_qt_clipboard,
                                  init_xclip_clipboard, init_xsel_clipboard,
                                  init_klipper_clipboard, init_no_clipboard)
from pyperclip.windows import init_windows_clipboard


class _TestClipboard(unittest.TestCase):
    clipboard = None
    supports_unicode = True

    @property
    def copy(self):
        return self.clipboard[0]

    @property
    def paste(self):
        return self.clipboard[1]

    def setUp(self):
        if not self.clipboard:
            self.skipTest("Clipboard not supported.")

    def test_copy_simple(self):
        self.copy("pyper\r\nclip")

    def test_copy_paste_simple(self):
        msg = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(1000))
        self.copy(msg)
        self.assertEqual(self.paste(), msg)

    def test_copy_paste_whitespace(self):
        msg = ''.join(random.choice(string.whitespace) for _ in range(1000))
        self.copy(msg)
        self.assertEqual(self.paste(), msg)

    def test_copy_blank(self):
        self.copy('TEST')
        self.copy('')
        self.assertEqual(self.paste(), '')

    def test_copy_unicode(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        self.copy(u"ಠ_ಠ")

    def test_copy_unicode_emoji(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        self.copy(u"🙆")

    def test_copy_paste_unicode(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        msg = u"ಠ_ಠ"
        self.copy(msg)
        self.assertEqual(self.paste(), msg)

    def test_copy_paste_unicode_emoji(self):
        if not self.supports_unicode:
            raise unittest.SkipTest()
        msg = u"🙆"
        self.copy(msg)
        self.assertEqual(self.paste(), msg)


class TestCygwin(_TestClipboard):
    if 'cygwin' in platform.system().lower():
        clipboard = init_windows_clipboard(True)


class TestWindows(_TestClipboard):
    if os.name == 'nt' or platform.system() == 'Windows':
        clipboard = init_windows_clipboard()


class TestOSX(_TestClipboard):
    if os.name == 'posix' or platform.system() == 'Darwin':
        try:
            import Foundation  # check if pyobjc is installed
            import AppKit
        except ImportError:
            clipboard = init_osx_pbcopy_clipboard() # TODO
        else:
            clipboard = init_osx_pyobjc_clipboard()


class TestGtk(_TestClipboard):
    if HAS_DISPLAY:
        try:
            import gtk
        except ImportError:
            pass
        else:
            clipboard = init_gtk_clipboard()


class TestQt(_TestClipboard):
    if HAS_DISPLAY:
        try:
            import PyQt5
        except ImportError:
            try:
                import PyQt4
            except ImportError:
                pass
            else:
                clipboard = init_qt_clipboard()
        else:
            clipboard = init_qt_clipboard()


class TestXClip(_TestClipboard):
    if _executable_exists("xclip"):
        clipboard = init_xclip_clipboard()


class TestXSel(_TestClipboard):
    if _executable_exists("xsel"):
        clipboard = init_xsel_clipboard()


class TestKlipper(_TestClipboard):
    if _executable_exists("klipper") and _executable_exists("qdbus"):
        clipboard = init_klipper_clipboard()


class TestNoClipboard(unittest.TestCase):
    copy, paste = init_no_clipboard()

    def test_copy(self):
        with self.assertRaises(RuntimeError):
            self.copy("foo")

    def test_paste(self):
        with self.assertRaises(RuntimeError):
            self.paste()

class TestCLI(unittest.TestCase):
    def setUp(self):
        super(TestCLI, self).setUp()
        self.unicode = u"ಠ_ಠ %d\n" % (random.randint(0, 999))

    def _run(this, *args):
        return subprocess.Popen(['pyperclip'] + list(args),
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT
        )

    def test_copy(self):
        proc = self._run('--copy')
        output, _ = proc.communicate((self.unicode).encode('utf-8'))

        self.assertEqual(output, '')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(pyperclip.paste(), self.unicode.strip())

    def test_paste(self):
        pyperclip.copy(self.unicode.strip())
        proc = self._run('--paste')
        output, _ = proc.communicate()

        self.assertEqual(output.decode('utf-8'), self.unicode)
        self.assertEqual(proc.poll(), 0)

if __name__ == '__main__':
    unittest.main()
