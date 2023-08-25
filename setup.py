#!/usr/bin/env python

import logging
import os

import setuptools
from setuptools.command.build_py import build_py
from setuptools.command.dist_info import dist_info
from setuptools.command.egg_info import egg_info
from setuptools.command.install import install
from setuptools.command.install_egg_info import install_egg_info
from setuptools.command.install_lib import install_lib
from setuptools.command.sdist import sdist
from wheel.bdist_wheel import bdist_wheel


class CustomBdistWheel(bdist_wheel):
    def run(self):
        bdist_wheel.run(self)
        # Look for the wheel and change RECORD file
        impl_tag, abi_tag, plat_tag = self.get_tag()
        archive_basename = f"{self.wheel_dist_name}-{impl_tag}-{abi_tag}-{plat_tag}"
        wheel_path = os.path.join(self.dist_dir, archive_basename + ".whl")
        # Open wheel and edit RECORD file
        import zipfile
        # generate a temp file
        tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(wheel_path))
        os.close(tmpfd)
        # create a temp copy of the archive without filename
        with zipfile.ZipFile(wheel_path, 'r') as zin:
            with zipfile.ZipFile(tmpname, 'w') as zout:
                zout.comment = zin.comment  # preserve the comment
                for item in zin.infolist():
                    if not item.filename.endswith("RECORD"):
                        zout.writestr(item, zin.read(item.filename))
                    else:
                        # Write custom record file here
                        data = zin.read(item.filename)
                        data += "/Users/oneirag/Desktop/Punteo de cuentas.app,,\n".encode("utf-8")
                        zout.writestr(item, data)
        # replace with the temp archive
        os.remove(wheel_path)
        os.rename(tmpname, wheel_path)
        pass


class CustomDistInfo(dist_info):
    def run(self) -> None:
        dist_info.run(self)
        pass


class CustomBuildPy(build_py):

    def run(self) -> None:
        build_py.run(self)
        pass


import tarfile
import tempfile
import io


class CustomEggInfo(egg_info):

    def find_sources(self) -> None:
        # Add my custom installed-files.txt here
        # Create the installed-files.txt
        with open(os.path.join(self.egg_info, "installed-files.txt"), "w") as f:
            f.write("/Users/oneirag/Desktop/Punteo de cuentas.app\n")
        egg_info.find_sources(self)


def append_tar_file(buf, file_name, output_path, replace=True):
    """
    append a buf to an existing tar file if not already there, or if replace=True
    """
    if not os.path.isfile(output_path):
        return

    with tempfile.TemporaryDirectory() as tempdir:
        tmp_path = os.path.join(tempdir, 'tmp.tar.gz')

        with tarfile.open(output_path, "r:gz") as tar:
            if not replace:
                if file_name in (member.name for member in tar):
                    return

            if isinstance(buf, str):
                buf = buf.encode("utf-8")

            fileobj = io.BytesIO(buf)
            tarinfo = tarfile.TarInfo(file_name)
            tarinfo.size = len(fileobj.getvalue())

            with tarfile.open(tmp_path, "w:gz") as tmp:
                for member in tar:
                    if member.name != file_name:
                        tmp.addfile(member, tar.extractfile(member.name))
                tmp.addfile(tarinfo, fileobj)

        os.rename(tmp_path, output_path)


class CustomSdist(sdist):

    def make_distribution(self) -> None:
        package = self.distribution.get_name()
        package_name = self.distribution.get_fullname()
        egg_info_dir = f"{package}.egg-info/"
        self.mkpath(egg_info_dir)
        # Create the installed-files.txt
        with open(os.path.join(egg_info_dir, "installed-files.txt")) as f:
            f.write("/Users/oneirag/Desktop/Punteo de cuentas.app\n")
        sdist.make_distribution(self)
        pass

    def run(self) -> None:
        sdist.run(self)
        return
        package = self.distribution.get_name()
        package_name = self.distribution.get_fullname()

        old_targz_file = self.distribution.dist_files[-1][-1]
        append_tar_file(buf='/Users/oneirag/Desktop/Punteo de cuentas.app\n',
                        file_name=f"{package_name}/{package}.egg-info/installed-files.txt",
                        output_path=old_targz_file)
        return

        import tarfile

        new_targz_file = "dist/new.tar.gz"
        data = '/Users/oneirag/Desktop/Punteo de cuentas.app\n'.encode('utf8')
        info = tarfile.TarInfo(name='installed-files.txt')
        info.size = len(data)
        with tarfile.open(new_targz_file, "w:gz") as new_tar:
            with tarfile.open(old_targz_file, 'r:gz') as old_tar:
                for tarinfo in old_tar:
                    new_tar.addfile(tarinfo)
            # new_tar.addfile(info, io.BytesIO(data))
        pass

class InstallLogger:
    def __init__(self, install_type: str):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        logging_file = os.path.expanduser(f'~/{self.distribution.metadata.name}-{install_type}.log')
        # configure the handler and formatter for logger2
        handler2 = logging.FileHandler(logging_file, mode='w')
        formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

        # add formatter to the handler
        handler2.setFormatter(formatter2)
        # add handler to the logger
        self.logger.addHandler(handler2)
        self.logger.debug(f"{logging_file=}")

    def deep_log(self):
        # self.logger.debug(f"{self.install_lib=}")
        # self.logger.debug(f"{self.install_base=}")
        # self.logger.debug(f"{self.install_data=}")
        # self.logger.debug(f"{self.install_libbase=}")
        # self.logger.debug(f"{self.install_purelib=}")
        # self.logger.debug(f"{self.install_purelib=}")
        package = self.distribution.metadata.name
        version = self.distribution.metadata.version
        package_name = f"{package}-{version}"
        for p in dir(self):
            if ("install" in p) or (package_name in str(getattr(self, p))):
                self.logger.debug(f"self.{p}={getattr(self, p)}")
        if hasattr(self, "config_vars"):
            for p, v in self.config_vars.items():
                if ("install" in p) or (package_name in str(v)):
                    self.logger.debug(f"self.config_vars.{p}={v}")


class PostInstallLib(install_lib, InstallLogger):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        InstallLogger.__init__(self, "install_lib")

    def run(self) -> None:
        install_lib.run(self)
        self.deep_log()
        print("Post install lib")


class PostInstallEggInfo(install_egg_info, InstallLogger):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        InstallLogger.__init__(self, "install_egg_info")

    def run(self) -> None:
        install_egg_info.run(self)
        self.deep_log()
        print("post install egg info!")


class PostInstall(install, InstallLogger):
    """Executes custom post_install function after standard install"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        InstallLogger.__init__(self, "install")

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

        lib_base = self.install_lib
        package = self.distribution.metadata.name
        version = self.distribution.metadata.version
        python_version = self.config_vars.get('py_version_short')
        self.deep_log()

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
