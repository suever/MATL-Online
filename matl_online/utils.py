import os
import zipfile

from datetime import datetime


def parse_iso8601(date):
    """
    Convert a date in ISO 8601 format (used by github) to a datetime object
    """
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")


def get_members(zip_file):
    """
    Removes leading directory from all contents of the zip file
    """
    prefix = os.path.commonprefix(zip_file.namelist())

    offset = len(prefix)

    for zip_info in zip_file.infolist():
        name = zip_info.filename
        if len(name) > offset:
            zip_info.filename = name[offset:]
            yield zip_info


def unzip(fileobj, destination, flatten=True):
    """
    Unzip an archive to a specific directory and flatten the shared folder
    prefix of all contents.
    """
    archive = zipfile.ZipFile(fileobj)

    # Ensure that the destination exists
    if not os.path.isdir(destination):
        os.makedirs(destination)

    inputs = ()

    if flatten:
        inputs = (get_members(archive),)

    archive.extractall(destination, *inputs)
