import json
import pathlib
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, parse_obj_as, root_validator, validator
from scipy.io import loadmat  # type: ignore[import]

from matl_online.matl.source import get_matl_folder


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


def help_file(version: str) -> pathlib.Path:
    """Grab the help data for the specified version."""
    folder = get_matl_folder(version)

    help_json = folder.joinpath("help.json")

    # If the file already exists, simply return it
    if help_json.is_file():
        return help_json

    # Otherwise we need to generate it from the help.mat file
    return generate_documentation_json(folder.joinpath("help.mat"), help_json)
