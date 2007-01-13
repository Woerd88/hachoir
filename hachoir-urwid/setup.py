#!/usr/bin/env python

try:
    from setuptools import setup
    with_setuptools = True
except ImportError:
    from distutils.core import setup
    with_setuptools = False

URL = 'http://hachoir.org/wiki/hachoir-urwid'
CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']

def main():
    import hachoir_urwid
    install_options = {
        "name": 'hachoir-urwid',
        "version": hachoir_urwid.__version__,
        "url": URL,
        "download_url": URL,
        "author": "Julien Muchembled and Victor Stinner",
        "description": "Binary file explorer using Hachoir and urwid libraries",
        "long_description": open('README').read(),
        "classifiers": CLASSIFIERS,
        "license": 'GNU GPL v2',
        "scripts": ["hachoir-urwid"],
        "packages": ["hachoir_urwid"],
        "package_dir": {"hachoir_urwid": "hachoir_urwid"},
    }
    if with_setuptools:
        install_options["install_requires"] = ("hachoir-core>=0.7.0", "hachoir-parser>=0.7.0", "urwid>=0.9.4")
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

