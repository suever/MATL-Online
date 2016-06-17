import oct2py
import os
import re
import requests
import StringIO
import zipfile
import tempfile
import shutil

from flask import Flask, render_template, request, jsonify
#from flask_socketio import SocketIO, emit

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['APPDIR'] = os.path.dirname(os.path.realpath(__file__))
app.config['MATL_FOLDER'] = os.path.join(app.config['APPDIR'], 'MATL')
app.config['MATL_REPO'] = 'lmendo/MATL'
app.config['MATL_WRAP_DIR'] = os.path.join(app.config['MATL_FOLDER'], 'wrappers')
app.config['GITHUB_API'] = 'https://api.github.com'

#socketio = SocketIO(app)

import logging
logging.basicConfig(filename='/Users/suever/MATL.log')
logger = logging.getLogger('MATL')
logger.setLevel(logging.DEBUG)

oc = oct2py.Oct2Py(logger=logger)


def get_members(zip_file):
    """
    Removes leading directory from all contents of the zip file
    """
    prefix = os.path.commonprefix(zip_file.namelist())

    offset = len(prefix)

    for zip_info in zip_file.infolist():
        name = zip_info.filename
        if len(name) > offset:
            zip_info.filename = name[offset:]
            yield zip_info


def install_matl(version, folder):

    url = app.config['GITHUB_API'] + '/repos/' + app.config['MATL_REPO'] + '/releases/tags/' + version
    resp = requests.get(url)

    if resp.status_code == 404:
        raise KeyError('Tag "%s" is invalid' % version)

    zipball = resp.json()['zipball_url']

    response = requests.get(zipball, stream=True)
    Z = zipfile.ZipFile(StringIO.StringIO(response.content))

    os.makedirs(folder)
    Z.extractall(folder, get_members(Z))


def get_matl_folder(version):
    # Check if the folder exists
    matl_folder = os.path.join(app.config['MATL_FOLDER'], version)

    if not os.path.isdir(matl_folder):
        install_matl(version, matl_folder)

    return matl_folder


def parseError(message):
    """
    Parses the error messages returned by oct2py
    """
    match = re.search('(?<=Octave returned:\n).*', message, re.DOTALL)
    if match is not None:
        message = match.group()

    return message


def matl(flags, code='', inputs='', version='18.0.1'):
    """
    Opens a session with Octave and manages input/output as well as errors
    """

    result = {}

    tempdir = tempfile.mkdtemp(prefix='matl_session_')
    outfile = os.path.join(tempdir, 'defout')

    startdir = oc.pwd()

    # Create a temp folder here
    oc.cd(tempdir)

    oc.addpath(get_matl_folder(version))

    oc.addpath(app.config['MATL_WRAP_DIR'])

    try:
        oc.matl_runner(flags, code, inputs, outfile)
    except Exception as e:
        result['error'] = parseError(e.message)

    # Check to see if there is any output
    with open(outfile, 'r') as fid:
        result['output'] = fid.read()

    oc.cd(startdir)

    shutil.rmtree(tempdir)

    return jsonify(result), 200


@app.route('/')
def home():
    code = request.values.get('code', '')
    inputs = request.values.get('inputs', '')
    version = request.values.get('version', '18.1.0')
    return render_template('index.html', code=code, inputs=inputs, version=version)


'''
@app.route('/broadcast')
def broadcast():
    socketio.emit('mybroadcast', {'message': 'HELLO WORLD'}, broadcast=True)
    return 'Success'
'''


@app.route('/explain', methods=['POST', 'GET'])
def explain():
    code = request.values.get('code', '')
    return matl('-eo', code, version=request.values.get('version', ''))


@app.route('/run', methods=['POST'])
def run():
    inputs = request.values.get('inputs', '')
    code = request.values.get('code', '')
    version = request.values.get('version', '')

    return matl('-ro', code, inputs, version=version)


#socketio.run(app)
app.run(debug=True)
