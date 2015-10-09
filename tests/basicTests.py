# -*- coding: utf-8 -*-

import unittest
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pyperclip

import platform
RUNNING_PY2 = '2' == platform.python_version_tuple()[0]

class TestCopyPaste(unittest.TestCase):
    def test_copyPaste(self):
        pyVersion = '%s.%s.%s' % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
        print('Testing on: Python %s - %s' % (pyVersion, pyperclip._functions))
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

if __name__ == '__main__':
    unittest.main()
