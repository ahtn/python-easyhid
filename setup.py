#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from setuptools import setup
import os

# Load the version number
try: # python3
    fields = {}
    with open(os.path.join("easyhid", "version.py")) as f:
        exec(f.read(), fields)
    __version__ = fields['__version__']
except: # python2
    execfile(os.path.join("easyhid", "version.py"))

setup(
    name = 'easyhid',
    version = __version__,
    description = "A simple interface to the HIDAPI library.",
    url = "http://github.com/ahtn/python-easyhid",
    author = "jem",
    author_email = "jem@seethis.link",
    license = 'MIT',
    packages = ['easyhid'],
    install_requires = ['cffi'],
    keywords = ['hidapi', 'usb', 'hid'],
    zip_safe = False
)
