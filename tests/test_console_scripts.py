"""
Tests that console_scripts defined in pyproject.toml work properly
[project.scripts]
liquidaciones = "ong_gesfincas.liquidaciones_gui:main"
punteo = "ong_gesfincas.conciliation_gui:main"
"""
from unittest import TestCase, main

from src.ong_gesfincas.conciliation_gui import main as punteo
from src.ong_gesfincas.liquidaciones_gui import main as liquidaciones


class TestConsole(TestCase):
    def test_punteo(self):
        punteo()

    def test_liquidaciones(self):
        liquidaciones()


if __name__ == '__main__':
    main()


