class FileReader():
    def __init__(self):
        self._files = {}

    def readfile(self, loc):
        with open(loc, 'r') as f:
            self._files[loc] = f.read()

    def readfiles(self, files):
        for loc in files:
            try:
                with open(loc, 'r') as f:
                    self._files[loc] = f.read()
            except Exception as e:
                print(e)

    @property
    def filesread(self):
        return self._files


if __name__ == '__main__':
    import time

    fr = FileReader()

    start = time.perf_counter()
    fr.readfiles([
        'tests/tagsfile',
        'tests/cmd-bind-key.c',
        'tests/cmd-break-pane.c',
        'tests/cmd-find.c'
    ])
    end = time.perf_counter()

    print('{0:<10}.{1:<8} : {2:<8}'.format(fr.__module__, fr.readfiles.__name__, end - start))

    # print(fr.filesread)
