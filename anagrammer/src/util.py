"""Shared helpers for the anagrammer project."""

VOWELS = set("aeiouy")
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


def normalize(phrase):
    """Extract only lowercase alpha characters from a phrase."""
    return "".join(c.lower() for c in phrase if c.isalpha())


def is_vowel(c):
    return c.lower() in VOWELS


def is_consonant(c):
    return c.lower() in CONSONANTS
