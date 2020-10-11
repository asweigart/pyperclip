import re
from setuptools import setup, find_packages

# Load version from module (without loading the whole module)
with open('src/pyperclip/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

# Read in the README.md for the long description.
with open("README.md", "r") as fh:
    long_description = fh.read()

# Dynamically calculate the version based on pyperclip.VERSION.
setup(
    name='pyperclip',
    version=version,
    url='https://github.com/asweigart/pyperclip',
    author='Al Sweigart',
    author_email='al@inventwithpython.com',
    description=('A cross-platform clipboard module for Python. (Only handles plain text for now.)'),
    long_description=long_description,
    license='BSD',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    test_suite='tests',
    keywords="clipboard copy paste clip xsel xclip",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Environment :: MacOS X',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
