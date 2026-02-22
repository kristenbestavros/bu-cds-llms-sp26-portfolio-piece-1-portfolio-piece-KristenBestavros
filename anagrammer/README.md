
# Anagrammer

A command-line tool that generates name-like anagrams from words and phrases. Given any input text, it rearranges **every letter** into fictional character names that sound plausible and pronounceable.

```
$ python anagrammer.py "Perfect Anagram"
  1. Frepater Macgan
  2. Pangefer Macart
  3. Ferpane Macgart
  4. Preena Macfgart
  5. Capat Man Ferger
  6. Prega Fert Macan
  7. Fer Panter Macga
  8. Preft Gana Macer
  9. Marana F. Pecterg
 10. Magent F. Caraper
```

Every output is a perfect anagram of the input -- all letters used exactly once, ignoring punctuation (hyphens and apostrophes).

## How It Works

The tool uses a hybrid algorithm combining:

- **Trigram Markov chain** trained on thousands of real names from cultures worldwide to guide letter selection toward name-like sequences
- **Phonotactic rules** enforcing pronounceability constraints (valid consonant clusters, vowel requirements, syllable structure)
- **Template-based formatting** that splits letters into structured name parts (first, middle, last, initials, hyphenated surnames)
- **Cross-boundary scoring** that evaluates how naturally adjacent name segments flow into each other, penalizing consonant pile-ups at segment boundaries
- **Hill-climbing refinement** that swaps letters between name segments to improve overall quality
- **Syllable-aware refinement** that swaps whole syllables between segments after character-level hill-climbing, finding improvements that single-letter swaps would miss
- **Dictionary filtering** that rejects name segments matching common English words (~8,000 words), so results look like plausible names rather than recognizable vocabulary
- **Configurable temperature** for controlling the diversity/quality tradeoff during generation

For each input, the tool selects several name templates appropriate for the letter count, generates hundreds of candidates per template, scores them on a composite metric (Markov likelihood, length balance, vowel ratio, starting-letter diversity, bigram overlap, and boundary flow), and returns the top results with diversity-aware selection.

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)

### Standard Library Modules

| Module | Purpose |
|--------|---------|
| `argparse` | CLI argument parsing |
| `collections` | `Counter` and `defaultdict` for letter/trigram frequency tracking |
| `dataclasses` | Structured template and segment definitions |
| `enum` | Segment role constants |
| `math` | Log-probability scoring |
| `pickle` | Caching trained Markov models to disk |
| `random` | Candidate generation and sampling |

### Dev Tools

| Tool | Purpose |
|------|---------|
| [Ruff](https://docs.astral.sh/ruff/) | Linting (`ruff check`) and formatting (`ruff format`) |
| [pytest](https://docs.pytest.org/) | Unit and integration tests |

## Usage

```
python anagrammer.py "phrase to anagram"
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n`, `--count` | 15 | Number of results to show |
| `-d`, `--dataset` | `both` | Training data: `both`, `male`, or `female` |
| `-t`, `--template` | auto | Use a specific name template (e.g., `"First Last"`) |
| `--first` | none | Lock in a specific first name |
| `--last` | none | Lock in a last name (`"Name"`, `"First-Second"`, or `"-Second"`) |
| `--temp` | none | Set a constant sampling temperature (overrides `--temp-min`/`--temp-max`) |
| `--temp-min` | 1.2 | Minimum sampling temperature (start of generation) |
| `--temp-max` | 2.0 | Maximum sampling temperature (end of generation) |
| `--allow-words` | off | Allow name segments that are recognizable English words |
| `--list-templates` | off | List all available templates and exit |
| `--seed` | random | Random seed for reproducible output |
| `--verbose` | off | Show scores, templates, and anagram verification |
| `--no-cache` | off | Force Markov model rebuild (ignore cached model) |

### Examples

Basic usage:

```
$ python anagrammer.py "Whistleblower"
  1. Whille Berstow
  2. Withel Bowlers
  3. Browes Thewill
  4. There Bowswill
  5. Whillow Ste Ber
  6. Will Bowset Her
  7. Wes Wille Borth
  8. Bell Res Withow
  9. Withes R. Bellow
 10. Heter B. Willows
```

Masculine-leaning names:

```
$ python anagrammer.py "A stitch in time saves nine" --dataset male
  1. Vistes Mani Chian-Tineste
  2. Testie Istens Man-Vichian
  3. Mentein Vastes Chiti-Sian
  4. Visti Mente Chani-Stesian
  5. Avis Tiste Mence Tinis-Han
  6. Can Mett Siestes Hian-Vini
  7. Vines Manie Chia Tins-Sett
  8. Tene Machi Stani Vitis-Sen
  9. Viestes C. Manians-Hinetti
 10. Vistai S. Machinen-Tiesten
```

Feminine-leaning names:

```
$ python anagrammer.py "A stitch in time saves nine" --dataset female
  1. Mette Ista Vichen-Siannis
  2. Saniste Chia Metti-Vinsen
  3. Vine Testess Machian-Tini
  4. Channes Viette Stis-Miani
  5. Mina Vie Stine Schett-Sian
  6. Cha Mani Sentie Vittis-Sen
  7. Sita Ivines Sine Chett-Man
  8. Te Chine Setti Vins-Masian
  9. Manne I. Tistevis-Chianets
 10. Vistie N. Mattine-Schaines
```

Fewer results with verbose scoring:

```
$ python anagrammer.py "Split Loyalty" -n 5 --verbose
Input: "Split Loyalty" (12 letters: ailllopsttyy)

  1. Listy Tapolly                  [score:    -6.2] [First Last] [OK]
  2. Sitally Polty                  [score:    -6.3] [First Last] [OK]
  3. Lis Ally Potty                 [score:    -8.7] [First Middle Last] [OK]
  4. Stity Al Polly                 [score:    -9.1] [First Middle Last] [OK]
  5. Ality P. Stolly                [score:   -16.2] [First M. Last] [OK]
```

Choosing a specific template:

```
$ python anagrammer.py "Burning the midnight oil" --template "First Middle Last" -n 5
  1. Delmith Bortin Ginghuni
  2. Thiting Bridel Moughinn
  3. Tionith Lingen Drighumb
  4. Ghiling Tonted Ribhmuni
  5. Linobud Heritt Minghing
```

Locking in a first name:

```
$ python anagrammer.py "pride goes before the fall" --first Rigel -n 5
  1. Rigel Deshoel Patoffe-Ber
  2. Rigel Desta Beoper-Hoffel
  3. Rigel Bola Des Pete-Hoffer
  4. Rigel Abere Ted Hoff-Poles
  5. Rigel P. Hatoffee-Derobles
```

Locking in a hyphenated last name:

```
$ python anagrammer.py "every cloud has a silver lining" --last "Verily-Songs" -n 5
  1. Chilin Aula Dever Verily-Songs
  2. Ludia Cher Velina Verily-Songs
  3. Lucilia Dever Han Verily-Songs
  4. Rudeva Cheli Lian Verily-Songs
  5. Ellia Avin Ducher Verily-Songs
```

Controlling temperature:

```
$ python anagrammer.py "Hello World" --temp 1.0 -n 5    # lower = more conservative
$ python anagrammer.py "Hello World" --temp 3.0 -n 5    # higher = more diverse/unusual
$ python anagrammer.py "Hello World" --temp-min 1.0 --temp-max 2.5 -n 5  # ramp up over attempts
```

Allowing English words in names:

```
$ python anagrammer.py "Hello World" --allow-words -n 5  # permits segments like "world", "hello"
```

Listing available templates:

```
$ python anagrammer.py --list-templates
Available templates:

  Mononym                         (3-10 letters)
  I. Last                         (3-6 letters)
  First Last                      (6-17 letters)
  First M. Last                   (7-16 letters)
  First Middle Last               (9-21 letters)
  First M. M. Last                (9-18 letters)
  First M. Last-Last              (10-24 letters)
  First M. M. Last-Last           (11-25 letters)
  First Middle Last-Last          (12-29 letters)
  First Middle Middle Last-Last   (15-35 letters)
```

Reproducible output:

```
$ python anagrammer.py "Hello World" --seed 42
$ python anagrammer.py "Hello World" --seed 42   # identical output
```

## Name Formats

The tool automatically selects name structures based on input length:

| Input Length | Formats Generated |
|---|---|
| 3-5 letters | Mononym, I. Last |
| 6 letters | Mononym, I. Last, First Last |
| 7-10 letters | Mononym, First Last, First M. Last, and others as length allows |
| 11-15 letters | First Last, First M. Last, First Middle Last, First M. M. Last |
| 16+ letters | All above plus hyphenated variants (e.g. First M. Last-Last) |

Multiple formats appear in each run for variety. Cosmetic punctuation (initials with `.`, hyphenated surnames, rare apostrophes like O'Brien) is applied for stylistic diversity.

## Scoring

Candidates are ranked by a composite score combining:

| Component | What it measures |
|-----------|-----------------|
| Markov log-likelihood | How name-like each segment sounds (per-character, normalized by length) |
| Length balance | Penalizes extreme length differences between segments |
| Vowel ratio | Penalizes deviation from ~40% vowels |
| Starting-letter diversity | Bonus for segments starting with different letters |
| Bigram repetition | Penalty for repeated letter pairs across segments |
| Cross-boundary flow | How naturally adjacent segments transition (Markov-scored, with consonant pile-up penalties) |

Final result selection uses diversity-aware greedy picking to avoid returning too many similar names.

## Generation Pipeline

1. **Template selection** -- choose name structures viable for the input length
2. **Markov-guided construction** -- build each segment character-by-character, filtered by phonotactic lookahead
3. **Letter distribution** -- insert any remaining letters into segments at score-optimal positions
4. **Character-level refinement** -- hill-climbing: swap individual letters between segments to improve Markov scores
5. **Syllable-level refinement** -- swap whole syllables between segments for larger structural improvements
6. **Scoring and ranking** -- composite scoring with diversity-aware selection

## Training Data

Three datasets are available, all sourced from [Kate Monk's Onomastikon](https://tekeli.li/onomastikon/):

| Dataset | Contents | Description |
|---------|----------|-------------|
| **`both`** (default) | ~47,500 male + ~39,400 female first names + ~18,900 surnames | All names, no gender bias |
| **`male`** | ~47,500 male first names + ~18,900 surnames | Masculine-leaning patterns |
| **`female`** | ~39,400 female first names + ~18,900 surnames | Feminine-leaning patterns |

The Markov model is cached after first training for faster subsequent runs. Use `--no-cache` to force a rebuild.

## Data Sources

Name data is sourced from [Kate Monk's Onomastikon](https://tekeli.li/onomastikon/) (© 1997 Kate Monk), a comprehensive reference of names from cultures worldwide including Celtic, European, African, Asian, Middle Eastern, and Pacific traditions.

The English word filter list (`data/english_words.txt`, ~8,000 words) is used to reject name segments that look like common vocabulary rather than names. This can be bypassed with `--allow-words`.

The scraping script `build_name_data.py` is included in the repo for reproducibility. It uses only the Python standard library and includes rate-limiting to be polite to the server.

## Project Structure

```
anagrammer/
    anagrammer.py         CLI entry point
    main.py               Convenience entry point (calls anagrammer.main)
    build_name_data.py    Scraping script for name data (tekeli.li)
    src/
        __init__.py
        generator.py      Orchestrator: template selection, scoring, ranking
        solver.py         Core algorithm: Markov-guided construction + refinement
        markov.py         Trigram Markov chain: training, scoring, guidance
        phonotactics.py   Phonotactic constraints: onset/coda clusters, vowel rules, syllabification
        templates.py      Name templates: structure definitions, formatting
        letterbag.py      Letter multiset utility
        util.py           Shared helpers
    data/
        male_first.txt      Male first names (~47,500)
        female_first.txt    Female first names (~39,400)
        surnames.txt        Surnames (~18,900)
        english_words.txt   English word filter list (~8,000)
        .cache/             Cached trained models (auto-generated)
```