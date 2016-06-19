import os
import re
import requests
import shutil
import StringIO
import tempfile
import uuid

from app import app, octave
from flask import url_for
from utils import unzip


def install_matl(version, folder):
    """
    Downloads the specified version of the MATL source code to the desired
    location.
    """

    url = 'https://api.github.com/repos/%s/releases/tags/%s'
    url = url % (app.config['MATL_REPO'], version)

    resp = requests.get(url)

    if resp.status_code == 404:
        raise KeyError('Tag "%s" is invalid' % version)

    zipball = resp.json()['zipball_url']

    response = requests.get(zipball, stream=True)
    unzip(StringIO.StringIO(response.content), folder)


def get_matl_folder(version):
    """
    Check if folder exists and download the source code if necessary
    """

    matl_folder = os.path.join(app.config['MATL_FOLDER'], version)

    if not os.path.isdir(matl_folder):
        install_matl(version, matl_folder)

    return matl_folder


def matl(flags, code='', inputs='', version=''):
    """
    Opens a session with Octave and manages input/output as well as errors
    """

    result = {}

    # Create a temporary folder
    tempdir = tempfile.mkdtemp(prefix='matl_session_')

    # The file containing STDOUT will also live in this temporary folder
    outfile = os.path.join(tempdir, 'defout')

    # Remember what directory octave is current in
    startdir = octave.pwd()

    # Change directories to the temporary folder so that all temporary
    # files are placed in here and won't interfere with other requests
    octave.cd(tempdir)

    # Add the folder for the appropriate MATL version
    matl_folder = get_matl_folder(version)
    octave.addpath(matl_folder)

    # Actually run the MATL code
    octave.matl_runner(flags, code, inputs, outfile)

    output = ''

    # Check to see if there was any output
    with open(outfile, 'r') as fid:
        output = fid.read()

    parts = re.split('(\[.*?\].*?\n)', output)

    result = list()

    for part in parts:
        if part == '':
            continue

        item = dict()

        if part.startswith('[IMAGE]'):
            filename = part.replace('[IMAGE]', '').rstrip()
            # Move the image where it needs to go
            fname = str(uuid.uuid4()) + '.png'

            shutil.move(os.path.join(tempdir, filename),
                        os.path.join(app.config['TEMP_IMAGE_DIR'], fname))

            item['type'] = 'image'
            item['value'] = url_for('static', filename='temp/' + fname)
        elif part.startswith('[STDERR]'):
            msg = part.replace('[STDERR]', '').rstrip()
            item['type'] = 'stderr'
            item['value'] = msg
        else:
            item['type'] = 'stdout'
            item['value'] = part

        result.append(item)

    # Change back to the original directory
    octave.cd(startdir)
    octave.rmpath(matl_folder)

    # Remove the temporary directory
    shutil.rmtree(tempdir)

    return result
