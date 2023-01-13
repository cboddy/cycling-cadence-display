#!/usr/bin/env python3
from setuptools import find_packages, setup


def get_long_description():
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="cycling-cadence-display",
    version="0.1.0",
    packages=find_packages(),
    author="Chris Boddy",
    author_email="chris@boddy.im",
    zip_safe=False,
    url="https://github.com/cboddy/cycling-cadence-display",
    description="A terminal-user-interface to display a dashboard of information about a cycling cadence meter via Bluetooth",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    install_requires=[
        "bleak",
        "pandas",
        "termplotlib",
        "rich",
        "pycycling",
    ],
    entry_points={
        "console_scripts": ["cycling_cadence_display = cycling_cadence_display.app:main"],
    },
    tests_require=["pytest", "mock", "freezegun"],
)
