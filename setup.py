#!/usr/bin/env python

import logging
import os

import setuptools
from setuptools.command.install import install


class PostInstall(install):
    """Executes custon post_install function after standard install"""
    def run(self):
        print(self)
        install.run(self)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        logging_file = os.path.expanduser(f'~/{self.distribution.metadata.name}-install.log')
        # configure the handler and formatter for logger2
        handler2 = logging.FileHandler(logging_file, mode='w')
        formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

        # add formatter to the handler
        handler2.setFormatter(formatter2)
        # add handler to the logger
        self.logger.addHandler(handler2)
        self.logger.debug(f"{logging_file=}")

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
            self.logger.debug(f"{install_path=}")
            if os.path.isdir(install_path):
                if inst_type == "dist":
                    self.logger.debug("Dist install found")
                    # Look for RECORD file and add shortcut info
                    # TODO: verify processing of RECORD file
                    record_file = os.path.join(install_path, "RECORD")
                    self.logger.debug(f"{record_file=}")
                    if os.path.isfile(record_file):
                        with open(scut_filename, "r") as f:
                            scut_content = f.read()
                            len_scut = len(scut_content)
                        self.logger.debug(f"{scut_content=}")
                        import hashlib
                        import base64
                        sha256 = base64.urlsafe_b64encode(hashlib.sha256(scut_content.encode()).digest())[:-1]
                        txt_append_record_file = f"{scut_filename},sha256={sha256},{len_scut}"
                    else:
                        txt_append_record_file = f"{scut_filename},,"
                    self.logger.debug(f"{txt_append_record_file=}")
                    with open(record_file, "a") as f:
                        f.writelines([txt_append_record_file])
                elif inst_type == "egg":
                    # add line to the (could be non-existing) file installed-files.txt
                    self.logger.debug("Egg install found")
                    with open(os.path.join(install_path, "installed-files.txt"), "a") as f:
                        f.writelines([scut_filename])
            else:
                self.logger.debug("Directory not found")


if __name__ == "__main__":
    setuptools.setup()
