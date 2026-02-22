"""Letter multiset (bag) utility class for tracking available letters."""

from collections import Counter


class LetterBag:
    """A multiset of lowercase letters, used to track which letters are
    available during anagram construction."""

    def __init__(self, source=""):
        """Build a LetterBag from a string, keeping only alpha characters."""
        self._counts = Counter(c.lower() for c in source if c.isalpha())

    def contains(self, letter):
        """Check if the bag contains at least one of the given letter."""
        return self._counts.get(letter.lower(), 0) > 0

    def count(self, letter):
        """Return how many of the given letter are available."""
        return self._counts.get(letter.lower(), 0)

    def subtract(self, letters):
        """Remove letters from the bag. Letters can be a string or iterable."""
        for c in letters:
            c = c.lower()
            if self._counts[c] <= 0:
                raise ValueError(f"Cannot subtract '{c}': not available")
            self._counts[c] -= 1
            if self._counts[c] == 0:
                del self._counts[c]

    def add(self, letters):
        """Add letters back to the bag."""
        for c in letters:
            self._counts[c.lower()] += 1

    def is_empty(self):
        """Check if the bag has no letters remaining."""
        return self.total() == 0

    def total(self):
        """Total number of letters in the bag."""
        return sum(self._counts.values())

    def available_letters(self):
        """Return set of distinct letters currently in the bag."""
        return set(self._counts.keys())

    def copy(self):
        """Return a shallow copy of this bag."""
        new = LetterBag()
        new._counts = Counter(self._counts)
        return new

    def as_sorted_string(self):
        """Return all letters as a sorted string (for display/debugging)."""
        return "".join(sorted(self._counts.elements()))

    def is_subset_of(self, other):
        """Check if every letter in this bag exists in other (with multiplicity)."""
        for letter, count in self._counts.items():
            if other.count(letter) < count:
                return False
        return True

    def missing_from(self, other):
        """Return a string of letters in self that are not available in other."""
        missing = []
        for letter, count in sorted(self._counts.items()):
            deficit = count - other.count(letter)
            if deficit > 0:
                missing.append(letter * deficit)
        return "".join(missing)

    def __eq__(self, other):
        if isinstance(other, LetterBag):
            return self._counts == other._counts
        return NotImplemented

    def __repr__(self):
        return f"LetterBag({self.as_sorted_string()!r})"
