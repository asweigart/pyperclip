import unittest
import sys
import os

sys.path.append(os.path.abspath('..'))
import pyperclip


class TestCopyPaste(unittest.TestCase):
    def test_copypaste(self):
        pyVersion = '%s.%s.%s' % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
        print('Testing on: Python %s - %s' % (pyVersion, pyperclip._functions))
        msg = 'The quick brown fox jumped over the yellow lazy dog.'
        pyperclip.copy(msg)
        self.assertEqual(pyperclip.paste(), msg)


if __name__ == '__main__':
    unittest.main()
