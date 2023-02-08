"""Public-facing routes of our application."""

import hmac
import json
import os
import uuid
from datetime import datetime
from hashlib import sha1
from typing import Optional

import requests
from flask import Blueprint, abort, current_app, jsonify
from flask import render_template as _render_template
from flask import request, send_file, session
from flask_socketio import emit, rooms
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError

from matl_online.errors import InvalidVersion
from matl_online.extensions import celery, csrf, socketio
from matl_online.matl import help_file, refresh_releases
from matl_online.public.models import Release
from matl_online.settings import Config
from matl_online.tasks import matl_task
from matl_online.utils import sanitize_version

blueprint = Blueprint("public", __name__, static_folder="../static")

last_modified_time = os.stat(os.path.join(Config.PROJECT_ROOT, ".git")).st_mtime
last_modified_datetime = datetime.utcfromtimestamp(last_modified_time)
last_modified_date = last_modified_datetime.strftime("%Y/%m/%d")


def render_template(*args, **kwargs):
    """Add common properties via a custom render_template function."""
    kwargs["modified"] = kwargs.get("modified", last_modified_date)
    kwargs["current_year"] = kwargs.get("current_year", last_modified_datetime.year)

    analytics_id = current_app.config["GOOGLE_ANALYTICS_UNIVERSAL_ID"]
    kwargs["google_analytics_id"] = analytics_id

    return _render_template(*args, **kwargs)


def _latest_version_tag():
    latest = Release.latest()
    if latest is None:
        return ""

    return latest.tag


def _parse_version(version: Optional[str]) -> str:
    try:
        return sanitize_version(version or "")
    except InvalidVersion:
        return _latest_version_tag()


@blueprint.route("/")
def home():
    """Serve the main page of the site."""
    code = request.values.get("code", "")
    inputs = request.values.get("inputs", "")

    # Get the list of versions to show in the list
    versions = Release.query.all()
    versions.sort(key=lambda x: x.version, reverse=True)

    version = _parse_version(request.values.get("version"))

    return render_template(
        "index.html", code=code, inputs=inputs, version=version, versions=versions
    )


@blueprint.route("/privacy/optout")
def privacy_opt():
    """Endpoint for opting out of Google Analytics."""
    key = "gaoptout"

    new = request.values.get("value", "true")

    payload = {"previous": request.cookies.get(key), "current": new}

    resp = jsonify(payload)
    resp.set_cookie(key, new)
    return resp


@blueprint.route("/privacy")
def privacy():
    """Disclaimer about Google Analytics and opt out option."""
    return render_template("privacy.html")


@csrf.exempt
@blueprint.route("/hook", methods=["POST"])
def github_hook():
    """GitHub web hook for receiving information about MATL releases."""
    # Now verify that the secret is correct
    secret = str.encode(current_app.config["GITHUB_HOOK_SECRET"] or "")

    # Extract the signature from the custom header
    signature = request.headers.get("X-Hub-Signature")
    if signature is None:
        abort(403)

    pieces = signature.split("=")
    if pieces[0] != "sha1" or len(pieces) != 2:
        abort(501)

    signature = pieces[1]

    mac = hmac.new(secret, msg=request.get_data(), digestmod=sha1)

    if str(mac.hexdigest()) != str(signature):
        abort(403)

    # Implement ping
    event = request.headers.get("X-GitHub-Event", "ping")
    if event == "ping":
        return jsonify({"msg": "pong"})

    payload = request.json

    # Ignore any non-release events
    if "release" not in payload:
        return "", 200

    # We don't actually care if this is a modification, a new release, or
    # whatever. We will simply refresh our local catalog of release
    # information regardless.
    refresh_releases()

    return jsonify({"success": True}), 200


@blueprint.route("/share", methods=["POST"])
def share():
    """Route for posting image data to IMGUR to share via a link."""
    img = request.values.get("data")

    try:
        validate_csrf(request.headers.get("X-Csrftoken"))
    except ValidationError as e:
        abort(400, str(e))

    # Add the authorization headers
    client_id = current_app.config["IMGUR_CLIENT_ID"]
    header = {"Authorization": "Client-ID %s" % client_id}

    # POST parameters for imgur API
    payload = {"image": img.split("base64,")[-1], "type": "base64"}

    response = requests.post("https://api.imgur.com/3/image", payload, headers=header)
    response_data = json.loads(response.text)

    if response_data["success"]:
        result = {
            "success": response_data["success"],
            "link": response_data["data"]["link"],
        }

        return jsonify(result), 200

    else:
        return jsonify({"success": False}), 400


@socketio.on("connect")
def connected():
    """Send an event to the client with the ID of their session."""
    session_id = rooms()[0]
    emit("connection", {"session_id": session_id})


@socketio.on("kill")
def kill_task(data):
    """Triggered when a kill message is sent to kill a task."""
    taskid = session.get("taskid", None)
    if taskid is not None:
        celery.control.revoke(taskid, terminate=True, signal="SIGTERM")

    # Send a success notification regardless just in case something went
    # wrong and the task was ALREADY killed
    emit("complete", {"success": False, "message": "User terminated the job"})

    session["taskid"] = None


@socketio.on("submit")
def submit_job(data):
    """Submit some code and inputs for interpretation."""
    # If we already have a task disable submitting
    uid = data.get("uid", str(uuid.uuid4()))

    # Process all input arguments
    inputs = data.get("inputs", "")
    code = data.get("code", "")

    version = _parse_version(data.get("version", ""))

    # No op if no inputs are provided
    if code == "":
        return

    task = matl_task.delay("-ro", code, inputs, version=version, session=uid)

    # Store the currently executing task ID in the session
    session["taskid"] = task.id


@blueprint.route("/explain", methods=["POST", "GET"])
def explain():
    """Provide the user with an explanation of some code."""
    code = request.values.get("code", "")
    version = _parse_version(request.values.get("version", ""))

    result = matl_task.delay("-eo", code, version=version).wait()
    return jsonify(result), 200


@blueprint.route("/help/<version>", methods=["GET"])
def documentation(version):
    """Return a JSON representation of the help for the requested version."""
    try:
        sanitize_version(version)
    except InvalidVersion:
        return "version not found", 404

    return send_file(help_file(version))
