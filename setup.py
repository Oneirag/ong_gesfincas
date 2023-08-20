#!/usr/bin/env python

import setuptools
from setuptools.command.install import install


def post_install(self):
    """Creates a shortcut in desktop after install"""

    import os
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

    lib_base = self.install_lib
    package = self.distribution.metadata.name
    version = self.distribution.metadata.version
    python_version = self.config_vars.get('py_version_short')
    for inst_type in "dist", "egg":
        install_basepath = f"{lib_base}{package}-{version}-py{python_version}.{inst_type}-info"
        if os.path.isdir(install_basepath):
            if inst_type == "dist":
                # Look for RECORD file and add shortcut info
                record_file = os.path.join(install_basepath, "RECORD")
                # TODO: process RECORD file
            elif inst_type == "egg":
                # add line to the (could be non-existing) file installed-files.txt
                with open(os.path.join(install_basepath, "installed-files.txt"), "a") as f:
                    f.writelines([scut_filename])


class PostInstall(install):
    def run(self):
        print(self)
        install.run(self)
        post_install(self)


if __name__ == "__main__":
    setuptools.setup()
