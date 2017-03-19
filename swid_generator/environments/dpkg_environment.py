# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import subprocess
import glob

from .common import CommonEnvironment
from ..package_info import PackageInfo, FileInfo


class DpkgEnvironment(CommonEnvironment):
    """
    Environment class for distributions using dpkg as package manager (e.g.
    Ubuntu, Debian or Mint).

    The packages are retrieved from the database using the ``dpkg-query`` tool:
    http://man7.org/linux/man-pages/man1/dpkg-query.1.html

    """
    executable = 'dpkg-query'
    executable_ls = 'ls'

    installed_states = {
        'install ok installed': True,
        'deinstall ok config-files': False
    }

    @classmethod
    def get_package_list(cls):
        """
        Get list of installed packages.

        Returns:
            List of ``PackageInfo`` instances.

        """
        command_args = [cls.executable, '-W', '-f=${Package}\\n${Version}\\n${Status}\\n${conffiles}\\t']
        data = subprocess.check_output(command_args)
        result = []


        if isinstance(data, bytes):
            data = data.decode('utf-8')
        line_list = data.split('\t')

        for line in line_list:
            split_line = line.split('\n')

            if len(split_line) >= 4:
                info = PackageInfo()
                info.package = split_line[0]
                info.version = split_line[1]
                info.status = split_line[2]

                if split_line[3] != '':
                    fileinfos = []
                    for filepath in split_line[3:len(split_line)]:
                        file = FileInfo(filepath)
                        file.mutable = True
                        fileinfos.append(file)

                    info.files.extend(fileinfos)

                result.append(info)

        return [r for r in result if cls._package_installed(r)]

    @classmethod
    def get_files_for_package(cls, package_name):
        """
        Get list of files related to the specified package.

        Args:
            package_name (str):
                The package name as string (e.g. ``cowsay``).

        Returns:
            List of ``FileInfo`` instances.

        """
        command_args = [cls.executable, '-L', package_name]
        data = subprocess.check_output(command_args)
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        lines = data.rstrip().split('\n')
        files = filter(cls._is_file, lines)
        return [FileInfo(path) for path in files]

    @classmethod
    def _package_installed(cls, package_info):
        """
        Try to find out whether the specified package is installed or not.

        If the installed state cannot be determined with certainty we assume
        it's installed.

        Args:
            package_info (package_info.PackageInfo):
                The package to check.

        Returns:
            True or False

        """
        return cls.installed_states.get(package_info.status, True)
