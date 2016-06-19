import os
import oct2py

from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from settings import ProdConfig, DevConfig

app = Flask(__name__)

CONFIG = ProdConfig if os.environ.get('MATL_ONLINE_ENV') == 'prod' else DevConfig
app.config.from_object(CONFIG)

db = SQLAlchemy(app)

octave = oct2py.Oct2Py()
octave.source(os.path.join(app.config['MATL_WRAP_DIR'], '.octaverc'))
octave.addpath(app.config['MATL_WRAP_DIR'])


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


@app.route('/explain', methods=['POST', 'GET'])
def explain():
    code = request.values.get('code', '')
    result = matl('-eo', code, version=request.values.get('version', ''))
    return jsonify(result), 200


@app.route('/help/<version>', methods=['GET'])
def help(version):

    # Get the help data
    return send_file(help_file(version))


@app.route('/run', methods=['POST'])
def run():
    inputs = request.values.get('inputs', '')
    code = request.values.get('code', '')
    version = request.values.get('version', '')

    result = matl('-ro', code, inputs, version=version)
    return jsonify(result), 200

from models import Release
from matl import matl, help_file
