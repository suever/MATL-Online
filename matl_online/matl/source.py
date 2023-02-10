import logging
import pathlib
from io import BytesIO
from typing import Optional

import requests
from flask import current_app
from werkzeug.utils import secure_filename

from matl_online.utils import unzip


def install_matl(version: str, folder: pathlib.Path) -> None:
    """Download a specific version of MATL source code."""
    logging.info(f"Downloading MATL version {version}...")
    repo = current_app.config["MATL_REPO"]
    url = "/".join(["https://github.com", repo, "zipball", secure_filename(version)])
    response = requests.get(url, stream=True)

    if response.status_code == 404:
        raise KeyError('Tag "%s" is invalid' % version)

    unzip(BytesIO(response.content), folder)


def get_matl_folder(version: str, install: bool = True) -> Optional[pathlib.Path]:
    """Check if folder exists and download the source code if necessary."""
    matl_folder = pathlib.Path(current_app.config["MATL_FOLDER"]).joinpath(
        secure_filename(version)
    )

    if not matl_folder.is_dir():
        if not install:
            return None

        install_matl(version, matl_folder)

    return matl_folder
