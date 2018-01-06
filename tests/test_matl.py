"""Unit tests for module for interacting with octave / MATL."""

import base64
import json
import os
import pytest
import shutil

from bs4 import BeautifulSoup
from datetime import datetime

from matl_online import matl
from matl_online.utils import parse_iso8601, ISO8601_FORMAT
from matl_online.public.models import Release
from .factories import DocumentationLinkFactory as DocLink

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestSourceCache:
    """Series of tests to check if source code is managed properly."""

    def test_no_source_no_install(self, app, tmpdir):
        """The source folder does not exist and we won't create it."""
        app.config['MATL_FOLDER'] = tmpdir.strpath
        folder = matl.get_matl_folder('18.3.0', install=False)

        # In this case, the result should simply be None
        assert folder is None

    def test_no_source_install(self, app, tmpdir, mocker):
        """The source folder does not exist but we'll fetch the source."""
        mock_install = mocker.patch('matl_online.matl.install_matl')
        app.config['MATL_FOLDER'] = tmpdir.strpath

        version = '0.0.0'

        folder = matl.get_matl_folder(version)
        expected = os.path.join(tmpdir.strpath, version)

        mock_install.assert_called_once_with(version, expected)
        assert folder == expected

    def test_source_folder_exists(self, app, tmpdir):
        """Source folder exists so simply return it."""
        app.config['MATL_FOLDER'] = tmpdir.strpath

        # Create the source folder
        version = '13.4.0'
        versiondir = tmpdir.mkdir(version)
        folder = matl.get_matl_folder(version, install=False)

        # Make sure that we only return the source folder
        assert folder == versiondir.strpath


class TestDocLinks:
    """Ensure that documentation hyperlinks are added appropriately."""

    def test_basic_doclink(self, db):
        """Use a straightforward single function name."""
        link = DocLink(name='ans')
        template = 'This is a doc string for <strong>%s</strong>'

        output = matl.add_doc_links(template % link.name)

        soup = BeautifulSoup(output, 'html.parser')

        assert soup.strong.a['href'] == link.link
        assert soup.strong.a.text == link.name

    def test_multiple_doclink(self, db):
        """Include two functions in the same docstring."""
        links = (DocLink(name='func1'), DocLink(name='func2'))
        template = 'This is a doc for <strong>%s</strong>'

        docstring = (template % links[0].name) + (template % links[1].name)

        output = matl.add_doc_links(docstring)

        soup = BeautifulSoup(output, 'html.parser')

        strongs = soup.findAll('strong')

        assert len(strongs) == len(links)

        for k, strong in enumerate(strongs):
            assert strong.a['href'] == links[k].link
            assert strong.a.text == links[k].name

    def test_single_quoted(self, db):
        """Single quoted function names should be ignored."""
        double = DocLink(name='double')
        links = (DocLink(name='func1'), DocLink(name='func2'))

        docstring = ("doc string for <strong>'%s'</strong>, " +
                     '<strong>%s</strong> and <strong>%s</strong>') % \
            (double.name, links[0].name, links[1].name)

        output = matl.add_doc_links(docstring)

        soup = BeautifulSoup(output, 'html.parser')
        strongs = soup.findAll('strong')

        # Make sure the first one wasn't converted to a link
        assert strongs[0].a is None

        # Remove it and make sure everything else is golden
        strongs = strongs[1:]

        assert len(strongs) == len(links)

        for k, strong in enumerate(strongs):
            assert strong.a['href'] == links[k].link
            assert strong.a.text == links[k].name

    def test_complex_function(self, db):
        """Test when there is a multi-function example."""
        mat2cell = DocLink(name='mat2cell')
        ones = DocLink(name='ones')
        size = DocLink(name='size')
        ndims = DocLink(name='ndims')

        expected = [mat2cell, ones, size, size, size, ndims]

        ex = 'mat2cell(x, ones(size(x,1),1), size(x,2),...,size(x,ndims(x)))'
        docstring = 'Doc for: <strong>%s</strong>' % ex

        output = matl.add_doc_links(docstring)

        soup = BeautifulSoup(output, 'html.parser')

        assert len(soup.findAll('strong')) == 1

        links = soup.strong.findAll('a')

        assert len(links) == len(expected)

        for k, link in enumerate(links):
            assert link.text == expected[k].name
            assert link['href'] == expected[k].link


class TestResults:
    """Series of tests to ensure proper MATL output parsing."""

    def test_error_parsing(self):
        """All errors are correctly classified."""
        msg = 'single error'
        result = matl.parse_matl_results('[STDERR]' + msg)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stderr'
        assert result[0]['value'] == msg

    def test_invalid_image_parsing(self):
        """Test with a bad filename and ensure no result."""
        filename = '/ignore/this/filename.png'
        result = matl.parse_matl_results('[IMAGE]' + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_nn_image_parsing(self, tmpdir):
        """Test for nearest-neighbor interpolated image."""
        fileobj = tmpdir.join('image.png')
        contents = b'hello'
        fileobj.write(contents)

        # Parse the string
        result = matl.parse_matl_results('[IMAGE_NN]' + fileobj.strpath)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'image_nn'

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents)
        assert result[0]['value'] == b'data:image/png;base64,' + encoded

        # Make sure the file was not removed
        assert os.path.isfile(fileobj.strpath)

    def test_image_parsing(self, tmpdir):
        """Test valid image result."""
        fileobj = tmpdir.join('image.png')
        contents = b'hello'
        fileobj.write(contents)

        # Parse the string
        result = matl.parse_matl_results('[IMAGE]' + fileobj.strpath)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'image'

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents)
        assert result[0]['value'] == b'data:image/png;base64,' + encoded

        # Make sure the file was not removed
        assert os.path.isfile(fileobj.strpath)

    def test_invalid_audio_parsing(self):
        """Test with a bad filename and ensure no result."""
        filename = '/ignore/this/audio.wav'
        result = matl.parse_matl_results('[AUDIO]' + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_audio_parsing(self, tmpdir):
        """Test valid audio result."""
        fileobj = tmpdir.join('audio.wav')
        contents = b'AUDIO'
        fileobj.write(contents)

        # Parse the string
        result = matl.parse_matl_results('[AUDIO]' + fileobj.strpath)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'audio'

        encoded = base64.b64encode(contents)
        assert result[0]['value'] == b'data:audio/wav;base64,' + encoded

        # Make sure that the file was not removed
        assert os.path.isfile(fileobj.strpath)

    def test_stdout2_parsing(self):
        """Test potential to have a second type of STDOUT."""
        expected = 'ouptut2'
        result = matl.parse_matl_results('[STDOUT]' + expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout2'
        assert result[0]['value'] == expected

    def test_stdout_single_line_parsing(self):
        """A single line of output is handled as STDOUT."""
        expected = 'standard output'
        result = matl.parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout'
        assert result[0]['value'] == expected

    def test_stdout_multi_line_parsing(self):
        """Multi-line output is also handled as STDOUT if not specified."""
        expected = 'standard\noutput'
        result = matl.parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout'
        assert result[0]['value'] == expected


class TestHelpParsing:
    """Series of tests for checking help to JSON conversion."""

    def test_generate_help_json(self, tmpdir, mocker, db):
        """Check all reading / parsing of help .mat file."""
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
        assert len(data['data']) == 3

        # Make sure it has all the necessary keys
        expected = ['source', 'description', 'brief', 'arguments']
        expected.sort()

        actual = list(data['data'][0].keys())
        actual.sort()

        assert actual == expected

        item = data['data'][0]

        # make sure all newlines were removed from description
        assert item.get('description').find('\n') == -1
        assert item.get('arguments') == ''
        assert item.get('source') == '&amp;'
        assert item.get('brief') == 'alternative input/output specification'

        item = data['data'][1]

        assert item.get('description').find('\n') == -1
        assert item.get('arguments') == '1--2 (1 / 2);  1'
        assert item.get('source') == 'a'
        assert item.get('brief') == 'any'

        item = data['data'][2]

        assert item.get('description') == '    '
        assert item.get('arguments') == '0;  1'
        assert item.get('source') == 'Y?'
        assert item.get('brief') == ''

    def test_help_json_exists(self, tmpdir, mocker):
        """Verify correctness of output JSON."""
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
    """Tests to check if MATL is properly downloaded and installed."""

    def test_valid_version(self, tmpdir, mocker, app):
        """Test using a version which we know to exist on github."""
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
        """Try to install a version which does NOT exist on github."""
        get = mocker.patch('matl_online.matl.requests.get')
        get.return_value.status_code = 404

        with pytest.raises(KeyError):
            matl.install_matl('3.4.5', tmpdir.strpath)


class TestReleaseRefresh:
    """Tests for updating our local release database from github."""

    def test_all_new(self, mocker, app, db):
        """Completely populate the database (no previous entries)."""
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
        """Ensure that pre-releases are ignored."""
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
        """Updated releases should be updated in our database."""
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
        """Updated releases should remove the old source code."""
        matl_folder = mocker.patch('matl_online.matl.get_matl_folder')
        matl_folder.return_value = tmpdir.strpath

        assert os.path.isdir(tmpdir.strpath)

        self.test_updated_release(mocker, app, db)

        assert not os.path.isdir(tmpdir.strpath)


class TestMATLInterface:
    """Some basic tests to check that the MATL interface is working."""

    def test_empty_inputs(self, mocker, app, moctave):
        """If no inputs are provided, MATL shouldn't receive any."""
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

    def test_single_input(self, mocker, app, moctave):
        """Single input parameter should be send to matl_runner."""
        get_matl_folder = mocker.patch('matl_online.matl.get_matl_folder')
        get_matl_folder.return_value = ''

        matl.matl(moctave, '-ro', code='D', inputs='12')

        # Find the call to matl_runner
        call = [x for x in moctave.evals if x.startswith('matl_runner')]

        assert len(call) == 1
        assert call[0].rstrip() == "matl_runner('-ro', {'D'}, '12');"

    def test_multiple_inputs(self, mocker, app, moctave):
        """Multiple input parameters should be send to matl_runner."""
        get_matl_folder = mocker.patch('matl_online.matl.get_matl_folder')
        get_matl_folder.return_value = ''

        matl.matl(moctave, '-ro', code='D', inputs='12\n13')

        # Find the call to matl_runner
        call = [x for x in moctave.evals if x.startswith('matl_runner')]

        assert len(call) == 1
        assert call[0].rstrip() == "matl_runner('-ro', {'D'}, '12','13');"

    def test_string_escape(self, mocker, app, moctave):
        """All single quotes need to be escaped properly."""
        get_matl_folder = mocker.patch('matl_online.matl.get_matl_folder')
        get_matl_folder.return_value = ''

        matl.matl(moctave, '-ro', code="'abc'")

        # Find the call to matl_runner
        call = [x for x in moctave.evals if x.startswith('matl_runner')]

        assert len(call) == 1
        assert call[0].rstrip() == "matl_runner('-ro', {'''abc'''});"
