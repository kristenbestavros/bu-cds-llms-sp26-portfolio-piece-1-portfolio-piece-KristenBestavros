"""Tests for letterbag.py - LetterBag multiset utility."""

import pytest

from src.letterbag import LetterBag


class TestConstruction:
    def test_from_string(self):
        bag = LetterBag("hello")
        assert bag.total() == 5
        assert bag.count("l") == 2

    def test_ignores_non_alpha(self):
        bag = LetterBag("a1b!c ")
        assert bag.total() == 3

    def test_lowercases(self):
        bag = LetterBag("AbC")
        assert bag.contains("a")
        assert bag.contains("b")
        assert bag.contains("c")

    def test_empty(self):
        bag = LetterBag("")
        assert bag.is_empty()
        assert bag.total() == 0


class TestContainsAndCount:
    def test_contains(self):
        bag = LetterBag("abc")
        assert bag.contains("a")
        assert not bag.contains("z")

    def test_count(self):
        bag = LetterBag("aab")
        assert bag.count("a") == 2
        assert bag.count("b") == 1
        assert bag.count("z") == 0


class TestSubtractAndAdd:
    def test_subtract(self):
        bag = LetterBag("hello")
        bag.subtract("hel")
        assert bag.total() == 2
        assert bag.count("l") == 1
        assert bag.count("o") == 1

    def test_subtract_raises_on_missing(self):
        bag = LetterBag("ab")
        with pytest.raises(ValueError, match="not available"):
            bag.subtract("z")

    def test_subtract_raises_on_excess(self):
        bag = LetterBag("a")
        with pytest.raises(ValueError, match="not available"):
            bag.subtract("aa")

    def test_add(self):
        bag = LetterBag("a")
        bag.add("b")
        assert bag.contains("b")
        assert bag.total() == 2


class TestUtilities:
    def test_is_empty(self):
        bag = LetterBag("a")
        assert not bag.is_empty()
        bag.subtract("a")
        assert bag.is_empty()

    def test_available_letters(self):
        bag = LetterBag("abba")
        assert bag.available_letters() == {"a", "b"}

    def test_copy_is_independent(self):
        bag = LetterBag("abc")
        copy = bag.copy()
        copy.subtract("a")
        assert bag.count("a") == 1  # original unchanged

    def test_as_sorted_string(self):
        bag = LetterBag("cab")
        assert bag.as_sorted_string() == "abc"


class TestSubsetAndMissing:
    def test_subset_true(self):
        small = LetterBag("ab")
        big = LetterBag("abc")
        assert small.is_subset_of(big)

    def test_subset_false(self):
        small = LetterBag("az")
        big = LetterBag("abc")
        assert not small.is_subset_of(big)

    def test_subset_respects_multiplicity(self):
        assert not LetterBag("aab").is_subset_of(LetterBag("ab"))
        assert LetterBag("aab").is_subset_of(LetterBag("aab"))

    def test_empty_is_subset_of_anything(self):
        assert LetterBag("").is_subset_of(LetterBag("abc"))

    def test_missing_from(self):
        bag = LetterBag("axyz")
        other = LetterBag("abc")
        assert bag.missing_from(other) == "xyz"

    def test_missing_from_with_multiplicity(self):
        bag = LetterBag("aaab")
        other = LetterBag("ab")
        assert bag.missing_from(other) == "aa"

    def test_missing_from_empty_when_subset(self):
        bag = LetterBag("ab")
        other = LetterBag("abc")
        assert bag.missing_from(other) == ""


class TestEquality:
    def test_equal_bags(self):
        assert LetterBag("abc") == LetterBag("cba")

    def test_unequal_bags(self):
        assert LetterBag("abc") != LetterBag("abd")

    def test_different_counts(self):
        assert LetterBag("aab") != LetterBag("ab")

    def test_not_equal_to_non_bag(self):
        assert LetterBag("a") != "a"
