# re relies on C code to do the actual matching.
import re


class WordMiner():
    def __init__(self, initfilelist=[]):
        self.words = []
        self.filewords = {}

    def mine(self, keywordpattern, filecontent):
        return re.findall(keywordpattern, filecontent)

    def update_words_of_file(self, keywordpattern, fileloc, filelines=None):
        self.filewords[fileloc] = set()

        if filelines is None:
            with open(fileloc) as f:
                self.filewords[fileloc].update(self.mine(keywordpattern, f.read()))
        else:
            self.filewords[fileloc].update(self.mine(keywordpattern, filelines))

        # Refreshing wordset
        words = set()
        for key, _ in self.filewords.items():
            words.update(self.filewords[key])

        self.words = list(words)


if __name__ == '__main__':
    import time

    wm = WordMiner()

    lines = ["I'm eric. Welcome here!", "Another boring sentence.",
             "GiraffeElephantBoat", "sfgsdg sdwerha aswertwe"] * 100000

    keywordpattern = '[a-zA-Z0-9_]+'

    start = time.perf_counter()
    results = wm.mine(keywordpattern, '\n'.join(lines))
    end = time.perf_counter()

    print('{0:<10}.{1:<8} : {2:<8}'.format(wm.__module__, wm.mine.__name__, end - start))

    # print(wm.words)
