# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from xml.etree import cElementTree as ET

from .utils import create_unique_id, create_software_id

import os

from operator import itemgetter


ROLE = 'tagCreator'
VERSION_SCHEME = 'alphanumeric'
XMLNS = 'http://standards.iso.org/iso/19770/-2/2015/schema.xsd'
XML_DECLARATION = '<?xml version="1.0" encoding="utf-8"?>'
N8060 = 'http://csrc.nist.gov/schema/swid/2015-extensions/swid-2015-extensions-1.0.xsd'


class Location:
    def __init__(self, path):
        self.path = path
        self.subdirectories = set()

    def addsubdirectory(self, directory):
        self.subdirectories.add(directory)


def _create_payload_tag(package_info):
    payload = ET.Element('Payload')

    all_locations = set()
    all_locations_head_and_tail = list()
    directory_and_subdirs = list()

    for file_info in package_info.files:
        all_locations.add(file_info.location)
        head, tail = os.path.split(file_info.location.strip())

        all_locations_head_and_tail.append({
            "head": head,
            "tail": tail
        })

    all_locations_sorted = sorted(all_locations_head_and_tail, key=lambda dictionary: len(dictionary['head']))

    for directory in all_locations_sorted:
        directorytag = ET.SubElement(payload, 'Directory')
        directorytag.set('root', directory['head'])
        directorytag.set('name', directory['tail'])

    """
    for test in all_locations_with_subdirectories:
        print(test.path)
        print(test.subdirectories)

    for location in all_locations:
        directorytag = ET.SubElement(payload, 'Directory')
        directorytag.set('root', location)

        for file_in_package in package_info.files:
            if file_in_package.location == location:
                filetag = ET.SubElement(directorytag, 'File')
                filetag.set('name', file_in_package.name)

                if file_in_package.mutable:
                    filetag.set('mutable', "true")
    """
    return payload


def all_matcher(ctx):
    return True


def package_name_matcher(ctx, value):
    return ctx['package_info'].package == value


def software_id_matcher(ctx, value):
    env = ctx['environment']
    os_string = env.get_os_string()
    architecture = env.get_architecture()
    unique_id = create_unique_id(ctx['package_info'], os_string, architecture)
    software_id = create_software_id(ctx['regid'], unique_id)
    return software_id == value


def create_swid_tags(environment, entity_name, regid, full=False, matcher=all_matcher):
    """
    Return SWID tags as utf8-encoded xml bytestrings for all available
    packages.

    Args:
        environment (swid_generator.environment.CommonEnvironment):
            The package management environment.
        entity_name (str):
            The SWID tag entity name.
        regid (str):
            The SWID tag regid.
        full (bool):
            Whether to include file payload. Default is False.
        matcher (function):
            A function that defines whether to return a tag or not. Default is
            a function that returns ``True`` for all tags.

    Returns:
        A generator object for all available SWID XML strings. The XML strings
        are all bytestrings, using UTF-8 encoding.

    """
    os_string = environment.get_os_string()
    pkg_info = environment.get_package_list()
    architecture = environment.get_architecture()

    for pi in pkg_info:

        ctx = {
            'regid': regid,
            'environment': environment,
            'package_info': pi
        }

        # Check if the software-id of the current package matches the targeted request
        if not matcher(ctx):
            continue

        # Header SoftwareIdentity
        software_identity = ET.Element('SoftwareIdentity')
        software_identity.set('xmlns', XMLNS)
        software_identity.set('n8060', N8060)
        software_identity.set('name', pi.package)
        software_identity.set('uniqueId', create_unique_id(pi, os_string, architecture))
        software_identity.set('version', pi.version)
        software_identity.set('versionScheme', VERSION_SCHEME)

        # SubElement Entity
        entity = ET.SubElement(software_identity, 'Entity')
        entity.set('name', entity_name)
        entity.set('regid', regid)
        entity.set('role', ROLE)

        if full:
            pi.files.extend(environment.get_files_for_package(pi.package))
            payload_tag = _create_payload_tag(pi)
            software_identity.append(payload_tag)

        swidtag_flat = ET.tostring(software_identity, encoding='utf-8').replace(b'\n', b'')
        yield XML_DECLARATION.encode('utf-8') + swidtag_flat
