# re relies on C code to do the actual matching.
import re


class WordMiner():
    def __init__(self, initfilelist=[]):
        self.words = set()

    def minetheline(self, keywordpattern, line):
        return re.findall(keywordpattern, line)

    def mine(self, keywordpattern, filecontent):
        results = re.findall(keywordpattern, filecontent)
        self.words.update(results)


if __name__ == '__main__':
    import time
    from multiprocessing import Pool as ProcessPool

    pool = ProcessPool(4)

    wm = WordMiner()

    lines = ["I'm eric. Welcome here!", "Another boring sentence.",
             "GiraffeElephantBoat", "sfgsdg sdwerha aswertwe"] * 100000

    keywordpattern = '[a-zA-Z0-9_]+'

    start = time.perf_counter()
    results = wm.mine(keywordpattern, '\n'.join(lines))
    end = time.perf_counter()

    print('{0:<10}.{1:<8} : {2:<8}'.format(wm.__module__, wm.mine.__name__, end - start))

    # print(wm.words)
