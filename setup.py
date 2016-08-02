#!/usr/bin/env python
from setuptools import setup, find_packages, Command
from setuptools.command.test import test

import os, sys, subprocess

class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise SystemExit(
            subprocess.call([sys.executable,
                             'app_test_runner.py',
                             'test_project']))

install_requires = ['six',]
base_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name = "django-dirtyfield",
    version = "1.0",
    description = "Track changed data in Django Models",
    url = "http://github.com/futurice/django-dirtyfield",
    author = "Jussi Vaihia",
    author_email = "jussi.vaihia@futurice.com",
    packages = ["djangodirtyfield"],
    include_package_data = True,
    keywords = 'django model dirty field',
    license = 'BSD',
    install_requires = install_requires,
    tests_require = install_requires,
    cmdclass = {
        'test': TestCommand,
    },
)
