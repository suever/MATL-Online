class MockZipFile:

    def __init__(self, *args, **kwargs):
        self.files = []
        self.extract_arguments = ()

    def addFiles(self, *args):
        self.files.extend(args)

    def namelist(self):
        return self.files

    def infolist(self):
        # filename: filename
        return [type('info', (object,), {'filename': x}) for x in self.files]

    def extractall(self, *args):
        self.extract_arguments = args
