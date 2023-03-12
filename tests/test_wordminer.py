from wordminer import WordMiner


def test_wordminer():
    wordminer = WordMiner()
    wordminer.update_words_per_file('./tests/words.txt')
    assert len(wordminer.words) == 113809


# pytest does not add the current directory in the PYTHONPATH itself, but
# here's a workaround (to be executed from the root of your repository):
#
# python -m pytest tests/
#
# It works because Python adds the current directory in the PYTHONPATH for you.
#
# But with pytest.ini just using pytest is enough.
