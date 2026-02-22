"""Phonotactic constraint validation for name segments.

Enforces hard rules about what letter sequences are pronounceable,
based on English phonotactic patterns. Used both for final validation
and for lookahead filtering during segment construction.
"""

from .util import CONSONANTS, VOWELS

# Valid word-initial consonant clusters (2-letter)
VALID_ONSETS_2 = frozenset(
    {
        "bl",
        "br",
        "ch",
        "cl",
        "cr",
        "dh",
        "dr",
        "dw",
        "fl",
        "fr",
        "gh",
        "gl",
        "gn",
        "gr",
        "gw",
        "kh",
        "kl",
        "kn",
        "kr",
        "kw",
        "ph",
        "pl",
        "pr",
        "ps",
        "qu",
        "rh",
        "sc",
        "sh",
        "sk",
        "sl",
        "sm",
        "sn",
        "sp",
        "st",
        "sv",
        "sw",
        "th",
        "tr",
        "ts",
        "tw",
        "vl",
        "vr",
        "wh",
        "wr",
        "zh",
    }
)

# Valid word-initial consonant clusters (3-letter)
VALID_ONSETS_3 = frozenset(
    {
        "chr",
        "phr",
        "sch",
        "scr",
        "shr",
        "sph",
        "spl",
        "spr",
        "squ",
        "str",
        "thr",
    }
)

# Valid word-final consonant clusters (2-letter)
VALID_CODAS_2 = frozenset(
    {
        "ch",
        "ck",
        "ct",
        "dg",
        "ds",
        "ff",
        "ft",
        "gh",
        "gs",
        "ks",
        "lb",
        "lc",
        "ld",
        "lf",
        "lk",
        "ll",
        "lm",
        "ln",
        "lp",
        "ls",
        "lt",
        "lv",
        "lz",
        "mb",
        "mn",
        "mp",
        "ms",
        "mt",
        "nc",
        "nd",
        "ng",
        "nk",
        "nn",
        "ns",
        "nt",
        "nx",
        "nz",
        "ph",
        "ps",
        "pt",
        "rb",
        "rc",
        "rd",
        "rf",
        "rg",
        "rk",
        "rl",
        "rm",
        "rn",
        "rp",
        "rs",
        "rt",
        "rv",
        "rz",
        "sh",
        "sk",
        "sm",
        "sp",
        "ss",
        "st",
        "th",
        "ts",
        "tt",
        "tz",
        "wl",
        "wn",
        "ws",
        "xt",
        "xn",
    }
)

# Valid word-final consonant clusters (3-letter)
VALID_CODAS_3 = frozenset(
    {
        "cts",
        "fts",
        "lch",
        "lds",
        "lfs",
        "lks",
        "lls",
        "lms",
        "lps",
        "lts",
        "mbs",
        "mps",
        "nce",
        "nch",
        "ncs",
        "nds",
        "ngs",
        "nks",
        "nse",
        "nth",
        "nts",
        "nze",
        "rbs",
        "rch",
        "rds",
        "rfs",
        "rks",
        "rls",
        "rms",
        "rns",
        "rps",
        "rse",
        "rst",
        "rth",
        "rts",
        "sks",
        "sts",
        "tch",
        "ths",
    }
)

# Common vowel digraphs that are acceptable (2 consecutive vowels)
VALID_VOWEL_PAIRS = frozenset(
    {
        "ae",
        "ai",
        "ao",
        "au",
        "ay",
        "ea",
        "ee",
        "ei",
        "eo",
        "eu",
        "ey",
        "ia",
        "ie",
        "io",
        "iu",
        "oa",
        "oe",
        "oi",
        "oo",
        "ou",
        "oy",
        "ua",
        "ue",
        "ui",
        "uo",
        "uy",
        "ya",
        "ye",
        "yi",
        "yo",
        "yu",
    }
)


def get_onset(segment):
    """Extract the initial consonant cluster (before first vowel)."""
    onset = []
    for c in segment:
        if c in VOWELS:
            break
        onset.append(c)
    return "".join(onset)


def get_coda(segment):
    """Extract the final consonant cluster (after last vowel)."""
    coda = []
    for c in reversed(segment):
        if c in VOWELS:
            break
        coda.insert(0, c)
    return "".join(coda)


def is_valid_onset(cluster):
    """Check if a consonant cluster is a valid word-initial onset."""
    if len(cluster) <= 1:
        return True
    if len(cluster) == 2:
        return cluster in VALID_ONSETS_2
    if len(cluster) == 3:
        return cluster in VALID_ONSETS_3
    return False


def is_valid_coda(cluster):
    """Check if a consonant cluster is a valid word-final coda."""
    if len(cluster) <= 1:
        return True
    if len(cluster) == 2:
        return cluster in VALID_CODAS_2
    if len(cluster) == 3:
        return cluster in VALID_CODAS_3
    return False


def _count_trailing(s, char_set):
    """Count how many trailing characters belong to char_set."""
    count = 0
    for c in reversed(s):
        if c in char_set:
            count += 1
        else:
            break
    return count


def _has_excessive_consonant_run(segment, max_run=3):
    """Check if any run of consecutive consonants exceeds max_run."""
    run = 0
    for c in segment:
        if c in CONSONANTS:
            run += 1
            if run > max_run:
                return True
        else:
            run = 0
    return False


def _has_excessive_vowel_run(segment, max_run=2):
    """Check if any run of consecutive vowels exceeds max_run,
    excluding valid vowel pairs."""
    run = 0
    for i, c in enumerate(segment):
        if c in VOWELS:
            run += 1
            if run > max_run:
                return True
            # Check if a pair is valid
            if run == 2:
                pair = segment[i - 1 : i + 1]
                if pair not in VALID_VOWEL_PAIRS:
                    return True
        else:
            run = 0
    return False


def _could_be_valid_onset_prefix(cluster):
    """Check if this consonant cluster could be the start of a valid onset.
    Used for lookahead during construction."""
    if len(cluster) <= 1:
        return True
    if len(cluster) == 2:
        return cluster in VALID_ONSETS_2 or any(
            o.startswith(cluster) for o in VALID_ONSETS_3
        )
    if len(cluster) == 3:
        return cluster in VALID_ONSETS_3
    return False


def _could_be_valid_coda_prefix(cluster):
    """Check if this consonant cluster could be the start of a valid coda.
    Used for lookahead near segment end."""
    if len(cluster) <= 1:
        return True
    if len(cluster) == 2:
        return cluster in VALID_CODAS_2 or any(
            o.startswith(cluster) for o in VALID_CODAS_3
        )
    if len(cluster) == 3:
        return cluster in VALID_CODAS_3
    return False


def is_valid_segment(segment):
    """Check whether a segment passes all phonotactic hard constraints."""
    if len(segment) == 0:
        return False

    # Single-letter segments are valid (used as initials)
    if len(segment) == 1:
        return segment.isalpha()

    # Must contain at least one vowel
    if not any(c in VOWELS for c in segment):
        return False

    # Valid onset cluster
    onset = get_onset(segment)
    if len(onset) > 1 and not is_valid_onset(onset):
        return False

    # Valid coda cluster
    coda = get_coda(segment)
    if len(coda) > 1 and not is_valid_coda(coda):
        return False

    # No excessive consonant runs (>3 consecutive)
    if _has_excessive_consonant_run(segment, max_run=3):
        return False

    # No excessive vowel runs (>2 consecutive, with pair validation)
    return not _has_excessive_vowel_run(segment, max_run=2)


def syllabify(segment):
    """Split a name segment into syllables using onset-maximization.

    Each syllable has an optional onset (consonants), a required nucleus
    (vowel or valid vowel pair), and an optional coda (consonants).
    When consonants appear between two nuclei, as many as possible are
    assigned to the onset of the following syllable (provided they form
    a valid onset cluster).

    Args:
        segment: lowercase alphabetic string

    Returns:
        List of syllable strings, or [segment] if syllabification fails.
    """
    if len(segment) <= 1:
        return [segment]

    # Identify nucleus positions (vowels / valid vowel pairs)
    nuclei = []  # list of (start_index, end_index_exclusive)
    i = 0
    while i < len(segment):
        if segment[i] in VOWELS:
            start = i
            # Extend through valid vowel pairs
            while (
                i + 1 < len(segment)
                and segment[i + 1] in VOWELS
                and segment[i : i + 2] in VALID_VOWEL_PAIRS
            ):
                i += 1
            nuclei.append((start, i + 1))
            i += 1
        else:
            i += 1

    if not nuclei:
        return [segment]

    # Build syllables by assigning consonants around nuclei
    syllables = []
    for ni, (nuc_start, nuc_end) in enumerate(nuclei):
        if ni == 0:
            # First nucleus: everything before it is the onset
            onset = segment[:nuc_start]
        else:
            # Consonants between previous nucleus end and this nucleus start
            prev_end = nuclei[ni - 1][1]
            consonant_cluster = segment[prev_end:nuc_start]

            # Onset-maximization: give as many consonants as possible to
            # this syllable's onset (must form a valid onset)
            split = 0  # how many go to the previous syllable's coda
            for k in range(len(consonant_cluster) + 1):
                candidate_onset = consonant_cluster[k:]
                if len(candidate_onset) == 0 or is_valid_onset(candidate_onset):
                    split = k
                    break
            else:
                # No valid onset found; give all to coda of previous syllable
                split = len(consonant_cluster)

            coda = consonant_cluster[:split]
            onset = consonant_cluster[split:]

            # Append coda to previous syllable
            if syllables:
                syllables[-1] += coda

        nucleus = segment[nuc_start:nuc_end]
        syllables.append(onset + nucleus)

    # Append any trailing consonants as coda of the last syllable
    if nuclei:
        trailing = segment[nuclei[-1][1] :]
        if syllables:
            syllables[-1] += trailing

    # Handle leading consonants with no following vowel (shouldn't happen
    # since we checked for nuclei, but be safe)
    if not syllables:
        return [segment]

    return syllables


def phonotactic_filter(candidates, partial_segment, position, target_len):
    """Filter candidate next-characters to avoid phonotactic dead ends.

    Args:
        candidates: list of (char, log_prob) tuples
        partial_segment: the segment built so far (string)
        position: current position index (0-based)
        target_len: intended total length of the segment

    Returns:
        Filtered list of (char, log_prob) tuples.
    """
    result = []
    for char, prob in candidates:
        test = partial_segment + char
        remaining_positions = target_len - position - 1

        # Don't exceed 3 consecutive consonants
        if char in CONSONANTS and _count_trailing(test, CONSONANTS) > 3:
            continue

        # Don't exceed 2 consecutive vowels (check pair validity)
        if char in VOWELS:
            trailing_vowels = _count_trailing(test, VOWELS)
            if trailing_vowels > 2:
                continue
            if trailing_vowels == 2:
                pair = test[-2:]
                if pair not in VALID_VOWEL_PAIRS:
                    continue

        # At start: building cluster must be a valid onset prefix
        if position == 0 or (len(test) <= 3 and all(c in CONSONANTS for c in test)):
            onset_so_far = get_onset(test)
            if len(onset_so_far) > 1 and not _could_be_valid_onset_prefix(onset_so_far):
                continue

        # Near the end: trailing consonants must be a valid coda prefix
        if remaining_positions <= 2 and char in CONSONANTS:
            trailing = get_coda(test)
            if len(trailing) > 1 and not _could_be_valid_coda_prefix(trailing):
                continue

        # Must have at least one vowel by the end (except single-letter initials)
        if (
            remaining_positions == 0
            and len(test) > 1
            and not any(c in VOWELS for c in test)
        ):
            continue

        result.append((char, prob))

    return result
