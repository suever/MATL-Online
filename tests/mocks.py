"""Module for creating some cusotm mock objects."""


class MockZipFile:
    """Mock zip file that implements only the methods we use for testing."""

    def __init__(self, *args, **kwargs):
        """Initialize the mock object."""
        self.files = []
        self.extract_arguments = ()

    def add_files(self, *args):
        """Add files to this archive."""
        self.files.extend(args)

    def namelist(self):
        """Get a list of all files in the archive."""
        return self.files

    def infolist(self):
        """Get metadata about all the files."""
        # filename: filename
        return [type("info", (object,), {"filename": x}) for x in self.files]

    def extractall(self, *args):
        """Pretend to extract all the files and record inputs."""
        self.extract_arguments = args
