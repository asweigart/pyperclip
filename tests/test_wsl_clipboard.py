import base64
import shutil
import subprocess
import unittest
from unittest import mock

import pyperclip


class TestWSLClipboard(unittest.TestCase):
    def test_paste_decodes_unicode_without_stripping_text(self):
        text = '  Turkish: \u00e7\u011f\u0131\u015f; emoji: \U0001f600\r\nnext line\n'
        output = base64.b64encode(text.encode('utf-8')) + b'\r\n'
        with mock.patch('pyperclip.subprocess.Popen') as popen:
            popen.return_value.communicate.return_value = (output, b'')
            _, paste = pyperclip.init_wsl_clipboard()
            self.assertEqual(paste(), text)

    def test_paste_preserves_powershell_error_reporting(self):
        with mock.patch('pyperclip.subprocess.Popen') as popen:
            popen.return_value.communicate.return_value = (b'', b'synthetic failure')
            _, paste = pyperclip.init_wsl_clipboard()
            with self.assertRaisesRegex(Exception, 'synthetic failure'):
                paste()


@unittest.skipUnless(shutil.which('powershell.exe'), 'Windows PowerShell is not available')
class TestWSLPowerShellScript(unittest.TestCase):
    def paste_synthetic(self, value):
        # Replace only the clipboard command; execute the backend's actual script.
        # These tests never access or modify the system clipboard.
        if value is None:
            expression = '$null'
        else:
            encoded = base64.b64encode(value.encode('utf-8')).decode('ascii')
            expression = "[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('%s'))" % encoded
        prefix = 'function Get-Clipboard { %s }; ' % expression
        real_popen = subprocess.Popen

        def synthetic_popen(args, **kwargs):
            return real_popen(args[:-1] + [prefix + args[-1]], **kwargs)

        with mock.patch('pyperclip.subprocess.Popen', side_effect=synthetic_popen):
            _, paste = pyperclip.init_wsl_clipboard()
            return paste()

    def test_null_clipboard_returns_empty_string(self):
        self.assertEqual(self.paste_synthetic(None), '')

    def test_empty_string_returns_empty_string(self):
        self.assertEqual(self.paste_synthetic(''), '')

    def test_text_and_whitespace_are_preserved(self):
        for text in ['  \t\r\n', 'Turkish: \u00e7\u011f\u0131\u015f; \U0001f600', 'first\r\nsecond\n']:
            with self.subTest(text=text):
                self.assertEqual(self.paste_synthetic(text), text)


if __name__ == '__main__':
    unittest.main()
