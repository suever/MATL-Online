"""Unit tests for checking GitHub Release web hook."""

import hmac
import json
from hashlib import sha1

from flask import url_for


def get_signature(app, data):
    """Create a signature header from the secret and payload."""
    secret = str.encode(app.config["GITHUB_HOOK_SECRET"] or "")
    sign = hmac.new(secret, msg=data.encode(), digestmod=sha1).hexdigest()
    return {"X-Hub-Signature": "sha1=" + sign}


class TestReleaseHook:
    """Tests for interacting with the /hook route."""

    def test_ping(self, app, testapp):
        """Send a valid ping event and check the response."""
        # Get a valid header
        headers = get_signature(app, "")
        url = url_for("public.github_hook")

        # Specify that this is a ping event
        headers.update({"X-Github-Event": "ping"})

        # Post empty data to the endpoint
        resp = testapp.post(url, {}, headers)

        # Succeeds and we get a pong back
        assert resp.status_code == 200
        assert resp.json.get("msg", "") == "pong"

    def test_no_signature(self, testapp):
        """No signature header at all - Should return a 403."""
        url = url_for("public.github_hook")
        resp = testapp.post(url, expect_errors=True)
        assert resp.status_code == 403

    def test_invalid_signature_type(self, testapp):
        """Invalid type of signature (not sha1)."""
        signatures = ["fake_signature", "fake=signature"]
        url = url_for("public.github_hook")

        for signature in signatures:
            headers = {"X-Hub-Signature": signature}

            resp = testapp.post(url, {}, headers, expect_errors=True)

            # Should return a 501 error in this case
            assert resp.status_code == 501

    def test_invalid_signature(self, testapp):
        """sha1 signature that doesn't use the right secret."""
        url = url_for("public.github_hook")
        headers = {"X-Hub-Signature": "sha1=fake"}

        resp = testapp.post(url, {}, headers, expect_errors=True)

        # Should return a 403
        assert resp.status_code == 403

    def test_release_event(self, app, testapp, mocker):
        """Create a valid release GitHub event."""
        url = url_for("public.github_hook")

        # Data must contain at least the release number
        data = {"release": "1.2.3"}

        # Create the valid headers
        headers = get_signature(app, json.dumps(data))
        headers.update({"X-GitHub-Event": "release"})

        # Mock the refresh_releases method
        refresh = mocker.patch("matl_online.public.views.refresh_releases")

        # Post the data
        resp = testapp.post_json(url, data, headers=headers)

        # Ensure it was successful and returns the expected payload
        assert resp.status_code == 200
        assert resp.json.get("success")

        # Make sure that we would have called the refresh_releases method
        assert refresh.call_count == 1

    def test_non_release_event(self, app, testapp, mocker):
        """Create a valid POST that isn't a release event."""
        url = url_for("public.github_hook")
        data = {"not_a_release": "true"}

        # Get the valid headers
        headers = get_signature(app, json.dumps(data))
        headers.update({"X-GitHub-Event": "not-release"})

        # Mock refresh_releases method
        refresh = mocker.patch("matl_online.public.views.refresh_releases")

        # Do the post
        resp = testapp.post_json(url, data, headers=headers)

        # Ensure it was successful with an empty response
        assert resp.status_code == 200
        assert resp.text == ""

        # Make sure that we never refresh the releases for these events
        refresh.assert_not_called()
