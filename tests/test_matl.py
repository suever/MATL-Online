import base64
import json
import os
import pytest
import shutil

from datetime import datetime

from matl_online import matl
from matl_online.utils import parse_iso8601, ISO8601_FORMAT
from matl_online.public.models import Release

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestSourceCache:
    def test_no_source_no_install(self, app, tmpdir):
        # The source folder does not exist and we won't create it
        app.config['MATL_FOLDER'] = tmpdir.strpath
        folder = matl.get_matl_folder('18.3.0', install=False)

        # In this case, the result should simply be None
        assert folder is None

    def test_no_source_install(self, app, tmpdir, mocker):
        # The source folder does not exist but we'll fetch the source

        mock_install = mocker.patch('matl_online.matl.install_matl')
        app.config['MATL_FOLDER'] = tmpdir.strpath

        version = '0.0.0'

        folder = matl.get_matl_folder(version)
        expected = os.path.join(tmpdir.strpath, version)

        mock_install.assert_called_once_with(version, expected)
        assert folder == expected

    def test_source_folder_exists(self, app, tmpdir):
        # Source folder exists so simply return it
        app.config['MATL_FOLDER'] = tmpdir.strpath

        # Create the source folder
        version = '13.4.0'
        versiondir = tmpdir.mkdir(version)
        folder = matl.get_matl_folder(version, install=False)

        # Make sure that we only return the source folder
        assert folder == versiondir.strpath


class TestResults:

    def test_error_parsing(self):

        msg = 'single error'
        result = matl.parse_matl_results('[STDERR]' + msg)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stderr'
        assert result[0]['value'] == msg

    def test_invalid_image_parsing(self):
        # Test with a bad filename and ensure no result
        filename = '/ignore/this/filename.png'
        result = matl.parse_matl_results('[IMAGE]' + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_image_parsing(self, tmpdir):
        fileobj = tmpdir.join('image.png')
        contents = 'hello'
        fileobj.write(contents)

        # Parse the string
        result = matl.parse_matl_results('[IMAGE]' + fileobj.strpath)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'image'

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents)
        assert result[0]['value'] == 'data:image/png;base64,' + encoded

        # Make sure the file was not removed
        assert os.path.isfile(fileobj.strpath)

    def test_stdout2_parsing(self):
        # This may be of use in the future...not sure
        expected = 'ouptut2'
        result = matl.parse_matl_results('[STDOUT]' + expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout2'
        assert result[0]['value'] == expected

    def test_stdout_single_line_parsing(self):

        # Single line
        expected = 'standard output'
        result = matl.parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout'
        assert result[0]['value'] == expected

    def test_stdout_multi_line_parsing(self):
        # Multi-line
        expected = 'standard\noutput'
        result = matl.parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout'
        assert result[0]['value'] == expected


class TestHelpParsing:

    def test_generate_help_json(self, tmpdir, mocker):

        folder = mocker.patch('matl_online.matl.get_matl_folder')
        folder.return_value = tmpdir.strpath

        # Copy the test file into place
        shutil.copy(os.path.join(TEST_DATA_DIR, 'help.mat'),
                    os.path.join(tmpdir.strpath, 'help.mat'))

        outfile = matl.help_file('1.2.3')

        assert outfile == os.path.join(folder.return_value, 'help.json')

        # Now actually check the file
        with open(outfile, 'r') as fid:
            data = json.load(fid)

        assert 'data' in data
        assert len(data['data']) == 2

        # Make sure it has all the necessary keys
        expected = ['source', 'description', 'brief', 'arguments']
        expected.sort()

        actual = data['data'][0].keys()
        actual.sort()

        assert actual == expected

        item = data['data'][0]

        # make sure all newlines were removed from description
        assert item.get('description').find('\n') == -1
        assert item.get('arguments') == ''
        assert item.get('source') == '<strong>&</strong>'
        assert item.get('brief') == 'alternative input/output specification'

        item = data['data'][1]

        assert item.get('description').find('\n') == -1
        assert item.get('arguments') == '1--2 (1 / 2);  1'
        assert item.get('source') == '<strong>a</strong>'
        assert item.get('brief') == 'any'

    def test_help_json_exists(self, tmpdir, mocker):
        folder = mocker.patch('matl_online.matl.get_matl_folder')
        folder.return_value = tmpdir.strpath

        jsonfile = tmpdir.join('help.json')
        contents = 'placeholder'
        jsonfile.write(contents)

        outfile = matl.help_file('1.2.3')

        assert outfile == jsonfile.strpath

        # Make sure the file wasn't updated
        with open(outfile, 'r') as fid:
            assert fid.read() == contents


class TestInstall:

    def test_valid_version(self, tmpdir, mocker, app):
        get = mocker.patch('matl_online.matl.requests.get')
        get.return_value.status_code = 200
        get.return_value.json = lambda: {'zipball_url': 'zipball'}
        content = 'zipball_content'
        get.return_value.content = content

        zipper = mocker.patch('matl_online.matl.unzip')

        matl.install_matl('1.2.3', tmpdir.strpath)

        assert zipper.called
        assert zipper.call_args[0][0].read() == content
        assert zipper.call_args[0][1] == tmpdir.strpath

    def test_invalid_version(self, tmpdir, mocker, app):
        get = mocker.patch('matl_online.matl.requests.get')
        get.return_value.status_code = 404

        with pytest.raises(KeyError):
            matl.install_matl('3.4.5', tmpdir.strpath)


class TestReleaseRefresh:

    def test_all_new(self, mocker, app, db):
        get = mocker.patch('matl_online.matl.requests.get')

        with open(os.path.join(TEST_DATA_DIR, 'releases.json')) as fid:
            data = json.load(fid)
            get.return_value.json = lambda: data

        matl.refresh_releases()

        # Now query all releases
        releases = Release.query.all()

        assert len(releases) == len(data)

        for k, release in enumerate(releases):
            assert release.tag == data[k]['tag_name']

    def test_prerelease(self, mocker, app, db):
        # Change one of the releases to a pre release and hope it's ignored
        get = mocker.patch('matl_online.matl.requests.get')

        with open(os.path.join(TEST_DATA_DIR, 'releases.json')) as fid:
            data = json.load(fid)
            data[-1]['prerelease'] = True
            get.return_value.json = lambda: data

        matl.refresh_releases()

        # Query all releases
        releases = Release.query.all()

        assert len(releases) == len(data) - 1

        for k, release in enumerate(releases):
            assert release.tag == data[k]['tag_name']

    def test_updated_release(self, mocker, app, db):
        get = mocker.patch('matl_online.matl.requests.get')

        with open(os.path.join(TEST_DATA_DIR, 'releases.json')) as fid:
            data = json.load(fid)

            # Make a release with the first one listed here but set the
            # date to be wrong

            tag_of_interest = data[0]['tag_name']

            Release.create(date=parse_iso8601(data[0]['published_at']),
                           tag=tag_of_interest)

            # Now make the pub date something else
            newdate = datetime(2000, 1, 1)
            data[0]['published_at'] = newdate.strftime(ISO8601_FORMAT)

            get.return_value.json = lambda: data

        assert Release.query.count() == 1

        matl.refresh_releases()

        releases = Release.query.all()

        assert len(releases) == len(data)

        # Now check to make sure that the release has the updated date
        updated = Release.query.filter(Release.tag == tag_of_interest).one()

        assert updated.date == newdate

    def test_updated_release_with_source(self, mocker, app, db, tmpdir):

        matl_folder = mocker.patch('matl_online.matl.get_matl_folder')
        matl_folder.return_value = tmpdir.strpath

        assert os.path.isdir(tmpdir.strpath)

        self.test_updated_release(mocker, app, db)

        assert not os.path.isdir(tmpdir.strpath)


class TestMATLInterface:

    def test_empty_inputs(self, mocker, app, moctave):
        get_matl_folder = mocker.patch('matl_online.matl.get_matl_folder')
        foldername = 'folder'
        get_matl_folder.return_value = foldername

        matl.matl(moctave, '-ro')

        # Make sure we only had eval calls (faster)
        assert len(moctave.method_calls) == 0

        # Make sure we move to the temp directory at the beginning
        assert moctave.evals[0].startswith('cd(')

        # Ensure the MATL code gets added to the path
        assert moctave.evals[1] == "addpath('%s')" % foldername

        # Make sure we cleanup at the end
        assert moctave.evals[-1].startswith('cd(')

    def test_string_escape(self, mocker, app, moctave):
        get_matl_folder = mocker.patch('matl_online.matl.get_matl_folder')
        get_matl_folder.return_value = ''

        matl.matl(moctave, '-ro', code="'abc'")

        # Find the call to matl_runner
        call = [x for x in moctave.evals if x.startswith('matl_runner')]

        assert len(call) == 1
        assert call[0] == "matl_runner('-ro', {'''abc'''}, '');"
