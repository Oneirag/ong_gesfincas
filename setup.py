#!/usr/bin/env python

import setuptools
from setuptools.command.install import install


class PostInstall(install):
    """Executes custon post_install function after standard install"""
    def run(self):
        print(self)
        install.run(self)
        self.post_install()

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

        with open(scut_filename, "r") as f:
            scut_content = f.read()
            len_scut = len(scut_content)
        lib_base = self.install_lib
        package = self.distribution.metadata.name
        version = self.distribution.metadata.version
        python_version = self.config_vars.get('py_version_short')
        for inst_type in "dist", "egg":
            install_path = "{lib_base}{package}-{version}{python_version_str}.{inst_type}-info".format(
                lib_base=lib_base, package=package, version=version,
                python_version_str=f"-py{python_version}" if "egg" else "",
                inst_type=inst_type
            )
            if os.path.isdir(install_path):
                if inst_type == "dist":
                    # Look for RECORD file and add shortcut info
                    # TODO: verify processing of RECORD file
                    record_file = os.path.join(install_path, "RECORD")
                    import hashlib
                    import base64
                    sha256 = base64.urlsafe_b64encode(hashlib.sha256(scut_content.encode()).digest())
                    with open(record_file, "a") as f:
                        f.writelines([f"{scut_filename},sha256={sha256},{len_scut}"])
                elif inst_type == "egg":
                    # add line to the (could be non-existing) file installed-files.txt
                    with open(os.path.join(install_path, "installed-files.txt"), "a") as f:
                        f.writelines([scut_filename])


if __name__ == "__main__":
    setuptools.setup()
