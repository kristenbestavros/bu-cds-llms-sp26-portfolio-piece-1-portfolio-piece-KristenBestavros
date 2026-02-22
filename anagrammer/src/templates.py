"""Name structure templates for anagram output formatting.

Defines how a set of letter segments should be arranged into a name
(e.g., "First Last", "First M. Last-Last"). Handles template selection
based on letter count and final name formatting.
"""

import random
from dataclasses import dataclass
from enum import Enum


class SegmentRole(Enum):
    FIRST = "first"
    MIDDLE = "middle"
    LAST = "last"
    INITIAL = "initial"
    HYPHENATED_LAST = "hyph_last"


@dataclass
class SegmentSpec:
    role: SegmentRole
    min_len: int
    max_len: int


@dataclass
class NameTemplate:
    label: str
    segments: list  # list of SegmentSpec

    def total_min(self):
        return sum(s.min_len for s in self.segments)

    def total_max(self):
        return sum(s.max_len for s in self.segments)


# Template catalog organized by increasing complexity
TEMPLATES = [
    # Single name (mononym) for shorter inputs
    NameTemplate(
        "Mononym",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 10),
        ],
    ),
    # Initial + short surname for short inputs
    NameTemplate(
        "I. Last",
        [
            SegmentSpec(SegmentRole.INITIAL, 1, 1),
            SegmentSpec(SegmentRole.LAST, 2, 5),
        ],
    ),
    # Simple: First Last
    NameTemplate(
        "First Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 8),
            SegmentSpec(SegmentRole.LAST, 3, 9),
        ],
    ),
    # First M. Last
    NameTemplate(
        "First M. Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 7),
            SegmentSpec(SegmentRole.INITIAL, 1, 1),
            SegmentSpec(SegmentRole.LAST, 3, 8),
        ],
    ),
    # First Middle Last
    NameTemplate(
        "First Middle Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 7),
            SegmentSpec(SegmentRole.MIDDLE, 3, 6),
            SegmentSpec(SegmentRole.LAST, 3, 8),
        ],
    ),
    # First M. M. Last
    NameTemplate(
        "First M. M. Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 7),
            SegmentSpec(SegmentRole.INITIAL, 1, 1),
            SegmentSpec(SegmentRole.INITIAL, 1, 1),
            SegmentSpec(SegmentRole.LAST, 4, 9),
        ],
    ),
    # First M. Last-Last
    NameTemplate(
        "First M. Last-Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 7),
            SegmentSpec(SegmentRole.INITIAL, 1, 1),
            SegmentSpec(SegmentRole.LAST, 3, 8),
            SegmentSpec(SegmentRole.HYPHENATED_LAST, 3, 8),
        ],
    ),
    # First M. M. Last-Last
    NameTemplate(
        "First M. M. Last-Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 7),
            SegmentSpec(SegmentRole.INITIAL, 1, 1),
            SegmentSpec(SegmentRole.INITIAL, 1, 1),
            SegmentSpec(SegmentRole.LAST, 3, 8),
            SegmentSpec(SegmentRole.HYPHENATED_LAST, 3, 8),
        ],
    ),
    # First Middle Last-Last
    NameTemplate(
        "First Middle Last-Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 7),
            SegmentSpec(SegmentRole.MIDDLE, 3, 6),
            SegmentSpec(SegmentRole.LAST, 3, 8),
            SegmentSpec(SegmentRole.HYPHENATED_LAST, 3, 8),
        ],
    ),
    # First Middle Middle Last-Last
    NameTemplate(
        "First Middle Middle Last-Last",
        [
            SegmentSpec(SegmentRole.FIRST, 3, 7),
            SegmentSpec(SegmentRole.MIDDLE, 3, 6),
            SegmentSpec(SegmentRole.MIDDLE, 3, 6),
            SegmentSpec(SegmentRole.LAST, 3, 8),
            SegmentSpec(SegmentRole.HYPHENATED_LAST, 3, 8),
        ],
    ),
]


MIN_LETTERS_FOR_HYPHEN = 16

# Lookup table for case-insensitive template label matching
_TEMPLATE_LABELS = {t.label.lower(): t for t in TEMPLATES}


def get_template_by_label(label):
    """Look up a template by its label (case-insensitive).

    Returns the NameTemplate, or None if not found.
    """
    return _TEMPLATE_LABELS.get(label.strip().lower())


def list_templates():
    """Return a list of (label, min_letters, max_letters) tuples for all templates."""
    return [(t.label, t.total_min(), t.total_max()) for t in TEMPLATES]


def select_templates(n_letters, required_roles=None):
    """Select 3-5 templates that can accommodate the given letter count.

    Args:
        n_letters: total number of letters to distribute
        required_roles: optional set of SegmentRole values that the template
            must contain (e.g., {SegmentRole.FIRST} when --first is used)

    Returns:
        List of viable NameTemplate objects.
    """
    viable = []
    for t in TEMPLATES:
        if t.total_min() <= n_letters <= t.total_max():
            # Only allow hyphenated templates for longer inputs
            has_hyphen = any(s.role == SegmentRole.HYPHENATED_LAST for s in t.segments)
            if has_hyphen and n_letters < MIN_LETTERS_FOR_HYPHEN:
                continue
            # Filter by required roles if specified
            if required_roles:
                template_roles = {s.role for s in t.segments}
                if not required_roles.issubset(template_roles):
                    continue
            viable.append(t)

    if not viable:
        viable = [_generate_custom_template(n_letters)]

    random.shuffle(viable)
    return viable[:5]


def _generate_custom_template(n_letters):
    """Generate a fallback template for unusual letter counts."""
    if n_letters <= 3:
        # Very short: use an initial + short name
        return NameTemplate(
            "I. Last",
            [
                SegmentSpec(SegmentRole.INITIAL, 1, 1),
                SegmentSpec(SegmentRole.LAST, n_letters - 1, n_letters - 1),
            ],
        )
    elif n_letters <= 5:
        return NameTemplate(
            "First Last",
            [
                SegmentSpec(SegmentRole.FIRST, 2, n_letters - 2),
                SegmentSpec(SegmentRole.LAST, 2, n_letters - 2),
            ],
        )
    else:
        # Very long: split into 4 parts
        per = n_letters // 4
        rem = n_letters % 4
        return NameTemplate(
            "First M. Last-Last",
            [
                SegmentSpec(SegmentRole.FIRST, per, per + rem),
                SegmentSpec(SegmentRole.INITIAL, 1, 1),
                SegmentSpec(SegmentRole.LAST, per, per + 3),
                SegmentSpec(SegmentRole.HYPHENATED_LAST, per, per + 3),
            ],
        )


def relax_template(template, n_letters):
    """Create a copy of a template with widened segment bounds to fit n_letters.

    Used when the user explicitly requests a template that doesn't match
    the input letter count. Returns None if physically impossible.
    """
    n_initials = sum(1 for s in template.segments if s.role == SegmentRole.INITIAL)
    available = n_letters - n_initials
    n_non_initial = len(template.segments) - n_initials

    if n_non_initial == 0 or available < n_non_initial * 2:
        return None  # physically impossible (each non-initial needs at least 2)

    per_seg_max = available - (n_non_initial - 1) * 2
    new_specs = []
    for spec in template.segments:
        if spec.role == SegmentRole.INITIAL:
            new_specs.append(SegmentSpec(spec.role, 1, 1))
        else:
            new_specs.append(SegmentSpec(spec.role, 2, max(2, per_seg_max)))

    return NameTemplate(template.label, new_specs)


def format_name(parts, template):
    """Format raw segments into a display name.

    Args:
        parts: list of lowercase strings (one per segment)
        template: the NameTemplate that was used

    Returns:
        Formatted name string (e.g., "Bethel Wrislow").
    """
    formatted = []
    for segment, spec in zip(parts, template.segments, strict=False):
        capitalized = segment.capitalize()
        if spec.role == SegmentRole.INITIAL:
            formatted.append(capitalized[0] + ".")
        elif spec.role == SegmentRole.HYPHENATED_LAST:
            if formatted:
                formatted[-1] = formatted[-1] + "-" + capitalized
            else:
                formatted.append(capitalized)
        else:
            formatted.append(capitalized)

    return " ".join(formatted)


def maybe_add_apostrophe(parts, template, frozen_indices=None):
    """Rarely add a cosmetic apostrophe to qualifying surnames.

    Only applied to surnames starting with 'o' followed by a consonant,
    at a low probability. Does not change the letter content.

    Args:
        parts: list of lowercase segment strings
        template: the NameTemplate used
        frozen_indices: optional set of segment indices to skip (user-specified names)

    Returns:
        Modified list of segment strings (apostrophe inserted).
    """
    frozen = frozen_indices or set()
    result = list(parts)
    for i, (seg, spec) in enumerate(zip(result, template.segments, strict=False)):
        if i in frozen:
            continue
        if (
            spec.role in (SegmentRole.LAST, SegmentRole.HYPHENATED_LAST)
            and len(seg) >= 4
            and seg[0] == "o"
            and seg[1] not in "aeiouy"
            and random.random() < 0.05
        ):
            result[i] = seg[0] + "'" + seg[1:]
    return result
