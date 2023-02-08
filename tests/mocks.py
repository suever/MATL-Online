"""Module for creating some custom mock objects."""

from typing import Any, List, Tuple


class MockZipFile:
    """Mock zip file that implements only the methods we use for testing."""

    files: List[str]
    extract_all_arguments: Tuple[Any, ...]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the mock object."""
        self.files = []
        self.extract_all_arguments = ()

    def add_files(self, *args: Any) -> None:
        """Add files to this archive."""
        self.files.extend(args)

    def namelist(self) -> List[str]:
        """Get a list of all files in the archive."""
        return self.files

    def infolist(self) -> List[Any]:
        """Get metadata about all the files."""
        return [type("info", (object,), {"filename": x}) for x in self.files]

    def extractall(self, *args: Any) -> None:
        """Pretend to extract all the files and record inputs."""
        self.extract_all_arguments = args
