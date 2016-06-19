import oct2py
import os
import re
import requests
import StringIO
import zipfile
import tempfile
import shutil

from datetime import datetime

from flask import Flask, render_template, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from settings import ProdConfig, DevConfig

app = Flask(__name__)

CONFIG = ProdConfig if os.environ.get('MATL_ONLINE_ENV') == 'prod' else DevConfig
app.config.from_object(CONFIG)

db = SQLAlchemy(app)

oc = oct2py.Oct2Py(timeout=app.config['OCTAVE_TIMEOUT'])

# Add all of our custom and overloaded functions on the path
oc.source(os.path.join(app.config['MATL_WRAP_DIR'], '.octaverc'))
oc.addpath(app.config['MATL_WRAP_DIR'])


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

    # Create a temp folder here
    tempdir = tempfile.mkdtemp(prefix='matl_session_')

    # The file containing STDOUT will also live in this temporary folder
    outfile = os.path.join(tempdir, 'defout')

    # Remember what directory octave is current in
    startdir = oc.pwd()

    # Change directories to the temporary folder so all temporary files are
    # placed in here and won't interfere with other sessions
    oc.cd(tempdir)

    # Add the folder for the appropriate MATL version
    matl_folder = get_matl_folder(version)
    oc.addpath(matl_folder)

    oc.matl_runner(flags, code, inputs, outfile)

    # Check to see if there is any output
    with open(outfile, 'r') as fid:
        output = fid.read()

    # Split at all control sequences (for now just [IMAGE])
    parts = re.split('(\[.*?\].*?\n)', output)

    result = list()

    for part in parts:
        if part == '':
            continue

        item = dict()

        if part.startswith('[IMAGE]'):
            filename = part.replace('[IMAGE]', '').rstrip()
            # Move the image where it needs to go
            import uuid
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
    oc.cd(startdir)
    oc.rmpath(matl_folder)

    # Remove the temporary directory
    shutil.rmtree(tempdir)

    return jsonify(result), 200


def parse_iso8601(date):
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")


def populate_releases():
    resp = requests.get(app.config['GITHUB_API'] + '/repos/' + app.config['MATL_REPO'] + '/releases')
    for item in resp.json():

        # Ignore any pre-releases
        if item['prerelease']:
            continue

        # Query for this version
        release = Release.query.filter(Release.tag==item['tag_name']).first()

        if release is None:
            Release.create(tag=item['tag_name'], date=parse_iso8601(item['published_at']))


@app.route('/')
def home():
    code = request.values.get('code', '')
    inputs = request.values.get('inputs', '')

    # Get the list of versions to show in the list
    versions = Release.query.order_by(Release.date.desc()).all()
    version = request.values.get('version', '')

    version = Release.query.filter(Release.tag == version).first()

    # Default to the latest version
    if version is None:
        version = versions[0]

    return render_template('index.html', code=code,
                           inputs=inputs,
                           version=version,
                           versions=versions)


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

from models import Release
