import base64
import pathlib

from matl_online.matl.io import parse_matl_results


class TestResults:
    """Series of tests to ensure proper MATL output parsing."""

    def test_error_parsing(self) -> None:
        """All errors are correctly classified."""
        msg = "single error"
        result = parse_matl_results("[STDERR]" + msg)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stderr"
        assert result[0]["value"] == msg

    def test_invalid_image_parsing(self) -> None:
        """Test with a bad filename and ensure no result."""
        filename = "/ignore/this/filename.png"
        result = parse_matl_results("[IMAGE]" + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_nn_image_parsing(self, tmp_path: pathlib.Path) -> None:
        """Test for nearest-neighbor interpolated image."""
        file_handle = tmp_path.joinpath("image.png")
        contents = b"hello"

        with open(file_handle, "wb") as fid:
            fid.write(contents)

        # Parse the string
        result = parse_matl_results("[IMAGE_NN]" + file_handle.as_posix())

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "image_nn"

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents).decode()
        assert result[0]["value"] == "data:image/png;base64," + encoded

        # Make sure the file was not removed
        assert file_handle.is_file()

    def test_image_parsing(self, tmp_path: pathlib.Path) -> None:
        """Test valid image result."""
        file_handle = tmp_path.joinpath("image.png")
        contents = b"hello"

        with open(file_handle, "wb") as fid:
            fid.write(contents)

        # Parse the string
        result = parse_matl_results("[IMAGE]" + file_handle.as_posix())

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "image"

        # Since the file is empty it should just be the header portion
        encoded = base64.b64encode(contents).decode()
        assert result[0]["value"] == "data:image/png;base64," + encoded

        # Make sure the file was not removed
        assert file_handle.is_file()

    def test_invalid_audio_parsing(self) -> None:
        """Test with a bad filename and ensure no result."""
        filename = "/ignore/this/audio.wav"
        result = parse_matl_results("[AUDIO]" + filename)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_audio_parsing(self, tmp_path: pathlib.Path) -> None:
        """Test valid audio result."""
        file_handle = tmp_path.joinpath("audio.wav")
        contents = b"AUDIO"

        with open(file_handle, "wb") as fid:
            fid.write(contents)

        # Parse the string
        result = parse_matl_results("[AUDIO]" + file_handle.as_posix())

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "audio"

        encoded = base64.b64encode(contents).decode()
        assert result[0]["value"] == "data:audio/wav;base64," + encoded

        # Make sure that the file was not removed
        assert file_handle.is_file()

    def test_stdout2_parsing(self) -> None:
        """Test potential to have a second type of STDOUT."""
        expected = "ouptut2"
        result = parse_matl_results("[STDOUT]" + expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stdout2"
        assert result[0]["value"] == expected

    def test_stdout_single_line_parsing(self) -> None:
        """A single line of output is handled as STDOUT."""
        expected = "standard output"
        result = parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stdout"
        assert result[0]["value"] == expected

    def test_stdout_multi_line_parsing(self) -> None:
        """Multi-line output is also handled as STDOUT if not specified."""
        expected = "standard\noutput"
        result = parse_matl_results(expected)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "stdout"
        assert result[0]["value"] == expected
