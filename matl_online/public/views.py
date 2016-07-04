import json
import requests
import uuid

from flask import (Blueprint,
                   abort,
                   current_app,
                   render_template,
                   request,
                   jsonify,
                   send_file,
                   session)

from flask_socketio import emit, rooms

from matl_online.matl import help_file
from matl_online.public.models import Release

from matl_online.extensions import socketio, celery
from flask_wtf.csrf import validate_csrf
from matl_online.tasks import matl_task

blueprint = Blueprint('public', __name__, static_folder='../static')


@blueprint.route('/')
def home():

    session['uid'] = str(uuid.uuid4())

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


@blueprint.route('/share', methods=['POST',])
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
