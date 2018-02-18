#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from setuptools import setup

setup(
    name = 'easyhid',
    version = '0.0.3',
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
