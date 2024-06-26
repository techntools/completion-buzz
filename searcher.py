class Searcher():
    def findmatches(self, prefix, wordset, skip):
        # Python's difflib.get_close_matches also sounds useful
        if any(c.isupper() for c in prefix):
            return [ v for v in wordset if v.startswith(prefix) and (v not in skip) ]
        else:
            return [ v for v in wordset if v.lower().startswith(prefix) and (v not in skip) ]


if __name__ == '__main__':
    import time

    from nltk.corpus import words

    start = time.perf_counter()
    [v for v in words.words() if 'thr' in v]
    end = time.perf_counter()

    print(end - start)
