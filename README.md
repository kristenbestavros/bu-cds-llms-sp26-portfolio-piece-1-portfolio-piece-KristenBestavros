# Anagram Name Generator: An N-gram Language Model Analysis

A portfolio piece for CDS 593 (Theory and Applications of LLMs) at Boston University.

## Overview

This project analyzes a character-level trigram Markov anagram name generator — a CLI tool that rearranges any input phrase into fictional character names using every letter exactly once. The analysis connects the tool's design choices to core LLM concepts: n-gram language models, temperature-based sampling, decoding strategies, and the limitations of fixed-context models. The notebook investigates how each design decision affects output quality and diversity, and situates the tool's architecture relative to modern sequence modeling. Each section in the analysis notebook has a written explanation of methods and interpretation of results; the notebook is meant to be read as a narrative. This is an improvement on and reflection of my week 1 lab.

The dedicated github repository for the anagrammer can be found [here.](https://github.com/kristenbestavros/anagrammer)

Example usage:

```
$ python anagrammer/anagrammer.py "Perfect Anagram"
  1. Frepater Macgan
  2. Pangefer Macart
  3. Ferpane Macgart
  4. Preena Macfgart
  5. Capat Man Ferger
```

## How the Tool Works

The anagrammer uses a hybrid pipeline:

- **Trigram Markov model** trained on ~106,000 real names (Kate Monk's Onomastikon) guides character-by-character generation
- **Phonotactic constraints** enforce pronounceability (valid consonant clusters, vowel requirements, syllable structure)
- **Template-based formatting** selects name structures appropriate for the input length (e.g., `First Last`, `First M. Last`, `First Middle Last-Last`)
- **Hill-climbing refinement** swaps individual letters between name segments to improve composite score
- **Syllable-level refinement** swaps whole syllables for structural improvements that character swaps would miss
- **Dictionary filtering** rejects segments matching common English words, keeping outputs name-like
- **Configurable temperature** controls the quality/diversity tradeoff during sampling

## What the Analysis Covers

The notebook (`notebooks/analysis.ipynb`) is organized as a narrative progressing from mechanism to behavior to limitations:

1. **Ablation study** — Isolates the contribution of each feature (character refinement, cross-boundary scoring, dictionary filtering) via before/after comparisons on composite score and output diversity
2. **Temperature and diversity** — Measures how sampling temperature trades generation quality for diversity; visualizes the tradeoff across a range of inputs
3. **Sampling strategies** — Compares unrestricted sampling against top-k and top-p; analyzes which strategies suit this constrained vocabulary setting
4. **Dataset comparison** — Tests whether models trained on male, female, or combined name data produce measurably different outputs; analyzes trigram frequency and ending-pattern distributions
5. **Input properties** — Examines whether input phrase characteristics (length, vowel ratio, entropy) predict output quality or diversity
6. **Embedding analysis** — Trains character n-gram embeddings and uses t-SNE to visualize where generated names land relative to real names

## Key Findings

- Composite score and perceptual quality diverge: adding features (refinement, cross-boundary scoring) reduces the numeric score but increases actual anagram quality
- Temperature scales quality and diversity as expected; outputs remain plausible even at high temperatures, suggesting the phonotactic constraints do most of the heavy lifting
- Top-k sampling outperforms top-p in this setting, consistent with the small, discrete character vocabulary (top-p mass concentrates too aggressively)
- Male and female training sets produce distinct phonotactic fingerprints: measurably different trigram distributions and name-ending patterns, reflecting real differences in the source data, though there a slight male bias exists in both the anagrammer and source data
- In character n-gram embedding space, generated names are indistinguishable from real names — no visible separation by source or gender — consistent with a model that has learned broad phonotactic patterns rather than name-specific features

## Repository Structure

```
portfolio-piece/
├── README.md                        (this file)
├── requirements.txt                 (analysis dependencies)
├── anagrammer/                      (the tool)
│   ├── anagrammer.py                (CLI entry point)
│   ├── src/                         (generator, solver, markov, phonotactics, ...)
│   ├── data/                        (name training data + cached models)
│   └── tests/                       (unit + integration tests)
├── notebooks/
│   └── analysis.ipynb               (main analysis notebook)
└── outputs/                         (generated figures)
```

## How to Run

### 1. Set up the environment

```bash
pip install -r requirements.txt
```

The anagrammer itself has no external dependencies (Python 3.8+ stdlib only). The analysis notebook requires the packages in `requirements.txt`.

### 2. Run the anagrammer (optional)

```bash
cd anagrammer
python anagrammer.py "your phrase here"
python anagrammer.py "your phrase here" --dataset female --temp 1.5 -n 10
python anagrammer.py --help        # full options
```

### 3. Run the analysis notebook

```bash
jupyter notebook notebooks/analysis.ipynb
```

The notebook already has all outputs saved, but you may rerun all cells top-to-bottom if you wish. Random seeds are set in the first code cell for reproducibility. Generated figures are saved to `outputs/`.

## Requirements

| Scope | Requirements |
|-------|-------------|
| Anagrammer | Python 3.8+, stdlib only |
| Analysis notebook | `gensim`, `matplotlib`, `seaborn`, `scikit-learn`, `numpy`, `pandas`, `jupyter` |

Install analysis dependencies with `pip install -r requirements.txt`.

## Data Sources

Name data is sourced from [Kate Monk's Onomastikon](https://tekeli.li/onomastikon/) (© 1997 Kate Monk), a comprehensive reference covering names from Celtic, European, African, Asian, Middle Eastern, and Pacific traditions. Three datasets are available:

| Dataset | Contents |
|---------|----------|
| `both` (default) | ~47,500 male + ~39,400 female first names + ~18,900 surnames |
| `male` | ~47,500 male first names + ~18,900 surnames |
| `female` | ~39,400 female first names + ~18,900 surnames |

The English word filter (`data/english_words.txt`, ~8,000 words) prevents name segments from matching common vocabulary. The scraping script (`build_name_data.py`) is included for reproducibility.
