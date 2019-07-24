"""setup instructions for setuptools."""

import os
from setuptools import setup, find_packages

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), "r") as fptr:
        return fptr.read()

setup(
    name="tinyos",
    version="2.1.2.3",
    description="Highly experimental TinyOS python tools (Unofficial Packaging)",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(exclude="tests"),
    install_requires=["pyserial"],
    test_suite="nose.collector",
    tests_require=["nose"],
)
