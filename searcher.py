class Searcher():
    matchtype = ('substring', 'fuzzy', 'prefix')

    def findmatches(self, wordset, prefix, matchtype=matchtype[2]):
        # Python's difflib.get_close_matches also sounds useful
        return {v for v in wordset if v.startswith(prefix)}


if __name__ == '__main__':
    import time

    from nltk.corpus import words

    start = time.perf_counter()
    [v for v in words.words() if 'thr' in v]
    end = time.perf_counter()

    print(end - start)
