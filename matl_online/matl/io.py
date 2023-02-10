import pathlib
import re
from typing import Dict, List, Optional

from matl_online.utils import base64_encode_file


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
