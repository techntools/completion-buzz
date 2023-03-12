from wordminer import WordMiner


def test_wordminer():
    wordminer = WordMiner()
    wordminer.update_words_per_file('./tests/words.txt')
    assert len(wordminer.words) == 113809


# Run with python -m pytest tests/
