import base64
import os

from matl_online.matl import parse_matl_results


class TestResults:

    def test_error_parsing(self):

        msg = 'single error'
        result = parse_matl_results('[STDERR]' + msg)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stderr'
        assert result[0]['value'] == msg

    def test_invalid_image_parsing(self):
        # Test with a bad filename and ensure no result
        filename = '/ignore/this/filename.png'
        result = parse_matl_results('[IMAGE]' + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_image_parsing(self, tmpdir):
        fileobj = tmpdir.join('image.png')
        contents = 'hello'
        fileobj.write(contents)

        # Parse the string
        result = parse_matl_results('[IMAGE]' + fileobj.strpath)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'image'

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents)
        assert result[0]['value'] == 'data:image/png;base64,' + encoded

        # Make sure the file was not removed
        assert os.path.isfile(fileobj.strpath)

    def test_stdout_single_line_parsing(self):

        # Single line
        expected = 'standard output'
        result = parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout'
        assert result[0]['value'] == expected

    def test_stdout_multi_line_parsing(self):
        # Multi-line
        expected = 'standard\noutput'
        result = parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'stdout'
        assert result[0]['value'] == expected
