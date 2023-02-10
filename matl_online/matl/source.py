import logging
import pathlib
import shutil
from io import BytesIO

import requests
from github import Github
from github.Repository import Repository
from werkzeug.utils import secure_filename

from matl_online.errors import MissingDirectory
from matl_online.settings import Config
from matl_online.utils import unzip


def github_repository(name: str) -> Repository:
    return Github().get_repo(name)


def remove_source_directory(ref: str, source_root: pathlib.Path) -> None:
    try:
        folder = get_matl_folder(
            ref,
            install=False,
            source_root=source_root,
        )
    except MissingDirectory:
        return

    shutil.rmtree(folder)


def install_matl(
    ref: str,
    folder: pathlib.Path,
    repository: str = Config.MATL_REPOSITORY,
) -> None:
    """Download a specific version (or commit) of the MATL source code."""
    logging.info(f"Downloading MATL ref {ref}...")

    repo = github_repository(repository)

    url = repo.get_archive_link("zipball", ref)

    response = requests.get(url, stream=True)

    if response.status_code == 404:
        raise KeyError('MATL version "%s" is invalid' % ref)

    unzip(BytesIO(response.content), folder)


def get_matl_folder(
    version: str,
    install: bool = True,
    source_root: pathlib.Path = Config.MATL_SOURCE_DIRECTORY,
) -> pathlib.Path:
    """Check if folder exists and download the source code if necessary."""
    matl_folder = source_root.joinpath(secure_filename(version))

    if not matl_folder.is_dir():
        if not install:
            raise MissingDirectory(f"MATL source folder for {version} does not exist")

        install_matl(version, matl_folder)

    return matl_folder
