from matl_online.types import (
    MATLExplainTaskParameters,
    MATLRunTaskParameters,
    MATLTaskParameters,
)


class TestMATLTaskParameters:
    def test_flags(self) -> None:
        # Given a MATLTaskParameters object
        params = MATLTaskParameters(code="", version="")

        # When accessing the flags
        flags = params.flags

        # They include only the defaults
        assert flags == "-o"

    def test_single_line_code(self) -> None:
        # Given params with a single line of code
        params = MATLTaskParameters(code="single line", version="")

        # The code lines are as expected
        assert params.code_lines == ["single line"]

    def test_multi_line_code(self) -> None:
        # Given params with multiple lines of code
        params = MATLTaskParameters(code="multiple\n lines", version="")

        # The code lines are as expected
        assert params.code_lines == ["multiple", " lines"]

    def test_single_input(self) -> None:
        # Given params with a single input
        params = MATLTaskParameters(code="input", version="")

        # The code lines are as expected
        assert params.code_lines == ["input"]

    def test_multiple_inputs(self) -> None:
        # Given params with multiple inputs
        params = MATLTaskParameters(code="input1\n input2", version="")

        # The code lines are as expected
        assert params.code_lines == ["input1", " input2"]


class TestMATLRunTaskParameters:
    def test_flags(self) -> None:
        # Given a MATLRunTaskParameters object
        params = MATLRunTaskParameters(code="", version="")

        # When accessing the flags
        flags = params.flags

        # They include the expected values
        assert flags == "-or"


class TestMATLExplainTaskParameters:
    def test_flags(self) -> None:
        # Given a MATLExplainTaskParameters object
        params = MATLExplainTaskParameters(code="", version="")

        # When accessing the flags
        flags = params.flags

        # They include the expected values
        assert flags == "-oe"
