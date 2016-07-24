"""Module for interacting with MATL and it's source code."""

import base64
import json
import os
import re
import requests
import shutil
import StringIO

from flask import current_app
from scipy.io import loadmat

from matl_online.public.models import Release
from matl_online.utils import unzip, parse_iso8601


def install_matl(version, folder):
    """Download a specific version of MATL source code."""
    url = '%s/repos/%s/releases/tags/%s'
    url = url % (current_app.config['GITHUB_API'],
                 current_app.config['MATL_REPO'], version)

    resp = requests.get(url)

    if resp.status_code == 404:
        raise KeyError('Tag "%s" is invalid' % version)

    zipball = resp.json()['zipball_url']

    response = requests.get(zipball, stream=True)
    unzip(StringIO.StringIO(response.content), folder)


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
            arguments = '%s;  %s' % \
                (info.__getattribute__('in')[k], info.out[k])

        # Replace all newlines in description
        info.descr[k] = info.descr[k].replace('\n', '')

        # Scipy loads empty char arrays as numeric arrays
        if not isinstance(info.comm[k], basestring):
            info.comm[k] = ''

        item = {'source': info.source[k],
                'brief': info.comm[k],
                'description': info.descr[k],
                'arguments': arguments}

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


def parse_matl_results(output):
    """Convert MATL output to a custom data structure.

    Takes all of the output and parses it out into sections to pass back
    to the client which indicates stderr/stdout/images, etc.
    """
    result = list()

    parts = re.split('(\[.*?\][^\n].*)', output)

    for part in parts:
        if part == '':
            continue

        item = dict()

        if part.startswith('[IMAGE]'):
            imname = part.replace('[IMAGE]', '')

            if not os.path.isfile(imname):
                continue

            # Base64-encode the image.
            with open(imname, 'rb') as image_file:
                encoded = base64.b64encode(image_file.read())
                srcstr = 'data:image/png;base64,' + encoded

            item['type'] = 'image'
            item['value'] = srcstr
        elif part.startswith('[STDERR]'):
            msg = part.replace('[STDERR]', '')
            item['type'] = 'stderr'
            item['value'] = msg
        elif part.startswith('[STDOUT]'):
            item['type'] = 'stdout2'
            msg = part.replace('[STDOUT]', '')
            item['value'] = msg
        else:
            item['type'] = 'stdout'
            item['value'] = part

        if len(item.keys()):
            result.append(item)

    return result


def matl(octave, flags, code='', inputs='', version='', folder=''):
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
        cmd = "matl_runner('%s', %s, %s);" % (flags, code, ','.join(inputs))
    else:
        inputs = None
        cmd = "matl_runner('%s', %s);" % (flags, code)

    # Actually run the MATL code
    octave.eval(cmd)

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
