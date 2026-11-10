import os
import subprocess
import sys
import unittest


class TestMainUsageExitCode(unittest.TestCase):
    def test_unknown_flag_exits_nonzero(self):
        src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
        env = dict(os.environ)
        env['PYTHONPATH'] = src + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
        proc = subprocess.run([sys.executable, '-m', 'pyperclip', '--bogus'],
                              capture_output=True, text=True, env=env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('Usage', proc.stdout)


if __name__ == '__main__':
    unittest.main()
