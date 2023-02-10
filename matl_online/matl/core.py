"""Module for interacting with MATL, and it's source code."""
import html
import json
import logging
import pathlib
import re
import shutil
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import requests
from dateutil import parser as date_parser
from flask import current_app
from scipy.io import loadmat  # type: ignore
from werkzeug.utils import secure_filename

from matl_online.octave import OctaveSession, OutputCallback
from matl_online.octave import string as octave_string
from matl_online.public.models import DocumentationLink, Release
from matl_online.types import MATLTaskParameters
from matl_online.utils import base64_encode_file, unzip

# Regular expression for pulling out content between <strong></strong> tags
STRONG_RE = re.compile(r"<strong>.*?</strong>")


def install_matl(version: str, folder: pathlib.Path) -> None:
    """Download a specific version of MATL source code."""
    logging.info(f"Downloading MATL version {version}...")
    repo = current_app.config["MATL_REPO"]
    url = "/".join(["https://github.com", repo, "zipball", secure_filename(version)])
    response = requests.get(url, stream=True)

    if response.status_code == 404:
        raise KeyError('Tag "%s" is invalid' % version)

    unzip(BytesIO(response.content), folder)


def add_doc_links(description: str) -> str:
    """Add hyperlinks to MATLAB's online documentation for built-ins."""
    # We want to find all bold parts
    values = re.findall(STRONG_RE, description)

    # These could be functions themselves, other MATL statements, or
    # complex function call examples:
    # mat2cell(x, ones(size(x,1),1), size(x,2),...,size(x,ndims(x)))

    def add_link(name: str) -> str:
        """Retrieve function documentation hyperlinks."""
        link = DocumentationLink.query.filter_by(name=name).first()

        if link:
            return '<a class="matdoc" href="%s" target="_blank">%s</a>' % (
                link.link,
                name,
            )

        return name

    for value in values:
        # Don't worry about anything that's enclosed in single-quotes '' as
        # these are typically flags that are passed to a given function or
        # pre-defined literal strings
        if not (value.startswith("<strong>'") or value.endswith("'</strong>")):
            # Replace all valid function names with links
            tmp = re.sub("[A-Za-z0-9]+", lambda x: add_link(x.group()), value)

            # Replace the original string with the link version
            description = description.replace(value, tmp)

    return description


def help_file(version: str) -> pathlib.Path:
    """Grab the help data for the specified version."""
    folder = get_matl_folder(version)

    assert folder, "MATL folder does not exist"

    outfile = folder.joinpath("help.json")

    if outfile.is_file():
        return outfile

    mat_file = folder.joinpath("help.mat")

    info = loadmat(
        mat_file.as_posix(),
        squeeze_me=True,
        mat_dtype=True,
        struct_as_record=False,
    )
    info = info["H"]

    # Now create an array of dicts
    result = []

    # Sort everything by the plain source
    src: Tuple[str, str] = info.sourcePlain
    sorted_indices = [
        x[0] for x in sorted(enumerate(src), key=lambda x: x[1].swapcase())
    ]

    for k in sorted_indices:
        if not info.inOutTogether[k] or len(info.out[k]) == 0:
            arguments = ""
        else:
            values = (info.__getattribute__("in")[k], info.out[k])
            arguments = "%s;  %s" % values

        # Put hyperlinks to the MATLAB documentation in the description
        info.descr[k] = add_doc_links(info.descr[k])

        # Replace all newlines in description
        info.descr[k] = info.descr[k].replace("\n", "")

        # Scipy loads empty char arrays as numeric arrays
        if not isinstance(info.comm[k], str):
            info.comm[k] = ""

        item = {
            "source": html.escape(info.sourcePlain[k]),
            "brief": info.comm[k],
            "description": info.descr[k],
            "arguments": arguments,
        }

        result.append(item)

    output = {"data": result}

    with open(outfile, "w") as fid:
        json.dump(output, fid)

    return outfile


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


def process_image(
    image_path: pathlib.Path,
    interpolation: bool = False,
) -> Optional[Dict[str, str]]:
    """Process an image result returned from MATL."""

    if not image_path.is_file():
        return None

    return {
        "type": "image" if interpolation else "image_nn",
        "value": "data:image/png;" + base64_encode_file(image_path),
    }


def process_audio(audio_file: pathlib.Path) -> Optional[Dict[str, str]]:
    """Process an audio file returned from MATL."""
    if not audio_file.is_file():
        return None

    return {
        "type": "audio",
        "value": "data:audio/wav;" + base64_encode_file(audio_file),
    }


def parse_matl_results(output: str) -> List[Dict[str, str]]:
    """Convert MATL output to a custom data structure.

    Takes all the output and parses it out into sections to pass back
    to the client which indicates stderr/stdout/images, etc.
    """
    result = list()

    parts = re.split(r"(\[.*?][^\n].*\n?)", output)

    for part in parts:
        if part == "":
            continue

        # Strip a single trailing newline
        part = part.rstrip("\n")

        if part.startswith("[IMAGE"):
            image_filename = pathlib.Path(re.sub(r"\[IMAGE.*?]", "", part))
            item = process_image(image_filename, part.startswith("[IMAGE]"))
        elif part.startswith("[AUDIO]"):
            item = process_audio(pathlib.Path(part.replace("[AUDIO]", "")))
        elif part.startswith("[STDERR]"):
            item = {"type": "stderr", "value": part.replace("[STDERR]", "")}
        elif part.startswith("[STDOUT]"):
            item = {"type": "stdout2", "value": part.replace("[STDOUT]", "")}
        else:
            item = {"type": "stdout", "value": part}

        if item:
            result.append(item)

    return result


def matl(
    octave: OctaveSession,
    matl_params: MATLTaskParameters,
    directory: pathlib.Path,
    line_handler: Optional[OutputCallback] = None,
) -> None:
    """Open a session with Octave and manages input/output as well as errors."""

    # Add the folder for the appropriate MATL version
    matl_folder = get_matl_folder(matl_params.version)

    # Ensure the matl folder exists
    assert matl_folder, "MATL folder does not exist"

    # Change directories to the temporary folder so that all temporary
    # files are placed in here and won't interfere with other requests
    with octave.current_directory(directory):
        with octave.paths(matl_folder):
            # Convert the code to a cell array element-per-line
            code = f"{{{','.join([octave_string(x) for x in matl_params.code_lines])}}}"

            octave.run(
                "matl_runner",
                octave_string(matl_params.flags),
                code,
                *[octave_string(x) for x in matl_params.input_lines],
                line_handler=line_handler,
            )


def refresh_releases() -> None:
    """Fetch new release information from GitHub and update local database."""
    repo = current_app.config["MATL_REPO"]
    resp = requests.get("https://api.github.com/repos/%s/releases" % repo)

    for item in resp.json():
        # Skip any pre-releases since they aren't ready for prime-time
        if item["prerelease"]:
            continue

        pubdate = date_parser.parse(item["published_at"])

        # Query the database for this release number
        release = Release.query.filter_by(tag=item["tag_name"]).first()

        if release is None:
            # This is a new release, and we don't need to do much
            Release.create(tag=item["tag_name"], date=pubdate)

        elif release.date != pubdate:
            # We have an updated release, and we need to clean up
            source_dir = get_matl_folder(item["tag_name"], install=False)

            # If we had previously downloaded this code, then delete it
            if source_dir is not None:
                shutil.rmtree(source_dir)

            # Now update the database entry
            release.update(date=pubdate)
