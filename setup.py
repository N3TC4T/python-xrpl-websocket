#!/usr/bin/env python
# coding: utf-8
import os
from setuptools import setup, find_packages


# read the contents of README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst')) as f:
    long_description = f.read()

VERSION = "0.1.0.rc3"
NAME = "xrpl_websocket"

install_requires = [
    'websocket-client==0.56.0',
    'wsaccel'
]

setup(
    name=NAME,
    version=VERSION,
    description="XRL Websocket Client",
    long_description=long_description,
    author="N3TC4T",
    author_email="netcat.av@gmail.com",
    url="https://github.com/N3TC4T/python-xrpl-websocket",
    license="Apache2",
    packages=find_packages(exclude=['tests*']),
    zip_safe=True,
    python_requires='>=2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        'License :: OSI Approved :: Apache Software License',
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    keywords='xrp, ledger, ripple, websocket',
)

