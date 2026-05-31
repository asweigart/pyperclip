# coding: utf-8
import string
import unittest
import random
import os
import platform

#import sys
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pyperclip
from pyperclip import _executable_exists, HAS_DISPLAY
from pyperclip import (init_osx_pbcopy_clipboard, init_osx_pyobjc_clipboard,
                                  init_dev_clipboard_clipboard,
                                  init_qt_clipboard,
                                  init_xclip_clipboard, init_xsel_clipboard,
                                  init_wl_clipboard,
                                  init_klipper_clipboard, init_no_clipboard)
from pyperclip import init_windows_clipboard
from pyperclip import init_wsl_clipboard

from pyperclip import PyperclipException

random.seed(42) # Make the "random" tests reproducible.

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

    def test_non_str(self):
        # Test copying an int.
        self.copy(42)
        self.assertEqual(self.paste(), '42')

        self.copy(-1)
        self.assertEqual(self.paste(), '-1')

        # Test copying a float.
        self.copy(3.141592)
        self.assertEqual(self.paste(), '3.141592')

        # Test copying bools.
        self.copy(True)
        self.assertEqual(self.paste(), 'True')

        self.copy(False)
        self.assertEqual(self.paste(), 'False')

        # All other non-str values raise an exception.
        with self.assertRaises(PyperclipException):
            self.copy(None)

        with self.assertRaises(PyperclipException):
            self.copy([2, 4, 6, 8])


class TestCygwin(_TestClipboard):
    if 'cygwin' in platform.system().lower():
        clipboard = init_dev_clipboard_clipboard()


class TestWindows(_TestClipboard):
    if os.name == 'nt' or platform.system() == 'Windows':
        clipboard = init_windows_clipboard()

class TestWSL(_TestClipboard):
    if platform.system() == 'Linux':
        with open('/proc/version', 'r') as f:
            if "Microsoft" in f.read():
                clipboard = init_wsl_clipboard()


class TestOSX(_TestClipboard):
    if os.name == 'mac' or platform.system() == 'Darwin':
        try:
            import Foundation  # check if pyobjc is installed
            import AppKit
        except ImportError:
            clipboard = init_osx_pbcopy_clipboard() # TODO
        else:
            clipboard = init_osx_pyobjc_clipboard()


class TestQt(_TestClipboard):
    if HAS_DISPLAY:
        try:
            import PyQt5.QtWidgets
        except ImportError:
            pass
        else:
            clipboard = init_qt_clipboard()


class TestXClip(_TestClipboard):
    if _executable_exists("xclip"):
        clipboard = init_xclip_clipboard()


class TestXSel(_TestClipboard):
    if _executable_exists("xsel"):
        clipboard = init_xsel_clipboard()


class TestWlClipboard(_TestClipboard):
    if _executable_exists("wl-copy"):
        clipboard = init_wl_clipboard()


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


class TestIsAvailable(unittest.TestCase):
    def setUp(self):
        self.original_copy = pyperclip.copy
        self.original_paste = pyperclip.paste
        self.original_determine_clipboard = pyperclip.determine_clipboard

    def tearDown(self):
        pyperclip.copy = self.original_copy
        pyperclip.paste = self.original_paste
        pyperclip.determine_clipboard = self.original_determine_clipboard

    def test_is_available_detects_clipboard_before_copy_or_paste(self):
        def fake_copy(text):
            pass

        def fake_paste():
            return ''

        def fake_determine_clipboard():
            return fake_copy, fake_paste

        pyperclip.copy = pyperclip.lazy_load_stub_copy
        pyperclip.paste = pyperclip.lazy_load_stub_paste
        pyperclip.determine_clipboard = fake_determine_clipboard

        self.assertTrue(pyperclip.is_available())
        self.assertEqual(pyperclip.copy, fake_copy)
        self.assertEqual(pyperclip.paste, fake_paste)

    def test_is_available_returns_false_when_no_clipboard_is_detected(self):
        pyperclip.copy = pyperclip.lazy_load_stub_copy
        pyperclip.paste = pyperclip.lazy_load_stub_paste
        pyperclip.determine_clipboard = pyperclip.init_no_clipboard

        self.assertFalse(pyperclip.is_available())


if __name__ == '__main__':
    unittest.main()
