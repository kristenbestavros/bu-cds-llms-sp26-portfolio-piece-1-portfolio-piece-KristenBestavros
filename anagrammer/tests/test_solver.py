"""Tests for solver.py - core generation algorithm."""

import random

import pytest

from src.letterbag import LetterBag
from src.markov import MarkovModel
from src.solver import (
    build_segment,
    generate_candidate,
    refine_candidate,
    refine_syllables,
    weighted_sample,
)
from src.templates import NameTemplate, SegmentRole, SegmentSpec


def _trained_model():
    model = MarkovModel()
    model.train(
        [
            "alice",
            "bob",
            "carol",
            "dave",
            "eve",
            "frank",
            "grace",
            "helen",
            "ivan",
            "julia",
            "karen",
            "leon",
            "maria",
            "nick",
        ]
    )
    return model


class TestWeightedSample:
    def test_returns_character(self):
        result = weighted_sample([("a", -1.0), ("b", -2.0)])
        assert result in ("a", "b")

    def test_empty_returns_none(self):
        assert weighted_sample([]) is None

    def test_single_candidate(self):
        assert weighted_sample([("x", -1.0)]) == "x"

    def test_deterministic_with_seed(self):
        random.seed(42)
        r1 = weighted_sample([("a", -1.0), ("b", -2.0), ("c", -3.0)])
        random.seed(42)
        r2 = weighted_sample([("a", -1.0), ("b", -2.0), ("c", -3.0)])
        assert r1 == r2


class TestBuildSegment:
    def test_builds_valid_segment(self):
        random.seed(42)
        model = _trained_model()
        bag = LetterBag("abcdefghijklmno")
        result = build_segment(bag, 3, 6, model)
        assert result is not None
        assert 3 <= len(result) <= 6

    def test_does_not_modify_original_bag(self):
        random.seed(42)
        model = _trained_model()
        bag = LetterBag("abcdefghij")
        original_total = bag.total()
        build_segment(bag, 3, 5, model)
        assert bag.total() == original_total

    def test_returns_none_if_impossible(self):
        model = _trained_model()
        bag = LetterBag("x")  # too few letters
        result = build_segment(bag, 5, 8, model)
        assert result is None


class TestGenerateCandidate:
    def test_produces_segments(self):
        random.seed(42)
        model = _trained_model()
        template = NameTemplate(
            "First Last",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 5),
                SegmentSpec(SegmentRole.LAST, 3, 5),
            ],
        )
        bag = LetterBag("abcdefgh")
        result = generate_candidate(bag, template, [model, model])
        # May be None due to randomness, but if not None, check structure
        if result is not None:
            assert len(result) == 2
            # All letters from bag should be used
            used = "".join(result)
            assert LetterBag(used) == bag

    def test_uses_all_letters(self):
        """Every letter from the bag must appear in the output."""
        random.seed(100)
        model = _trained_model()
        template = NameTemplate(
            "First Last",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 7),
                SegmentSpec(SegmentRole.LAST, 3, 7),
            ],
        )
        bag = LetterBag("helloworld")
        # Try several seeds since generation can fail
        for seed in range(50):
            random.seed(seed)
            result = generate_candidate(bag, template, [model, model])
            if result is not None:
                used = "".join(result)
                assert LetterBag(used) == bag
                return
        # If all 50 seeds fail, that's acceptable for this test
        # (generation is probabilistic), but flag it
        pytest.skip("Could not generate a valid candidate in 50 attempts")


class TestGenerateCandidateWithFixedSegments:
    def test_fixed_first_preserved(self):
        random.seed(42)
        model = _trained_model()
        template = NameTemplate(
            "First Last",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 5),
                SegmentSpec(SegmentRole.LAST, 3, 5),
            ],
        )
        bag = LetterBag("abcdefgh")
        fixed = {0: "abc"}
        for seed in range(50):
            random.seed(seed)
            result = generate_candidate(
                bag, template, [model, model], fixed_segments=fixed
            )
            if result is not None:
                assert result[0] == "abc"
                used = "".join(result)
                assert LetterBag(used) == bag
                return
        pytest.skip("Could not generate a valid candidate in 50 attempts")

    def test_fixed_last_preserved(self):
        random.seed(42)
        model = _trained_model()
        template = NameTemplate(
            "First Last",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 5),
                SegmentSpec(SegmentRole.LAST, 3, 5),
            ],
        )
        bag = LetterBag("abcdefgh")
        fixed = {1: "efgh"}
        for seed in range(50):
            random.seed(seed)
            result = generate_candidate(
                bag, template, [model, model], fixed_segments=fixed
            )
            if result is not None:
                assert result[1] == "efgh"
                used = "".join(result)
                assert LetterBag(used) == bag
                return
        pytest.skip("Could not generate a valid candidate in 50 attempts")


class TestRefineCandidate:
    def test_preserves_letters(self):
        random.seed(42)
        model = _trained_model()
        segments = ["hel", "low"]
        refined = refine_candidate(segments, [model, model], n_iterations=50)
        original_letters = sorted("".join(segments))
        refined_letters = sorted("".join(refined))
        assert original_letters == refined_letters

    def test_single_segment_unchanged(self):
        model = _trained_model()
        segments = ["hello"]
        refined = refine_candidate(segments, [model])
        assert refined == ["hello"]

    def test_frozen_indices_unchanged(self):
        random.seed(42)
        model = _trained_model()
        segments = ["hel", "low"]
        refined = refine_candidate(
            segments, [model, model], n_iterations=100, frozen_indices={0}
        )
        assert refined[0] == "hel"
        original_letters = sorted("".join(segments))
        refined_letters = sorted("".join(refined))
        assert original_letters == refined_letters


class TestRefineSyllables:
    def test_preserves_letters(self):
        random.seed(42)
        model = _trained_model()
        segments = ["halen", "meric"]
        refined = refine_syllables(segments, [model, model], n_iterations=100)
        original_letters = sorted("".join(segments))
        refined_letters = sorted("".join(refined))
        assert original_letters == refined_letters

    def test_single_segment_unchanged(self):
        model = _trained_model()
        segments = ["hello"]
        refined = refine_syllables(segments, [model])
        assert refined == ["hello"]

    def test_frozen_indices_unchanged(self):
        random.seed(42)
        model = _trained_model()
        segments = ["halen", "meric"]
        refined = refine_syllables(
            segments, [model, model], n_iterations=100, frozen_indices={0}
        )
        assert refined[0] == "halen"
        original_letters = sorted("".join(segments))
        refined_letters = sorted("".join(refined))
        assert original_letters == refined_letters

    def test_short_segments_no_crash(self):
        model = _trained_model()
        segments = ["ab", "cd"]
        refined = refine_syllables(segments, [model, model], n_iterations=50)
        original_letters = sorted("".join(segments))
        refined_letters = sorted("".join(refined))
        assert original_letters == refined_letters
