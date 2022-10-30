from wordminer import WordMiner
from filereader import FileReader
from searcher import Searcher


class CompletionEngine():
    def __init__(self, initfilelist=[]):
        self._filereader = FileReader()
        self._wordminer = WordMiner()
        self._searcher = Searcher()

    def minethefile(self, keywordpattern, file):
        content = self._filereader.readfile(file)
        self._wordminer.mine(keywordpattern, content)

    def startmining(self, keywordpattern, files):
        self._filereader.readfiles(files)

        for file, content in self._filereader.filesread.items():
            self._wordminer.mine(keywordpattern, content)

    def findmatches(self, prefix):
        return self._searcher.findmatches(self._wordminer.words, prefix)


if __name__ == '__main__':
    import time

    engine = CompletionEngine()

    # Note: Keywords start with albhabets, _, $ only for programming languages.
    keywordpattern = '[a-zA-Z0-9_]+'

    engine.startmining(keywordpattern, [
        'tests/tagsfile',
        'tests/cmd-bind-key.c',
        'tests/cmd-break-pane.c',
        'tests/cmd-find.c'
    ])

    start = time.perf_counter()
    matches = engine.findmatches('c')
    end = time.perf_counter()

    print('{0:<10}.{1:<8} : {2:<8}'.format(engine.__module__, engine.startmining.__name__, end - start))

    # print(matches)
