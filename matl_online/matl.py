"""Module for interacting with MATL and it's source code."""

import html
import json
import os
import re
import shutil
from io import BytesIO

import requests
from flask import current_app
from scipy.io import loadmat

from matl_online.public.models import DocumentationLink, Release
from matl_online.utils import base64_encode_file, parse_iso8601, unzip

# Regular expression for pulling out content between <strong></strong> tags
STRONG_RE = re.compile(r'\<strong\>.*?\<\/strong\>')


def install_matl(version, folder):
    """Download a specific version of MATL source code."""
    repo = current_app.config['MATL_REPO']
    url = '/'.join(['https://github.com', repo, 'zipball', version])
    response = requests.get(url, stream=True)

    if response.status_code == 404:
        raise KeyError('Tag "%s" is invalid' % version)

    unzip(BytesIO(response.content), folder)


def add_doc_links(description):
    """Add hyperlinks to MATLAB's online documentation for built-ins."""
    # We want to find all bold parts
    values = re.findall(STRONG_RE, description)

    # These could be functions themselves, other MATL statements, or
    # complex function call examples:
    # mat2cell(x, ones(size(x,1),1), size(x,2),...,size(x,ndims(x)))

    def add_link(name):
        """Retrieve function documentation hyperlinks."""
        link = DocumentationLink.query.filter_by(name=name).first()

        if link:
            return '<a class="matdoc" href="%s" target="_blank">%s</a>' % \
                (link.link, name)

        return name

    for value in values:
        # Don't worry about anything that's enclosed in single-quotes '' as
        # these are typically flags that are passed to a given function or
        # pre-defined literal strings
        if not (value.startswith("<strong>'") or value.endswith("'</strong>")):

            # Replace all valid function names with links
            tmp = re.sub('[A-Za-z0-9]+', lambda x: add_link(x.group()), value)

            # Replace the original string with the link version
            description = description.replace(value, tmp)

    return description


def help_file(version):
    """Grab the help data for the specified version."""
    folder = get_matl_folder(version)
    outfile = os.path.join(folder, 'help.json')

    if os.path.isfile(outfile):
        return outfile

    matfile = os.path.join(folder, 'help.mat')

    info = loadmat(matfile,
                   squeeze_me=True,
                   mat_dtype=True,
                   struct_as_record=False)
    info = info['H']

    # Now create an array of dicts
    result = []

    # Sort everything by the plain source
    src = info.sourcePlain
    sortinds = [x[0] for x in sorted(enumerate(src),
                                     key=lambda x: x[1].swapcase())]

    for k in sortinds:
        if not info.inOutTogether[k] or len(info.out[k]) == 0:
            arguments = ''
        else:
            values = (info.__getattribute__('in')[k], info.out[k])
            arguments = '%s;  %s' % values

        # Put hyperlinks to the MATLAB documentation in the description
        info.descr[k] = add_doc_links(info.descr[k])

        # Replace all newlines in description
        info.descr[k] = info.descr[k].replace('\n', '')

        # Scipy loads empty char arrays as numeric arrays
        if not isinstance(info.comm[k], str):
            info.comm[k] = ''

        item = {
            'source': html.escape(info.sourcePlain[k]),
            'brief': info.comm[k],
            'description': info.descr[k],
            'arguments': arguments
        }

        result.append(item)

    output = {'data': result}

    with open(outfile, 'w') as fid:
        json.dump(output, fid)

    return outfile


def get_matl_folder(version, install=True):
    """Check if folder exists and download the source code if necessary."""
    matl_folder = os.path.join(current_app.config['MATL_FOLDER'], version)

    if not os.path.isdir(matl_folder):
        if install:
            install_matl(version, matl_folder)
        else:
            matl_folder = None

    return matl_folder


def process_image(image_path, interpolation=False):
    """Process an image result returned from MATL."""
    if os.path.isfile(image_path):
        return ({
            'type': 'image' if interpolation else 'image_nn',
            'value': 'data:image/png;' + base64_encode_file(image_path)
        })


def process_audio(audio_file):
    """Process an audio file returned from MATL."""
    if os.path.isfile(audio_file):
        return {
            'type': 'audio',
            'value': 'data:audio/wav;' + base64_encode_file(audio_file)
        }


def parse_matl_results(output):
    """Convert MATL output to a custom data structure.

    Takes all of the output and parses it out into sections to pass back
    to the client which indicates stderr/stdout/images, etc.
    """
    result = list()

    parts = re.split(r'(\[.*?\][^\n].*\n?)', output)

    for part in parts:
        if part == '':
            continue

        # Strip a single trailing newline
        part = part.rstrip('\n')

        item = {}

        if part.startswith('[IMAGE'):
            item = process_image(re.sub(r'\[IMAGE.*?\]', '', part),
                                 part.startswith('[IMAGE]'))
        elif part.startswith('[AUDIO]'):
            item = process_audio(part.replace('[AUDIO]', ''))
        elif part.startswith('[STDERR]'):
            item = {'type': 'stderr', 'value': part.replace('[STDERR]', '')}
        elif part.startswith('[STDOUT]'):
            item = {'type': 'stdout2', 'value': part.replace('[STDOUT]', '')}
        else:
            item = {'type': 'stdout', 'value': part}

        if item:
            result.append(item)

    return result


def matl(octave, flags, code='', inputs='', version='', folder='', line_handler=None):
    """Open a session with Octave and manages input/output as well as errors."""
    # Remember what directory octave is current in
    def escape(x):
        return x.replace("'", "''")

    # Change directories to the temporary folder so that all temporary
    # files are placed in here and won't interfere with other requests
    octave.eval("cd('%s');" % escape(folder))

    # Add the folder for the appropriate MATL version
    matl_folder = get_matl_folder(version)
    cmd = "addpath('%s')" % escape(matl_folder)
    octave.eval(cmd)

    code = ["'%s'" % escape(item) for item in code.split('\n')]
    code = '{' + ','.join(code) + '}'

    if len(inputs):
        inputs = ["'%s'" % escape(item) for item in inputs.split('\n')]
        cmd = "matl_runner('%s', %s, %s);\n" % (flags, code, ','.join(inputs))
    else:
        inputs = None
        cmd = "matl_runner('%s', %s);\n" % (flags, code)

    # Actually run the MATL code
    octave.eval(cmd, line_handler=line_handler)

    # Change back to the original directory
    cmd = "cd('%s')" % escape(current_app.config['PROJECT_ROOT'])
    octave.eval(cmd)


def refresh_releases():
    """Fetch new release information from Github and update local database."""
    repo = current_app.config['MATL_REPO']
    resp = requests.get('https://api.github.com/repos/%s/releases' % repo)

    for item in resp.json():
        # Skip any pre-releases since they aren't ready for prime-time
        if item['prerelease']:
            continue

        pubdate = parse_iso8601(item['published_at'])

        # Query the database for this release number
        release = Release.query.filter_by(tag=item['tag_name']).first()

        if release is None:
            # This is a new release and we don't need to do much
            Release.create(tag=item['tag_name'], date=pubdate)

        elif release.date != pubdate:
            # We have an updated release and we need to clean up
            source_dir = get_matl_folder(item['tag_name'], install=False)

            # If we had previously downloaded this code, then delete it
            if source_dir is not None:
                shutil.rmtree(source_dir)

            # Now update the database entry
            release.update(date=pubdate)
