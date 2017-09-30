""""Tests for checking user interaction with views."""

import json

from flask import url_for
from .factories import ReleaseFactory

from matl_online.public.models import Release


class TestShare:
    """Tests the /share route for uploading to imgur."""

    def test_share_with_csrf(self, app, testapp, mocker):
        """Passing CSRF validation check."""
        csrf = mocker.patch('matl_online.public.views.validate_csrf')
        csrf.return_value = True

        post = mocker.patch('matl_online.public.views.requests.post')
        data = {'success': True, 'data': {'link': 'http://link'}}
        post.return_value.text = json.dumps(data)

        url = url_for('public.share', data='base64,data')

        response = testapp.post(url)

        # Make sure that CSRF token was actually checked
        assert csrf.call_count == 1
        assert post.call_count == 1

        head_expect = {'Authorization':
                       'Client-ID ' + app.config['IMGUR_CLIENT_ID']}

        post.assert_called_once_with('https://api.imgur.com/3/image',
                                     {'image': 'data', 'type': 'base64'},
                                     headers=head_expect)

        # Make sure that the response was correct
        assert response.status_code == 200

        payload = response.json

        assert payload.get('success') is True
        assert payload.get('link') == data['data']['link']

    def test_share_with_invalid_csrf(self, testapp):
        """Failing CSRF validation produces an error."""
        url = url_for('public.share', data='INVALID')
        resp = testapp.post_json(url, '', expect_errors=True)
        assert resp.status_code == 400

    def test_share_without_csrf(self, testapp):
        """Failing CSRF validation produces an error."""
        url = url_for('public.share', data='')
        resp = testapp.post_json(url, '', expect_errors=True)
        assert resp.status_code == 400

    def test_failed_upload(self, testapp, mocker):
        """Test if there was an error while uploading to imgur."""
        csrf = mocker.patch('matl_online.public.views.validate_csrf')
        csrf.return_value = True

        post = mocker.patch('matl_online.public.views.requests.post')
        post.return_value.text = json.dumps({'success': False})

        url = url_for('public.share', data='data')

        response = testapp.post(url, expect_errors=True)

        assert csrf.call_count == 1
        assert post.call_count == 1

        assert response.status_code == 400
        assert response.json.get('success') is False


class TestHome:
    """Test the main page of the site."""

    def test_defaults(self, testapp, mocker, db):
        """Check the default arguments passed to template."""
        url = url_for('public.home')
        ReleaseFactory.create_batch(size=10)

        render = mocker.patch('matl_online.public.views.render_template')
        render.return_value = ''

        testapp.get(url)

        args, params = render.call_args

        assert args[0] == 'index.html'
        assert params.get('inputs') == ''
        assert params.get('code') == ''
        assert params.get('version') == Release.latest().tag

        versions = params.get('versions')
        versions.sort()

        releases = Release.query.all()
        releases.sort()

        assert versions == releases

    def test_non_existent_version(self, testapp, mocker, db):
        """Pass an invalid version number via query string."""
        url = url_for('public.home', version='not a version')
        ReleaseFactory.create_batch(size=10)

        render = mocker.patch('matl_online.public.views.render_template')
        render.return_value = ''

        testapp.get(url)

        version = render.call_args[1].get('version')
        assert version == Release.latest().tag


class TestPrivacy:
    """Test privacy policy and associated routes."""

    def test_privacy_page(self, testapp):
        """Test the main view for errors."""
        url = url_for('public.privacy')
        resp = testapp.get(url)
        assert resp.status_code == 200

    def test_api(self, testapp):
        """Test the API for toggling the opt-in/opt-out status."""
        url = url_for('public.privacy_opt')

        opts = [('true', 'true'), ('true', 'false'),
                ('false', 'false'), ('false', 'true')]

        for previous, current in opts:
            testapp.set_cookie('gaoptout', previous)
            resp = testapp.get(url, params={'value': current})

            assert resp.status_code == 200
            assert resp.json['previous'] == previous
            assert resp.json['current'] == current
            assert testapp.cookies['gaoptout'] == current

    def test_optout(self, testapp):
        """Make sure that the cookie is respected."""
        url = url_for('public.privacy')

        # Opt-In
        testapp.set_cookie('gaoptout', 'false')
        resp = testapp.get(url)

        assert resp.status_code == 200
        assert resp.text.find('GoogleAnalyticsObject') != -1

        # Opt-Out
        testapp.set_cookie('gaoptout', 'true')
        resp = testapp.get(url)

        assert resp.status_code == 200
        assert resp.text.find('GoogleAnalyticsObject') == -1


class TestExplain:
    """Test the /explain route."""

    def test_with_version(self, testapp, mocker, db):
        """Specify a version and get a successful response."""
        ReleaseFactory(tag='1.2.3')
        ReleaseFactory(tag='2.4.5')

        version = '1.2.3'
        url = url_for('public.explain', version=version)

        data = {'data': 'this'}

        task = mocker.patch('matl_online.public.views.matl_task.delay')
        task.return_value.wait = lambda: data

        resp = testapp.get(url)

        assert resp.status_code == 200
        assert resp.json == data

    def test_no_version(self, testapp, mocker, db):
        """Do not specify a version and use the latest version."""
        releases = ReleaseFactory.create_batch(size=3)

        task = mocker.patch('matl_online.public.views.matl_task.delay')
        task.return_value.wait = lambda: {}

        resp = testapp.get(url_for('public.explain'))

        assert resp.status_code == 200
        assert task.call_args[1].get('version') == releases[-1].tag


def test_fetch_help(testapp, mocker, db, tmpdir):
    """Check that we get the expected JSON when requesting help."""
    folder = mocker.patch('matl_online.matl.get_matl_folder')
    folder.return_value = tmpdir.strpath

    jsonfile = tmpdir.join('help.json')
    data = {'placeholder': 'value'}
    jsonfile.write(json.dumps(data))

    url = url_for('public.help', version='1.2.3')

    resp = testapp.get(url)

    assert resp.status_code == 200
    assert resp.json == data
