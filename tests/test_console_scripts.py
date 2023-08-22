"""
Tests that console_scripts defined in setup.py work properly
    entry_points={
            'console_scripts': [
                'ong_gesfincas=ong_gesfincas.liquidaciones_gui:main',
                'punteo=ong_gesfincas.conciliation_gui:main',
            ],
        },
"""
from unittest import TestCase, main

from ong_gesfincas.conciliation_gui import main as punteo
from ong_gesfincas.liquidaciones_gui import main as liquidaciones


class TestConsole(TestCase):
    def test_punteo(self):
        punteo()

    def test_liquidaciones(self):
        liquidaciones()


if __name__ == '__main__':
    main()


