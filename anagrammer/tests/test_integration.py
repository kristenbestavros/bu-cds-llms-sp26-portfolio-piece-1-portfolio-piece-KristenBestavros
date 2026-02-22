"""Integration tests - end-to-end anagram generation and verification."""

import random

from anagrammer import validate_fixed_names, verify_anagram
from src.generator import AnagramGenerator
from src.letterbag import LetterBag
from src.util import normalize


class TestVerifyAnagram:
    def test_valid_anagram(self):
        assert verify_anagram("listen", "Silent")

    def test_invalid_anagram(self):
        assert not verify_anagram("hello", "world")

    def test_ignores_spaces_and_case(self):
        assert verify_anagram("William Shakespeare", "I am a weakish speller")

    def test_ignores_punctuation(self):
        assert verify_anagram("abc", "A.B.C.")


class TestEndToEnd:
    """Integration tests that run the full generation pipeline."""

    def test_generates_results(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        results = gen.generate("William Shakespeare", n_results=5)
        assert len(results) > 0

    def test_all_results_are_perfect_anagrams(self):
        """The core invariant: every result uses exactly the input letters."""
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "Hello World"
        results = gen.generate(phrase, n_results=5)
        normalized_input = normalize(phrase)
        input_bag = LetterBag(normalized_input)

        for name, _score, _label, _segments in results:
            result_bag = LetterBag(name)
            assert result_bag == input_bag, (
                f"Anagram mismatch: '{name}' is not a perfect anagram of '{phrase}'"
            )

    def test_results_have_expected_shape(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        results = gen.generate("Testing", n_results=3)
        for name, score, label, segments in results:
            assert isinstance(name, str)
            assert isinstance(score, float)
            assert isinstance(label, str)
            assert isinstance(segments, list)

    def test_short_input_returns_empty(self):
        gen = AnagramGenerator(dataset="both")
        results = gen.generate("ab", n_results=5)
        assert results == []

    def test_seed_reproducibility(self):
        gen = AnagramGenerator(dataset="both")
        random.seed(42)
        r1 = gen.generate("Reproducible", n_results=5)
        random.seed(42)
        r2 = gen.generate("Reproducible", n_results=5)
        names1 = [name for name, *_ in r1]
        names2 = [name for name, *_ in r2]
        assert names1 == names2

    def test_female_dataset(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="female")
        results = gen.generate("Dragon Fire", n_results=3)
        assert len(results) > 0
        # Verify anagram property for female dataset too
        input_bag = LetterBag(normalize("Dragon Fire"))
        for name, _score, _label, _segments in results:
            assert LetterBag(name) == input_bag

    def test_male_dataset(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="male")
        results = gen.generate("Dragon Fire", n_results=3)
        assert len(results) > 0
        input_bag = LetterBag(normalize("Dragon Fire"))
        for name, _score, _label, _segments in results:
            assert LetterBag(name) == input_bag


class TestTemperature:
    """Tests for custom temperature parameters."""

    def test_custom_temperature_produces_valid_anagrams(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "Hello World"
        results = gen.generate(phrase, n_results=5, temp_min=0.8, temp_max=0.8)
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, _label, _segments in results:
            assert LetterBag(name) == input_bag

    def test_constant_temperature_is_reproducible(self):
        gen = AnagramGenerator(dataset="both")
        random.seed(42)
        r1 = gen.generate("Dragon Fire", n_results=3, temp_min=1.5, temp_max=1.5)
        random.seed(42)
        r2 = gen.generate("Dragon Fire", n_results=3, temp_min=1.5, temp_max=1.5)
        names1 = [name for name, *_ in r1]
        names2 = [name for name, *_ in r2]
        assert names1 == names2

    def test_default_temperature_unchanged(self):
        """Omitting temp args should produce the same results as before."""
        gen = AnagramGenerator(dataset="both")
        random.seed(42)
        r1 = gen.generate("Testing", n_results=3)
        random.seed(42)
        r2 = gen.generate("Testing", n_results=3, temp_min=None, temp_max=None)
        names1 = [name for name, *_ in r1]
        names2 = [name for name, *_ in r2]
        assert names1 == names2


class TestTemplateFlag:
    """Tests for --template functionality."""

    def test_template_flag_selects_template(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        results = gen.generate("Hello World", n_results=5, template_label="First Last")
        assert len(results) > 0
        for _name, _score, label, _segments in results:
            assert label == "First Last"

    def test_template_flag_anagram_invariant(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "Hello World"
        results = gen.generate(phrase, n_results=5, template_label="First Last")
        input_bag = LetterBag(normalize(phrase))
        for name, _score, _label, _segments in results:
            assert LetterBag(name) == input_bag

    def test_invalid_template_returns_empty(self):
        gen = AnagramGenerator(dataset="both")
        results = gen.generate("Hello World", template_label="Nonexistent")
        assert results == []

    def test_physically_impossible_template_returns_empty(self):
        gen = AnagramGenerator(dataset="both")
        # "hello" = 5 letters, "First Middle Last" needs 3 segments of 2+ = 6 minimum
        results = gen.generate("hello", template_label="First Middle Last")
        assert results == []

    def test_template_outside_range_still_works(self):
        """Explicit template outside designed range should warn but produce results."""
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        # 22 letters, "First Last" designed for 6-17
        phrase = "a stitch in time saves nine"
        results = gen.generate(phrase, n_results=5, template_label="First Last")
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, label, _segments in results:
            assert label == "First Last"
            assert LetterBag(name) == input_bag

    def test_truly_impossible_template_returns_empty(self):
        gen = AnagramGenerator(dataset="both")
        # 4 letters cannot fill 3 non-initial segments (need 6+)
        results = gen.generate("word", template_label="First Middle Last")
        assert results == []


class TestFixedNames:
    """Tests for --first and --last functionality."""

    def test_fixed_first_anagram_invariant(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "pride goes before the fall"
        results = gen.generate(phrase, n_results=5, fixed_first="Rigel")
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, _label, _segments in results:
            assert LetterBag(name) == input_bag

    def test_fixed_first_appears_in_results(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        results = gen.generate(
            "pride goes before the fall", n_results=5, fixed_first="Rigel"
        )
        assert len(results) > 0
        for _name, _score, _label, segments in results:
            assert segments[0] == "rigel"

    def test_fixed_last_appears_in_results(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        results = gen.generate("William Shakespeare", n_results=5, fixed_last="Spear")
        assert len(results) > 0
        for _name, _score, _label, segments in results:
            # Last name is the last non-hyphenated LAST segment
            assert "spear" in [s.lower() for s in segments]

    def test_fixed_last_anagram_invariant(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "William Shakespeare"
        results = gen.generate(phrase, n_results=5, fixed_last="Spear")
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, _label, _segments in results:
            assert LetterBag(name) == input_bag

    def test_combined_first_and_last(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "William Shakespeare"
        results = gen.generate(
            phrase, n_results=5, fixed_first="Eli", fixed_last="Shaw"
        )
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, _label, segments in results:
            assert LetterBag(name) == input_bag
            assert segments[0] == "eli"

    def test_combined_template_and_first(self):
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "Hello World"
        results = gen.generate(
            phrase,
            n_results=5,
            template_label="First Last",
            fixed_first="Hello",
        )
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, label, segments in results:
            assert label == "First Last"
            assert segments[0] == "hello"
            assert LetterBag(name) == input_bag

    def test_fixed_hyphenated_last(self):
        """--last 'Smith-Jones' should fill both LAST and HYPHENATED_LAST."""
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "the pen is mightier than the sword"
        results = gen.generate(phrase, n_results=5, fixed_last="Prith-Towing")
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, _label, segments in results:
            assert LetterBag(name) == input_bag
            assert "prith" in segments
            assert "towing" in segments

    def test_fixed_hyph_last_second_position(self):
        """--last '-Thorne' should place Thorne in the HYPHENATED_LAST slot."""
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "the pen is mightier than the sword"
        results = gen.generate(phrase, n_results=5, fixed_last="-Thorne")
        assert len(results) > 0
        input_bag = LetterBag(normalize(phrase))
        for name, _score, _label, segments in results:
            assert LetterBag(name) == input_bag
            # Thorne should be in the last position (hyphenated)
            assert "thorne" in segments

    def test_fixed_last_trailing_hyphen_stripped(self):
        """--last 'Jones-' should behave same as --last 'Jones'."""
        random.seed(42)
        gen = AnagramGenerator(dataset="both")
        phrase = "pride goes before the fall"
        r1 = gen.generate(phrase, n_results=5, fixed_last="Beford")
        random.seed(42)
        r2 = gen.generate(phrase, n_results=5, fixed_last="Beford-")
        names1 = [name for name, *_ in r1]
        names2 = [name for name, *_ in r2]
        assert names1 == names2


class TestValidateFixedNames:
    def test_valid_fixed_name_passes(self):
        bag = LetterBag("abcdefghij")
        # Should not raise
        validate_fixed_names("abc", None, bag)

    def test_invalid_fixed_name_exits(self):
        import pytest

        bag = LetterBag("abc")
        with pytest.raises(SystemExit):
            validate_fixed_names("xyz", None, bag)

    def test_hyphenated_last_validates_letters_only(self):
        bag = LetterBag("abcdefghij")
        # Should not raise — hyphen is stripped before checking letters
        validate_fixed_names(None, "abc-def", bag)
