from engine import CompletionEngine


def test_wordminer():
    engine = CompletionEngine()

    # Note: Keywords start with albhabets, _, $ only for programming languages.
    keywordpattern = '[a-zA-Z0-9_]+'

    filelist = [
        'tests/tagsfile',
        'tests/cmd-bind-key.c',
        'tests/cmd-break-pane.c',
        'tests/cmd-find.c'
    ]

    engine.update_words_per_file(keywordpattern, filelist)

    assert filelist[0] in engine._wordminer.filewords
    assert len(engine._wordminer.filewords[filelist[0]]) > 1

    assert filelist[0] in engine._wordminer.filewords
    assert len(engine._wordminer.filewords[filelist[1]]) > 1

    assert filelist[0] in engine._wordminer.filewords
    assert len(engine._wordminer.filewords[filelist[2]]) > 1

    assert filelist[0] in engine._wordminer.filewords
    assert len(engine._wordminer.filewords[filelist[3]]) > 1

    assert len(engine._wordminer.words) == 7225

    assert len(engine._wordminer.words) > len(engine._wordminer.filewords[filelist[0]])
    assert len(engine._wordminer.words) > len(engine._wordminer.filewords[filelist[1]])
    assert len(engine._wordminer.words) > len(engine._wordminer.filewords[filelist[2]])
    assert len(engine._wordminer.words) > len(engine._wordminer.filewords[filelist[3]])
