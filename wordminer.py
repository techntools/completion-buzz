# re relies on C code to do the actual matching.
import re


class WordMiner():
    def __init__(self, initfilelist=[]):
        self.words = set()
        self.filewords = {}

    def minetheline(self, keywordpattern, line):
        return re.findall(keywordpattern, line)

    def mine(self, keywordpattern, filecontent):
        results = re.findall(keywordpattern, filecontent)
        self.words.update(results)

    def update_words_per_file(self, fileloc):
        if fileloc not in self.filewords:
            self.filewords[fileloc] = {}

        with open(fileloc) as f:
            for _, line in enumerate(f, 1):
                self.words.update(self.minetheline('[a-zA-Z0-9_]+', line))


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
