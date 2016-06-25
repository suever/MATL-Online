import json
import os
import re
import requests
import shutil
import StringIO
import uuid

from scipy.io import loadmat

from matl_online.settings import Config
from matl_online.utils import unzip


def install_matl(version, folder):
    """
    Downloads the specified version of the MATL source code to the desired
    location.
    """

    url = 'https://api.github.com/repos/%s/releases/tags/%s'
    url = url % (Config.MATL_REPO, version)

    resp = requests.get(url)

    if resp.status_code == 404:
        raise KeyError('Tag "%s" is invalid' % version)

    zipball = resp.json()['zipball_url']

    response = requests.get(zipball, stream=True)
    unzip(StringIO.StringIO(response.content), folder)


def help_file(version):
    """
    Grab the help data for the specified version
    """

    folder = get_matl_folder(version)
    outfile = os.path.join(folder, 'help.json')

    if os.path.isfile(outfile):
        return outfile

    matfile = os.path.join(folder, 'help.mat')

    info = loadmat(matfile, squeeze_me=True, struct_as_record=False)
    info = info['H']

    # Now create an array of dicts
    result = []

    for k in range(len(info.source)):

        if not info.inOutTogether[k] or len(info.out[k]) == 0:
            arguments = ""
        else:
            arguments = "%s;  %s" % (info.__getattribute__('in')[k], info.out[k])

        item = {'source': info.source[k],
                'description': info.descr[k],
                'arguments': arguments}

        result.append(item)

    output = {'data': result}

    with open(outfile, 'w') as fid:
        json.dump(output, fid)

    return outfile


def get_matl_folder(version):
    """
    Check if folder exists and download the source code if necessary
    """

    matl_folder = os.path.join(Config.MATL_FOLDER, version)

    if not os.path.isdir(matl_folder):
        install_matl(version, matl_folder)

    return matl_folder


def parse_matl_results(output):
    """
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
            imname = part.replace('[IMAGE]', '').rstrip()
            # Move the image where it needs to go
            fname = str(uuid.uuid4()) + '.png'

            shutil.move(imname,
                        os.path.join(Config.TEMP_IMAGE_DIR, fname))

            item['type'] = 'image'
            item['value'] = 'static/temp/' + fname
        elif part.startswith('[STDERR]'):
            msg = part.replace('[STDERR]', '').rstrip()
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
    """
    Opens a session with Octave and manages input/output as well as errors
    """

    # Remember what directory octave is current in
    startdir = octave.pwd()

    # Change directories to the temporary folder so that all temporary
    # files are placed in here and won't interfere with other requests
    octave.cd(folder)

    # Add the folder for the appropriate MATL version
    matl_folder = get_matl_folder(version)
    octave.addpath(matl_folder)

    # Actually run the MATL code
    octave.matl_runner(flags, code, inputs)

    # Change back to the original directory
    octave.cd(startdir)
    octave.rmpath(matl_folder)
