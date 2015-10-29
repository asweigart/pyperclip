
from setuptools import setup


# Dynamically calculate the version based on pyperclip.VERSION.
setup(
    name='pyperclip',
    version=__import__('pyperclip').__version__,
    url='https://github.com/asweigart/pyperclip',
    author='Al Sweigart',
    author_email='al@inventwithpython.com',
    description=('A cross-platform clipboard module for Python. (only handles plain text for now)'),
    license='BSD',
    packages=['pyperclip'],
    test_suite='tests',
    keywords="gui automation test testing keyboard mouse cursor click press keystroke control",
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
    ],
)