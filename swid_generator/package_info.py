# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import os.path


class FileInfo(object):
    def __init__(self, path):
        self.location = os.path.split(path)[0]
        self.name = (os.path.split(path)[1]).split(' ')[0]
        self.mutable = False


class PackageInfo(object):
    def __init__(self, package='', version='', files=None, conffiles=None):
        if files is None:
            files = []
        self.package = package
        self.version = version
        self.files = files
        self.conffiles = conffiles
