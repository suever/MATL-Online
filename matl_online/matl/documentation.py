import json
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, parse_obj_as, root_validator, validator
from scipy.io import loadmat  # type: ignore[import]

from matl_online.matl.source import get_matl_folder
from matl_online.public.models import DocumentationLink

# Regular expression for pulling out content between <strong></strong> tags
STRONG_RE = re.compile(r"<strong>.*?</strong>")


class FunctionDocumentation(BaseModel):
    source: str = Field(alias="sourcePlain")
    brief: str = Field(alias="comm")
    description: str = Field(alias="descr")

    arguments: Optional[str] = None

    @validator(
        "source",
        "brief",
        "description",
        pre=True,
    )
    def remove_newlines(cls, value: str) -> str:
        return value.replace("\n", "")

    # Workaround for https://github.com/pydantic/pydantic/issues/935
    @root_validator(pre=True)
    def set_arguments(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values["inOutTogether"] == 0 or len(values["out"]) == 0:
            arguments = ""
        else:
            arguments = f"{values['in']}; {values['out']}"

        values["arguments"] = arguments
        return values


def struct_of_arrays_to_array_of_dicts(value: Any) -> List[Dict[str, Any]]:
    """Converts a numpy struct or arrays to an array of dictionaries."""
    names: Tuple[str] = value.dtype.names

    values_lists = [value[name].item() for name in names]

    return [dict(zip(names, values)) for values in zip(*values_lists)]


def documentation_from_file(mat_file: pathlib.Path) -> List[FunctionDocumentation]:
    file_contents = loadmat(mat_file.as_posix(), squeeze_me=True, variable_names="H")
    functions = struct_of_arrays_to_array_of_dicts(file_contents["H"])

    return parse_obj_as(List[FunctionDocumentation], functions)


def generate_documentation_json(
    help_filename: pathlib.Path,
    json_filename: pathlib.Path,
) -> pathlib.Path:
    print(f"Generating new documentation at {json_filename.as_posix()}")
    docs = documentation_from_file(help_filename)

    # TODO: Add documentation links

    contents = {"data": [doc.dict() for doc in docs]}

    with open(json_filename, "w") as fid:
        json.dump(contents, fid)

    return json_filename


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

    help_json = folder.joinpath("help.json")

    # If the file already exists, simply return it
    if help_json.is_file():
        return help_json

    # Otherwise we need to generate it from the help.mat file
    return generate_documentation_json(folder.joinpath("help.mat"), help_json)
