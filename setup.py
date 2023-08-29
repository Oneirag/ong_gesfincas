from setuptools import setup

from ong_utils.desktop_shortcut import PipCreateShortcut

setup(cmdclass={'bdist_wheel': PipCreateShortcut})
