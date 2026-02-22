#!/usr/bin/env python3
"""Anagrammer: Generate name-like anagrams from words and phrases.

Usage:
    python anagrammer.py "Whistleblower"
    python anagrammer.py "Pride goes before the fall" --dataset female -n 8
    python anagrammer.py "Split Loyalty" --seed 42 --verbose
"""

import argparse
import random
import sys

from src.generator import AnagramGenerator
from src.letterbag import LetterBag
from src.util import normalize


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate name-like anagrams from a word or phrase.",
    )
    parser.add_argument(
        "phrase",
        nargs="?",
        default=None,
        help="Word or phrase to anagram",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=15,
        help="Number of name candidates to generate (default: 15)",
    )
    parser.add_argument(
        "-d",
        "--dataset",
        choices=["both", "male", "female"],
        default="both",
        help="Training dataset: 'both' (all), 'male', or 'female'",
    )
    parser.add_argument(
        "-t",
        "--template",
        default=None,
        help="Use a specific name template (e.g., 'First Last', 'First M. Last')",
    )
    parser.add_argument(
        "--first",
        default=None,
        help="Lock in a specific first name (its letters must be in the input phrase)",
    )
    parser.add_argument(
        "--last",
        default=None,
        help=(
            "Lock in a specific last name. Supports hyphenated forms:"
            " 'Smith' (primary), 'Smith-Jones' (both), '-Jones' (second only)"
        ),
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List all available name templates and exit",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show scores and template details",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force Markov model rebuild, ignoring cached model",
    )
    parser.add_argument(
        "--temp",
        type=float,
        default=None,
        help="Set both temp-min and temp-max to a constant temperature",
    )
    parser.add_argument(
        "--allow-words",
        action="store_true",
        help="Allow name segments that are recognizable English words",
    )
    parser.add_argument(
        "--temp-min",
        type=float,
        default=None,
        help="Minimum sampling temperature (default: 1.2)",
    )
    parser.add_argument(
        "--temp-max",
        type=float,
        default=None,
        help="Maximum sampling temperature (default: 2.0)",
    )
    # Preprocess argv so values like "-Delphae" (starting with a dash) are not
    # mistaken for flags.  Rewrite "--first <val>" / "--last <val>" to use the
    # equals form ("--last=-Delphae") which argparse always handles correctly.
    raw = sys.argv[1:]
    fixed = []
    i = 0
    while i < len(raw):
        if raw[i] in ("--first", "--last") and i + 1 < len(raw):
            fixed.append(f"{raw[i]}={raw[i + 1]}")
            i += 2
        else:
            fixed.append(raw[i])
            i += 1

    return parser.parse_args(fixed)


def validate_input(phrase):
    """Validate the input phrase and return normalized letters."""
    # Check for non-ASCII
    non_ascii = [c for c in phrase if ord(c) > 127]
    if non_ascii:
        chars = "".join(set(non_ascii))
        print(f"Warning: Non-ASCII characters ignored: {chars}", file=sys.stderr)

    normalized = normalize(phrase)

    if not normalized:
        print("Error: Input must contain at least one letter.", file=sys.stderr)
        sys.exit(1)

    if len(normalized) < 3:
        print(
            "Error: Input must contain at least 3 letters to generate a name.",
            file=sys.stderr,
        )
        sys.exit(1)

    return normalized


def validate_fixed_names(fixed_first, fixed_last, input_bag):
    """Validate that fixed name letters are available in the input bag."""
    combined = ""
    if fixed_first:
        combined += normalize(fixed_first)
    if fixed_last:
        # Strip hyphens before checking — hyphens are structural, not letters
        combined += normalize(fixed_last.replace("-", ""))

    if not combined:
        return

    fixed_bag = LetterBag(combined)
    if not fixed_bag.is_subset_of(input_bag):
        missing = fixed_bag.missing_from(input_bag)
        names = []
        if fixed_first:
            names.append(f"'{fixed_first}'")
        if fixed_last:
            names.append(f"'{fixed_last}'")
        print(
            f"Error: Cannot form {' and '.join(names)} from the input letters."
            f" Missing: {missing}",
            file=sys.stderr,
        )
        sys.exit(1)


def verify_anagram(original_phrase, generated_name):
    """Verify that a generated name is a perfect anagram of the input."""
    original = LetterBag(original_phrase)
    result = LetterBag(generated_name)
    return original == result


def main():
    args = parse_args()

    # Handle --list-templates
    if args.list_templates:
        from src.templates import list_templates

        print("Available templates:\n")
        for label, min_l, max_l in list_templates():
            print(f"  {label:<30}  ({min_l}-{max_l} letters)")
        sys.exit(0)

    # Phrase is required unless --list-templates was used
    if args.phrase is None:
        print("Error: A phrase argument is required.", file=sys.stderr)
        sys.exit(1)

    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)

    # Validate input
    normalized = validate_input(args.phrase)
    bag = LetterBag(normalized)

    # Validate fixed names
    if args.first or args.last:
        validate_fixed_names(args.first, args.last, bag)

    # Show input info in verbose mode
    if args.verbose:
        print(
            f'Input: "{args.phrase}" ({bag.total()} letters: {bag.as_sorted_string()})'
        )
        if args.template:
            print(f"Template: {args.template}")
        if args.first:
            print(f"Fixed first name: {args.first}")
        if args.last:
            print(f"Fixed last name: {args.last}")
        print()

    # Resolve temperature parameters
    temp_min = args.temp_min
    temp_max = args.temp_max
    if args.temp is not None:
        temp_min = args.temp
        temp_max = args.temp

    # Generate
    gen = AnagramGenerator(dataset=args.dataset, no_cache=args.no_cache)
    results = gen.generate(
        args.phrase,
        n_results=args.count,
        template_label=args.template,
        fixed_first=args.first,
        fixed_last=args.last,
        temp_min=temp_min,
        temp_max=temp_max,
        allow_words=args.allow_words,
    )

    if not results:
        print(
            "Could not generate any valid names from this input."
            " Try a different phrase.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Display results
    for i, (name, score, label, _segments) in enumerate(results, 1):
        if args.verbose:
            # Verify anagram property
            is_valid = verify_anagram(args.phrase, name)
            status = "OK" if is_valid else "MISMATCH"
            print(f"{i:>3}. {name:<30} [score: {score:>7.1f}] [{label}] [{status}]")
        else:
            print(f"{i:>3}. {name}")


if __name__ == "__main__":
    main()
