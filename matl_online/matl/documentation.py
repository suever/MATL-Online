import pathlib
import re
from typing import Tuple

from scipy.io import loadmat  # type: ignore[import]

from matl_online.public.models import DocumentationLink

from .core import get_matl_folder

# Regular expression for pulling out content between <strong></strong> tags
STRONG_RE = re.compile(r"<strong>.*?</strong>")


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
