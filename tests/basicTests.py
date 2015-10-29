# -*- coding: utf-8 -*-

import unittest
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pyperclip
from pyperclip import CYGWIN, WINDOWS, PBCOPY_PBPASTE, XCLIP, XSEL, KLIPPER, PYQT4, GTK

import platform
RUNNING_PY2 = '2' == platform.python_version_tuple()[0]

ALL_FUNCTION_SETS = (CYGWIN, WINDOWS, PBCOPY_PBPASTE, XCLIP, XSEL, KLIPPER, PYQT4, GTK)

# The user can specify which set of copy/paste functions to use instead of the default. The names are given as strings in OVERRIDE_FUNCTION_SET.
OVERRIDE_FUNCTION_SET = None
if len(sys.argv) > 1:
    OVERRIDE_FUNCTION_SET = sys.argv[1]
    assert OVERRIDE_FUNCTION_SET in ALL_FUNCTION_SETS, 'Function set specified must be one of: %s' % (ALL_FUNCTION_SETS)

if OVERRIDE_FUNCTION_SET is not None:
    pyperclip.setFunctions(OVERRIDE_FUNCTION_SET)

class TestCopyPaste(unittest.TestCase):
    def test_copyPaste(self):
        #pyVersion = '%s.%s.%s' % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
        #print('Testing on: Python %s - %s' % (pyVersion, pyperclip._functions))
        msg = 'The quick brown fox jumped over the yellow lazy dog.'
        pyperclip.copy(msg)
        self.assertEqual(pyperclip.paste(), msg)

    def test_randomCopyPaste(self):
        # This random version of the test_copyPaste() test is so that previous text on the clipboard does not cause a false positive.
        random.seed = 42
        msg = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890' * 3)
        random.shuffle(msg)
        msg = ''.join(msg)
        pyperclip.copy(msg)
        self.assertEqual(pyperclip.paste(), msg)

    def test_copyUnicode(self):
        pyperclip.copy('ಠ_ಠ')

    def test_pasteUnicode(self):
        if not RUNNING_PY2: # TODO: Can't get this test to work right under Python 2.
            pyperclip.copy('ಠ_ಠ')
            self.assertEqual(pyperclip.paste(), 'ಠ_ಠ')

    def test_copyBlank(self):
        pyperclip.copy('TEST')
        pyperclip.copy('')
        self.assertEqual(pyperclip.paste(), '')


class TestFunctionSets(unittest.TestCase):
    def test_determineFunctionSet(self):
        self.assertIn(pyperclip.determineFunctionSet(), ALL_FUNCTION_SETS)


if __name__ == '__main__':
    unittest.main()
