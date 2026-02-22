"""Tests for markov.py - trigram Markov chain model."""

from src.letterbag import LetterBag
from src.markov import MarkovModel


def _small_model():
    """Train a model on a small name set for testing."""
    model = MarkovModel()
    model.train(["alice", "bob", "carol", "dave", "eve", "frank", "grace"])
    return model


class TestMarkovTraining:
    def test_marks_trained(self):
        model = _small_model()
        assert model.trained

    def test_untrained_model(self):
        model = MarkovModel()
        assert not model.trained

    def test_has_log_probs(self):
        model = _small_model()
        assert len(model.log_probs) > 0

    def test_has_unigram_probs(self):
        model = _small_model()
        assert len(model.unigram_log_probs) > 0

    def test_skips_non_alpha(self):
        model = MarkovModel()
        model.train(["alice", "123", "bob-joe", ""])
        # Should still train on "alice" only (bob-joe has hyphen)
        assert model.trained


class TestMarkovScoring:
    def test_score_segment_returns_float(self):
        model = _small_model()
        score = model.score_segment("alice")
        assert isinstance(score, float)

    def test_empty_segment_score(self):
        model = _small_model()
        assert model.score_segment("") == -100.0

    def test_trained_name_scores_higher(self):
        model = _small_model()
        # A name from training should score higher than random consonants
        trained_score = model.score_segment("alice")
        nonsense_score = model.score_segment("xqzwj")
        assert trained_score > nonsense_score

    def test_score_name_sums_segments(self):
        model = _small_model()
        s1 = model.score_segment("alice")
        s2 = model.score_segment("bob")
        combined = model.score_name(["alice", "bob"])
        assert abs(combined - (s1 + s2)) < 1e-10


class TestGetLikelyNext:
    def test_returns_candidates(self):
        model = _small_model()
        bag = LetterBag("abcde")
        candidates = model.get_likely_next("al", bag)
        assert len(candidates) > 0

    def test_only_available_letters(self):
        model = _small_model()
        bag = LetterBag("ae")
        candidates = model.get_likely_next("al", bag)
        chars = {c for c, _ in candidates}
        assert chars <= {"a", "e"}

    def test_sorted_by_probability(self):
        model = _small_model()
        bag = LetterBag("abcde")
        candidates = model.get_likely_next("al", bag)
        probs = [p for _, p in candidates]
        assert probs == sorted(probs, reverse=True)
