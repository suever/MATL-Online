import hmac
import json
from hashlib import sha1
from flask import url_for


class TestReleaseHook:
    def test_ping(self, app, testapp, mocker):
        # Send a valid ping event and check the response

        # Get a valid header
        headers = self.get_signature(app, '')
        url = url_for('public.github_hook')

        # Specify that this is a ping event
        headers.update({'X-Github-Event': 'ping'})

        # Post empty data to the endpoint
        resp = testapp.post(url, {}, headers)

        # Succeeds and we get a pong back
        assert resp.status_code == 200
        assert resp.json.get('msg', '') == 'pong'

    def test_no_signature(self, testapp):
        # No signature header at all - Should return a 403
        url = url_for('public.github_hook')
        resp = testapp.post(url, expect_errors=True)
        assert resp.status_code == 403

    def test_invalid_signature_type(self, testapp):
        # Invalid type of signature (not sha1)
        signatures = ['fake_signature', 'fake=signature']
        url = url_for('public.github_hook')

        for signature in signatures:
            headers = {'X-Hub-Signature': signature}

            resp = testapp.post(url, {}, headers, expect_errors=True)

            # Should return a 501 error in this case
            assert resp.status_code == 501

    def test_invalid_signature(self, testapp):
        # sha1 signature that doesn't use the right secret
        url = url_for('public.github_hook')
        headers = {'X-Hub-Signature': 'sha1=fake'}

        resp = testapp.post(url, {}, headers, expect_errors=True)

        # Should return a 403
        assert resp.status_code == 403

    def test_release_event(self, app, testapp, mocker):
        # Create a valid release github event
        url = url_for('public.github_hook')

        # Data must contain at least the release number
        data = {'release': '1.2.3'}

        # Create the valid headers
        headers = self.get_signature(app, json.dumps(data))
        headers.update({'X-GitHub-Event': 'release'})

        # Mock the refresh_releases method
        refresh = mocker.patch('matl_online.public.views.refresh_releases')

        # Post the data
        resp = testapp.post_json(url, data, headers=headers)

        # Ensure it was successful and returns the expected payload
        assert resp.status_code == 200
        assert resp.json.get('success')

        # Make sure that we would have called the refresh_releases method
        refresh.assert_called_once()

    def test_non_release_event(self, app, testapp, mocker):
        # Create a valid POST that isn't a release event
        url = url_for('public.github_hook')
        data = {'not_a_release': 'true'}

        # Get the valid headers
        headers = self.get_signature(app, json.dumps(data))
        headers.update({'X-GitHub-Event': 'not-release'})

        # Mock refresh_releases method
        refresh = mocker.patch('matl_online.public.views.refresh_releases')

        # Do the post
        resp = testapp.post_json(url, data, headers=headers)

        # Ensure it was successful with an empty response
        assert resp.status_code == 200
        assert resp.text == ''

        # Make sure that we never refresh the releases for these events
        assert not refresh.called

    def get_signature(self, app, data):
        # Using the secret and payload create a signature header
        secret = app.config['GITHUB_HOOK_SECRET']
        sign = hmac.new(str(secret), msg=data, digestmod=sha1).hexdigest()
        return {'X-Hub-Signature': 'sha1=' + sign}
