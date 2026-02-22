"""Trigram Markov chain for scoring and guiding name generation.

Trains on lists of names to learn character-level transition probabilities.
Provides scoring (how name-like is a string?) and guided next-character
selection (what letter should come next, given what's available?).
"""

import contextlib
import math
import os
import pickle
from collections import Counter, defaultdict


class MarkovModel:
    """Order-3 character-level Markov model for name-likeness."""

    ORDER = 2  # context length (trigram = 2 context chars + 1 predicted)
    START = "^^"
    END = "$"

    def __init__(self):
        self.transitions = defaultdict(Counter)
        self.log_probs = {}
        self.unigram_log_probs = {}
        self.trained = False

    def train(self, names):
        """Train the model on a list of name strings."""
        self.transitions = defaultdict(Counter)
        unigram_counts = Counter()

        for name in names:
            name = name.lower().strip()
            if not name or not name.isalpha():
                continue
            padded = self.START + name + self.END
            for i in range(len(padded) - self.ORDER):
                context = padded[i : i + self.ORDER]
                next_char = padded[i + self.ORDER]
                self.transitions[context][next_char] += 1
                if next_char != self.END:
                    unigram_counts[next_char] += 1

        # Convert to log-probabilities with Laplace smoothing
        alphabet = set("abcdefghijklmnopqrstuvwxyz") | {self.END}
        alpha_size = len(alphabet)

        self.log_probs = {}
        for context, counter in self.transitions.items():
            total = sum(counter.values()) + alpha_size
            self.log_probs[context] = {}
            for char in alphabet:
                count = counter.get(char, 0) + 1
                self.log_probs[context][char] = math.log(count / total)

        # Unigram fallback
        total_unigram = sum(unigram_counts.values()) + 26
        self.unigram_log_probs = {}
        for c in "abcdefghijklmnopqrstuvwxyz":
            count = unigram_counts.get(c, 0) + 1
            self.unigram_log_probs[c] = math.log(count / total_unigram)

        self.trained = True

    def score_segment(self, segment):
        """Return log-probability of a segment under the model."""
        if not segment:
            return -100.0
        padded = self.START + segment.lower() + self.END
        score = 0.0
        for i in range(len(padded) - self.ORDER):
            context = padded[i : i + self.ORDER]
            next_char = padded[i + self.ORDER]
            score += self._get_log_prob(context, next_char)
        return score

    def score_name(self, segments):
        """Sum of segment scores for a complete name."""
        return sum(self.score_segment(seg) for seg in segments)

    def get_likely_next(self, context, available_bag):
        """Get available next characters ranked by probability.

        Args:
            context: the last ORDER characters (or fewer at start)
            available_bag: a LetterBag of remaining letters

        Returns:
            List of (char, log_prob) sorted by probability descending.
        """
        # Pad context to ORDER length
        if len(context) < self.ORDER:
            context = self.START[-(self.ORDER - len(context)) :] + context

        candidates = []
        available = sorted(available_bag.available_letters())

        if context in self.log_probs:
            for char in available:
                if char in self.log_probs[context]:
                    candidates.append((char, self.log_probs[context][char]))
        else:
            # Backoff to bigram (last 1 char of context)
            bigram_ctx = context[-1:]
            if bigram_ctx in self.log_probs:
                for char in available:
                    if char in self.log_probs[bigram_ctx]:
                        candidates.append((char, self.log_probs[bigram_ctx][char]))
            else:
                # Unigram fallback
                for char in available:
                    if char in self.unigram_log_probs:
                        candidates.append((char, self.unigram_log_probs[char]))

        candidates.sort(key=lambda x: (-x[1], x[0]))
        return candidates

    def _get_log_prob(self, context, char):
        """Get log-probability with backoff chain."""
        # Trigram
        if context in self.log_probs and char in self.log_probs[context]:
            return self.log_probs[context][char]
        # Bigram backoff
        bigram = context[-1:]
        if bigram in self.log_probs and char in self.log_probs[bigram]:
            return self.log_probs[bigram][char] - 1.0  # penalty for backoff
        # Unigram backoff
        if char in self.unigram_log_probs:
            return self.unigram_log_probs[char] - 2.0
        return -15.0  # very unlikely

    def save(self, path):
        """Serialize the trained model to a pickle file."""
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "log_probs": self.log_probs,
                    "unigram_log_probs": self.unigram_log_probs,
                    "trained": self.trained,
                },
                f,
            )

    @classmethod
    def load(cls, path):
        """Load a trained model from a pickle file."""
        model = cls()
        with open(path, "rb") as f:
            data = pickle.load(f)
        model.log_probs = data["log_probs"]
        model.unigram_log_probs = data["unigram_log_probs"]
        model.trained = data["trained"]
        return model


def load_or_train(data_files, cache_path=None, force_rebuild=False):
    """Load a cached model or train from data files.

    Args:
        data_files: list of paths to name list text files
        cache_path: optional path for pickle cache
        force_rebuild: if True, ignore cache

    Returns:
        A trained MarkovModel.
    """
    # Check cache
    if cache_path and not force_rebuild and os.path.exists(cache_path):
        cache_mtime = os.path.getmtime(cache_path)
        data_mtime = max(os.path.getmtime(f) for f in data_files if os.path.exists(f))
        if cache_mtime > data_mtime:
            try:
                return MarkovModel.load(cache_path)
            except (pickle.UnpicklingError, KeyError, EOFError):
                pass  # corrupted cache, rebuild

    # Train from scratch
    names = []
    for path in data_files:
        with open(path, encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    names.append(name)

    model = MarkovModel()
    model.train(names)

    # Cache the result
    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with contextlib.suppress(OSError):
            model.save(cache_path)

    return model
