import json

from flask import url_for
from .factories import ReleaseFactory

from matl_online.public.models import Release


class TestHome:
    def test_defaults(self, testapp, mocker, db):
        url = url_for('public.home')
        ReleaseFactory.create_batch(size=10)

        render = mocker.patch('matl_online.public.views.render_template')
        render.return_value = ''

        testapp.get(url)

        assert render.call_args[0][0] == 'index.html'

        params = render.call_args[1]

        assert params.get('inputs') == ''
        assert params.get('code') == ''
        assert params.get('version') == Release.latest()

        versions = params.get('versions')
        versions.sort()

        releases = Release.query.all()
        releases.sort()

        assert versions == releases

    def test_non_existent_version(self, testapp, mocker, db):
        url = url_for('public.home', version='not a version')
        ReleaseFactory.create_batch(size=10)

        render = mocker.patch('matl_online.public.views.render_template')
        render.return_value = ''

        testapp.get(url)

        version = render.call_args[1].get('version')
        assert version == Release.latest()
        assert version.tag != 'not a version'


class TestExplain:
    def test_with_version(self, testapp, mocker, db):

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
        releases = ReleaseFactory.create_batch(size=3)

        task = mocker.patch('matl_online.public.views.matl_task.delay')
        task.return_value.wait = lambda: {}

        resp = testapp.get(url_for('public.explain'))

        assert resp.status_code == 200
        assert task.call_args[1].get('version') == releases[-1].tag


def test_fetch_help(testapp, mocker, db, tmpdir):
    folder = mocker.patch('matl_online.matl.get_matl_folder')
    folder.return_value = tmpdir.strpath

    jsonfile = tmpdir.join('help.json')
    data = {'placeholder': 'value'}
    jsonfile.write(json.dumps(data))

    url = url_for('public.help', version='1.2.3')

    resp = testapp.get(url)

    assert resp.status_code == 200
    assert resp.json == data
