"""Miscellaneous utility functions for the application."""

import base64
import os
import zipfile
from datetime import datetime

ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def base64_encode_file(filename):
    """Load a file and return the base64-encoded version of the contents."""
    with open(filename, "rb") as fid:
        return "base64," + base64.b64encode(fid.read()).decode()


def parse_iso8601(date):
    """Convert a date in ISO 8601 format (used by GitHub) to a datetime object."""
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


def unzip(file_handle, destination, flatten=True):
    """Unzip an archive to a specific directory and flatten the shared prefix."""
    archive = zipfile.ZipFile(file_handle)

    # Ensure that the destination exists
    if not os.path.isdir(destination):
        os.makedirs(destination)

    inputs = ()

    if flatten:
        inputs = (get_members(archive),)

    archive.extractall(destination, *inputs)
