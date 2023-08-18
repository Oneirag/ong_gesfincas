#!/usr/bin/env python

import setuptools
from setuptools.command.install import install


def post_install():
    """Creates a shortcut in desktop after install"""
    # TODO: find PYTHONHOME/Lib/site-packages/{package}{version}.dist-info, add an extra line with the shortcut
    import os.path

    from pyshortcuts import make_shortcut, platform, shortcut, get_folders

    iconfile = 'shovel.icns' if platform.startswith('darwin') else 'shovel.ico'
    script = '_ -m liquidaciones.conciliation_gui'
    name = 'Punteo de cuentas'
    scut = shortcut(script=script, name=name, userfolders=get_folders())
    scut_filename = os.path.join(scut.desktop_dir, scut.target)
    # Not needed: shortcuts are not overwritten using make_shortcut
    # if os.path.exists(scut_filename):
    #     os.remove(scut_filename)
    retva = make_shortcut(script=script, name=name, icon=None,
                          description="Lanzador de la interfaz del punteo de cuentas",
                          startmenu=False)


class PostInstall(install):
    def run(self):
        install.run(self)
        post_install()


if __name__ == "__main__":
    setuptools.setup()
