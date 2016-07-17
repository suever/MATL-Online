import json
import hmac
import os
import requests
import uuid

from datetime import datetime

from flask import (Blueprint,
                   abort,
                   current_app,
                   render_template,
                   request,
                   jsonify,
                   send_file,
                   session)

from flask_socketio import emit, rooms
from flask_wtf.csrf import validate_csrf

from hashlib import sha1
from sys import hexversion

from matl_online.extensions import socketio, celery, csrf
from matl_online.matl import help_file, refresh_releases
from matl_online.public.models import Release
from matl_online.settings import Config
from matl_online.tasks import matl_task

blueprint = Blueprint('public', __name__, static_folder='../static')

modtime = os.stat(os.path.join(Config.PROJECT_ROOT, '.git')).st_mtime
last_modified = datetime.utcfromtimestamp(modtime).strftime('%Y/%m/%d')


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
                           versions=versions,
                           modified=last_modified)


@csrf.exempt
@blueprint.route('/hook', methods=['POST'])
def github_hook():

    # Now verify that the secret is correct
    secret = current_app.config['GITHUB_HOOK_SECRET']

    # Extract the signature from the custom header
    signature = request.headers.get('X-Hub-Signature')
    if signature is None:
        abort(403)

    pieces = signature.split('=')
    if pieces[0] != 'sha1' or len(pieces) != 2:
        abort(501)

    signature = pieces[1]

    mac = hmac.new(str(secret), msg=request.data, digestmod=sha1)

    if hexversion >= 0x020707F0:
        if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
            abort(403)
        else:
            if not str(mac.hexdigest()) == str(signature):
                abort(403)

    # Implement ping
    event = request.headers.get('X-GitHub-Event', 'ping')
    if event == 'ping':
        return jsonify({'msg': 'pong'})

    try:
        payload = json.loads(request.data)
    except:
        abort(400)

    # Ignore any non-release events
    if 'release' not in payload:
        return '', 200

    # We don't actually care if this is a modification, a new release, or
    # whatever. We will simply refresh our local catalog of release
    # information regardless.
    refresh_releases()

    return jsonify({'success': True}), 200


@blueprint.route('/share', methods=['POST'])
def share():
    img = request.values.get('data')

    if not validate_csrf(request.headers.get('X-Csrftoken')):
        abort(400, 'CSRF token missing or incorrect.')

    result = {'success': True,
              'link': 'https://imgur.com/opoxoisdf.png'}

    # Add the authorization headers
    clientid = current_app.config['IMGUR_CLIENT_ID']
    header = {'Authorization': 'Client-ID %s' % clientid}

    # POST parameters for imgur API
    payload = {'image': img.split('base64,')[-1],
               'type': 'base64'}

    resp = requests.post('https://api.imgur.com/3/image',
                         payload, headers=header)
    respdata = json.loads(resp.text)

    if respdata['success']:
        result = {'success': respdata['success'],
                  'link': respdata['data']['link']}

        return jsonify(result), 200

    else:
        return jsonify({'success': False}), 400


@socketio.on('connect')
def connected():
    # Go ahead and assign to their own room
    session_id = rooms()[0]
    emit('connection', {'session_id': session_id})


@socketio.on('kill')
def kill_task(data):
    taskid = session.get('taskid', None)
    if taskid is not None:
        celery.control.revoke(taskid, terminate=True)

    # Send a success notification regardless just in case something went
    # wrong and the task was ALREADY killed
    emit('complete', {
        'success': False,
        'message': 'User terminated the job'
    })

    session['taskid'] = None


@socketio.on('submit')
def submit_job(data):

    # If we already have a task disable submitting
    uid = data.get('uid', str(uuid.uuid4()))

    # Process all input arguments
    inputs = data.get('inputs', '')
    code = data.get('code', '')
    version = data.get('version', '18.3.0')

    # No op if no inputs are provided
    if code == '':
        return

    task = matl_task.delay('-ro', code, inputs,
                           version=version, session=uid)

    # Store the currently executing task ID in the session
    session['taskid'] = task.id


@blueprint.route('/explain', methods=['POST', 'GET'])
def explain():
    code = request.values.get('code', '')
    version = request.values.get('version', '18.3.0')

    result = matl_task.delay('-eo', code, version=version).wait()
    return jsonify(result), 200


@blueprint.route('/help/<version>', methods=['GET'])
def help(version):

    # Get the help data
    return send_file(help_file(version))
