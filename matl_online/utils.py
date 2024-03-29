"""Miscellaneous utility functions for the application."""

import base64
import os
import pathlib
import string
import zipfile
from typing import BinaryIO, Generator

from matl_online.errors import InvalidVersion
from matl_online.public.models import Release

COMMIT_HASH_LENGTH = 8


def base64_encode_file(filename: pathlib.Path) -> str:
    """Load a file and return the base64-encoded version of the contents."""
    with open(filename, "rb") as fid:
        return "base64," + base64.b64encode(fid.read()).decode()


def get_members(zip_file: zipfile.ZipFile) -> Generator[zipfile.ZipInfo, None, None]:
    """Remove leading directory from all contents of the zip file."""
    prefix = os.path.commonprefix(zip_file.namelist())

    offset = len(prefix)

    for zip_info in zip_file.infolist():
        name = zip_info.filename
        if len(name) > offset:
            zip_info.filename = name[offset:]
            yield zip_info


def unzip(
    file_handle: BinaryIO, destination: pathlib.Path, flatten: bool = True
) -> None:
    """Unzip an archive to a specific directory and flatten the shared prefix."""
    archive = zipfile.ZipFile(file_handle)

    # Ensure that the destination exists
    if not destination.is_dir():
        destination.mkdir()

    if flatten:
        archive.extractall(destination, get_members(archive))
    else:
        archive.extractall(destination)


def is_hexadecimal_string(value: str) -> bool:
    """Check whether the provide string is a valid hexadecimal string or not."""
    return all(character in string.hexdigits for character in value)


def sanitize_version(version: str) -> str:
    """Sanitizes the version provided by the user to ensure it is valid and not malicious."""

    # If the version is a commit hash, then pass the first 8 characters through
    if is_hexadecimal_string(version):
        if len(version) < COMMIT_HASH_LENGTH:
            raise InvalidVersion

        return (version[:COMMIT_HASH_LENGTH]).lower()

    # Assume this is a version tag and compare against the known releases of MATL
    if Release.exists(version):
        return version

    raise InvalidVersion
