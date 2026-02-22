"""Tests for util.py - shared helpers."""

from src.util import CONSONANTS, VOWELS, is_consonant, is_vowel, normalize


class TestNormalize:
    def test_basic(self):
        assert normalize("Hello World") == "helloworld"

    def test_strips_punctuation(self):
        assert normalize("it's a test!") == "itsatest"

    def test_strips_digits(self):
        assert normalize("abc123def") == "abcdef"

    def test_empty(self):
        assert normalize("") == ""

    def test_all_non_alpha(self):
        assert normalize("123 !@#") == ""

    def test_preserves_all_letters(self):
        assert normalize("AaBbCc") == "aabbcc"


class TestVowelsConsonants:
    def test_vowels_set(self):
        assert {"a", "e", "i", "o", "u", "y"} == VOWELS

    def test_y_is_both_vowel_and_consonant(self):
        # 'y' is intentionally classified as both (semi-vowel)
        assert {"y"} == VOWELS & CONSONANTS

    def test_all_letters_covered(self):
        all_alpha = set("abcdefghijklmnopqrstuvwxyz")
        assert all_alpha == VOWELS | CONSONANTS

    def test_is_vowel(self):
        for v in "aeiouy":
            assert is_vowel(v)
        assert not is_vowel("b")

    def test_is_vowel_uppercase(self):
        assert is_vowel("A")
        assert is_vowel("E")

    def test_is_consonant(self):
        for c in "bcdfg":
            assert is_consonant(c)
        assert not is_consonant("a")
