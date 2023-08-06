"""
Tests that console_scripts defined in setup.py work properly
    entry_points={
            'console_scripts': [
                'liquidaciones=liquidaciones.liquidaciones_gui:main',
                'punteo=liquidaciones.conciliation_gui:main',
            ],
        },
"""
from unittest import TestCase, main
from liquidaciones.conciliation_gui import main as punteo
from liquidaciones.liquidaciones_gui import main as liquidaciones


class TestConsole(TestCase):
    def test_punteo(self):
        punteo()

    def test_liquidaciones(self):
        liquidaciones()


if __name__ == '__main__':
    main()


