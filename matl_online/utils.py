"""Miscelaneous utility functions for the application."""

import base64
import itertools
import os
import zipfile

from datetime import datetime

ISO8601_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def base64_encode_file(filename):
    """Load a file and return the base64-encoded version of the contents."""
    with open(filename, 'rb') as fid:
        return b'base64,' + base64.b64encode(fid.read())


def grouper_iterator(n, items):
    """Group the input into chunks and yield each chunk"""
    args = [iter(items)] * n
    for group in itertools.izip_longest(*args):
        # This filter removes fill values
        yield [item for item in group if item is not None]


def grouper(n, items):
    """Group the input into chunks of N items."""
    args = [iter(items)] * n
    return ([e for e in t if e is not None] for t in itertools.izip_longest(*args))


def parse_iso8601(date):
    """Convert a date in ISO 8601 format (used by github) to a datetime object."""
    return datetime.strptime(date, ISO8601_FORMAT)


def get_members(zip_file):
    """Remove leading directory from all contents of the zip file."""
    prefix = os.path.commonprefix(zip_file.namelist())

    offset = len(prefix)

    for zip_info in zip_file.infolist():
        name = zip_info.filename
        if len(name) > offset:
            zip_info.filename = name[offset:]
            yield zip_info


def unzip(fileobj, destination, flatten=True):
    """Unzip an archive to a specific directory and flatten the shared prefix."""
    archive = zipfile.ZipFile(fileobj)

    # Ensure that the destination exists
    if not os.path.isdir(destination):
        os.makedirs(destination)

    inputs = ()

    if flatten:
        inputs = (get_members(archive),)

    archive.extractall(destination, *inputs)
