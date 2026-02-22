"""Core anagram-to-name generation algorithm.

Implements hybrid greedy construction with Markov guidance:
1. Build segments character-by-character using Markov probabilities
2. Distribute any remaining letters into segments
3. Refine via hill-climbing (swap letters between segments)
"""

import math
import random

from .phonotactics import is_valid_segment, phonotactic_filter, syllabify


def weighted_sample(candidates, temperature=1.2):
    """Sample a character from candidates using temperature-scaled probabilities.

    Args:
        candidates: list of (char, log_prob)
        temperature: >1 increases diversity, <1 increases greediness

    Returns:
        Selected character string.
    """
    if not candidates:
        return None

    # Apply temperature to log-probs and convert to probabilities
    max_lp = max(lp for _, lp in candidates)
    weights = []
    for _char, lp in candidates:
        # Shift by max for numerical stability, apply temperature
        w = math.exp((lp - max_lp) / temperature)
        weights.append(w)

    total = sum(weights)
    r = random.random() * total
    cumulative = 0.0
    for i, (char, _) in enumerate(candidates):
        cumulative += weights[i]
        if cumulative >= r:
            return char

    return candidates[-1][0]


def build_segment(
    available_bag, min_len, max_len, model, max_sub_attempts=50, temperature=1.2
):
    """Build one name segment character-by-character using Markov guidance.

    Args:
        available_bag: LetterBag of letters we can use
        min_len: minimum segment length
        max_len: maximum segment length
        model: trained MarkovModel
        max_sub_attempts: retries for this segment
        temperature: sampling temperature (higher = more diverse)

    Returns:
        A valid segment string, or None if all attempts failed.
    """
    for _ in range(max_sub_attempts):
        segment = ""
        bag = available_bag.copy()
        context = model.START
        target_len = random.randint(min_len, max_len)

        # Don't try to build a segment longer than available letters
        target_len = min(target_len, bag.total())
        if target_len < min_len:
            return None

        success = True
        for pos in range(target_len):
            candidates = model.get_likely_next(context[-2:], bag)
            candidates = phonotactic_filter(candidates, segment, pos, target_len)

            if not candidates:
                success = False
                break

            char = weighted_sample(candidates, temperature)
            if char is None:
                success = False
                break

            segment += char
            bag.subtract(char)
            context += char

        if success and len(segment) >= min_len and is_valid_segment(segment):
            return segment

    return None


def distribute_remaining(segments, remaining_bag, specs, models, frozen_indices=None):
    """Try to insert remaining letters into existing segments.

    Args:
        segments: list of segment strings (modified in place)
        remaining_bag: LetterBag of unused letters
        specs: list of SegmentSpec objects
        models: list of trained MarkovModel (one per segment)
        frozen_indices: optional set of segment indices to skip (user-specified)

    Returns:
        True if all remaining letters were distributed, False otherwise.
    """
    frozen = frozen_indices or set()
    for char in list(remaining_bag.as_sorted_string()):
        best_delta = -float("inf")
        best_insertion = None

        for seg_idx, segment in enumerate(segments):
            if seg_idx in frozen:
                continue
            spec = specs[seg_idx]
            if len(segment) >= spec.max_len:
                continue
            # Skip initials
            if spec.max_len == 1:
                continue

            for pos in range(len(segment) + 1):
                new_segment = segment[:pos] + char + segment[pos:]
                if is_valid_segment(new_segment):
                    old_score = models[seg_idx].score_segment(segment)
                    new_score = models[seg_idx].score_segment(new_segment)
                    delta = new_score - old_score
                    if delta > best_delta:
                        best_delta = delta
                        best_insertion = (seg_idx, new_segment)

        if best_insertion is None:
            return False

        seg_idx, new_segment = best_insertion
        segments[seg_idx] = new_segment

    return True


def generate_candidate(
    letter_bag, template, models, temperature=1.2, fixed_segments=None
):
    """Generate a single candidate name from a letter bag and template.

    Args:
        letter_bag: LetterBag with all input letters
        template: NameTemplate specifying segment structure
        models: list of trained MarkovModel (one per segment)
        temperature: sampling temperature (higher = more diverse)
        fixed_segments: optional dict mapping segment index to a fixed string

    Returns:
        List of segment strings, or None if generation failed.
    """
    fixed = fixed_segments or {}
    remaining = letter_bag.copy()
    specs = template.segments
    n_segments = len(specs)
    segments = [None] * n_segments

    # Pre-place fixed segments and subtract their letters
    for idx, seg_text in fixed.items():
        segments[idx] = seg_text
        remaining.subtract(seg_text)

    # Build order: only non-fixed segments, randomized for diversity
    order = [i for i in range(n_segments) if i not in fixed]
    random.shuffle(order)

    n_to_build = len(order)

    # Calculate how many letters we need to reserve for remaining segments
    for step, idx in enumerate(order):
        spec = specs[idx]

        # Calculate letters needed for segments not yet built
        letters_needed_later = 0
        for future_step in range(step + 1, n_to_build):
            future_idx = order[future_step]
            letters_needed_later += specs[future_idx].min_len

        available_now = remaining.total() - letters_needed_later

        # Adjust max_len to leave enough for later segments
        effective_max = min(spec.max_len, available_now)
        effective_min = spec.min_len

        if effective_max < effective_min:
            return None

        # For the last segment in build order, it must use exactly
        # the remaining letters (within its length constraints)
        if step == n_to_build - 1:
            needed = remaining.total()
            if needed < effective_min or needed > spec.max_len:
                return None
            effective_min = needed
            effective_max = needed

        segment = build_segment(
            remaining,
            effective_min,
            effective_max,
            models[idx],
            temperature=temperature,
        )
        if segment is None:
            return None

        segments[idx] = segment
        remaining.subtract(segment)

    # If letters remain (shouldn't happen with the last-segment logic above,
    # but handle edge cases), try to distribute them
    frozen = set(fixed.keys())
    if not remaining.is_empty() and not distribute_remaining(
        segments, remaining, specs, models, frozen_indices=frozen
    ):
        return None

    return segments


def _score_with_models(segments, models):
    """Score a complete name using per-segment models."""
    return sum(models[i].score_segment(seg) for i, seg in enumerate(segments))


def refine_candidate(segments, models, n_iterations=200, frozen_indices=None):
    """Hill-climbing refinement: swap letters between segments to improve score.

    Args:
        segments: list of segment strings
        models: list of trained MarkovModel (one per segment)
        n_iterations: number of swap attempts
        frozen_indices: optional set of segment indices to never modify

    Returns:
        Refined list of segment strings.
    """
    if len(segments) < 2:
        return segments

    best_score = _score_with_models(segments, models)
    best_segments = list(segments)
    current = list(segments)

    # Only consider segments longer than 1 (skip initials) and not frozen
    frozen = frozen_indices or set()
    swappable = [
        i for i in range(len(current)) if len(current[i]) > 1 and i not in frozen
    ]
    if len(swappable) < 2:
        return segments

    for _ in range(n_iterations):
        s1, s2 = random.sample(swappable, 2)
        if len(current[s1]) <= 1 or len(current[s2]) <= 1:
            continue

        p1 = random.randint(0, len(current[s1]) - 1)
        p2 = random.randint(0, len(current[s2]) - 1)

        # Swap characters
        c1 = current[s1][p1]
        c2 = current[s2][p2]
        if c1 == c2:
            continue

        new_s1 = current[s1][:p1] + c2 + current[s1][p1 + 1 :]
        new_s2 = current[s2][:p2] + c1 + current[s2][p2 + 1 :]

        if not is_valid_segment(new_s1) or not is_valid_segment(new_s2):
            continue

        trial = list(current)
        trial[s1] = new_s1
        trial[s2] = new_s2
        trial_score = _score_with_models(trial, models)

        if trial_score > best_score:
            best_score = trial_score
            best_segments = list(trial)
            current = list(trial)

    return best_segments


def refine_syllables(segments, models, n_iterations=200, frozen_indices=None):
    """Syllable-aware refinement: swap whole syllables between segments.

    After character-level hill-climbing, this pass tries swapping entire
    syllables between non-frozen segments to find improvements that
    single-character swaps would miss.

    Args:
        segments: list of segment strings
        models: list of trained MarkovModel (one per segment)
        n_iterations: number of swap attempts
        frozen_indices: optional set of segment indices to never modify

    Returns:
        Refined list of segment strings.
    """
    if len(segments) < 2:
        return segments

    frozen = frozen_indices or set()
    swappable = [
        i for i in range(len(segments)) if len(segments[i]) > 1 and i not in frozen
    ]
    if len(swappable) < 2:
        return segments

    best_score = _score_with_models(segments, models)
    best_segments = list(segments)
    current = list(segments)
    original_letters = sorted("".join(segments))

    for _ in range(n_iterations):
        s1, s2 = random.sample(swappable, 2)

        syls1 = syllabify(current[s1])
        syls2 = syllabify(current[s2])

        # Need at least 2 syllables in one segment to have something to swap
        if len(syls1) < 2 and len(syls2) < 2:
            continue

        # Pick a random syllable from each
        i1 = random.randint(0, len(syls1) - 1)
        i2 = random.randint(0, len(syls2) - 1)

        syl_a = syls1[i1]
        syl_b = syls2[i2]

        if syl_a == syl_b:
            continue

        # Build new segments by swapping syllables
        new_syls1 = list(syls1)
        new_syls2 = list(syls2)
        new_syls1[i1] = syl_b
        new_syls2[i2] = syl_a

        new_s1 = "".join(new_syls1)
        new_s2 = "".join(new_syls2)

        # Verify anagram invariant is preserved
        trial = list(current)
        trial[s1] = new_s1
        trial[s2] = new_s2
        if sorted("".join(trial)) != original_letters:
            continue

        # Validate phonotactics
        if not is_valid_segment(new_s1) or not is_valid_segment(new_s2):
            continue

        trial_score = _score_with_models(trial, models)
        if trial_score > best_score:
            best_score = trial_score
            best_segments = list(trial)
            current = list(trial)

    return best_segments


TEMP_MIN = 1.2
TEMP_MAX = 2.0


def solve(
    letter_bag,
    template,
    models,
    n_attempts=500,
    fixed_segments=None,
    temp_min=TEMP_MIN,
    temp_max=TEMP_MAX,
):
    """Generate multiple candidate names for a given template.

    Args:
        letter_bag: LetterBag with all input letters
        template: NameTemplate specifying structure
        models: list of trained MarkovModel (one per segment)
        n_attempts: number of generation attempts
        fixed_segments: optional dict mapping segment index to a fixed string
        temp_min: starting temperature for sampling (default: TEMP_MIN)
        temp_max: ending temperature for sampling (default: TEMP_MAX)

    Returns:
        List of (segments, score) tuples, sorted by score descending.
    """
    frozen = set(fixed_segments.keys()) if fixed_segments else set()
    results = []
    seen = set()

    for attempt_idx in range(n_attempts):
        # Escalate temperature to encourage diversity in later attempts
        progress = attempt_idx / max(n_attempts - 1, 1)
        temperature = temp_min + (temp_max - temp_min) * progress
        candidate = generate_candidate(
            letter_bag, template, models, temperature, fixed_segments
        )
        if candidate is None:
            continue

        refined = refine_candidate(candidate, models, frozen_indices=frozen)
        refined = refine_syllables(refined, models, frozen_indices=frozen)
        key = tuple(refined)
        if key in seen:
            continue
        seen.add(key)

        score = _score_with_models(refined, models)
        results.append((refined, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
