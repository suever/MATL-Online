from flask import Blueprint, render_template, request, jsonify, send_file

from matl_online.matl import help_file, matl
from matl_online.public.models import Release

blueprint = Blueprint('public', __name__, static_folder='../static')


@blueprint.route('/')
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


@blueprint.route('/explain', methods=['POST', 'GET'])
def explain():
    code = request.values.get('code', '')
    result = matl('-eo', code, version=request.values.get('version', ''))
    return jsonify(result), 200


@blueprint.route('/help/<version>', methods=['GET'])
def help(version):

    # Get the help data
    return send_file(help_file(version))


@blueprint.route('/run', methods=['POST'])
def run():
    inputs = request.values.get('inputs', '')
    code = request.values.get('code', '')
    version = request.values.get('version', '')

    result = matl('-ro', code, inputs, version=version)
    return jsonify(result), 200
