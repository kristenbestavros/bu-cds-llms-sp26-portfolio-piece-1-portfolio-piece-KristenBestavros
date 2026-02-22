# Project Overview

Portfolio piece for CDS 593 (Theory and Applications of LLMs). This project analyzes and extends an anagram name generator built on a trigram Markov model, connecting it to NLP concepts covered in the course (n-gram language models, sampling/decoding strategies, embeddings, the seq2seq bottleneck problem).

The portfolio piece includes the anagrammer tool itself (with improvements made for this assignment) and a Jupyter notebook analyzing its behavior, limitations, and connections to course material.

## Repository Structure

```
portfolio-piece/
├── CLAUDE.md              (this file)
├── README.md              (project overview for readers/graders)
├── requirements.txt       (Python dependencies for analysis)
├── anagrammer/            (the tool — copied from anagrammer repo)
│   ├── anagrammer.py      (CLI entry point)
│   ├── src/               (core modules: generator, solver, markov, etc.)
│   ├── data/              (training data + cached models)
│   └── tests/
├── notebooks/
│   └── analysis.ipynb     (main analysis notebook)
└── outputs/               (figures, saved results, tables)
```

## Commands

- Run anagrammer: `cd anagrammer && python anagrammer.py "test phrase"`
- Run anagrammer tests: `cd anagrammer && pytest`
- Lint anagrammer: `cd anagrammer && ruff check . --fix && ruff format .`
- Run notebook: `jupyter notebook notebooks/analysis.ipynb`

## Key Dependencies

The anagrammer itself uses only the Python standard library. The analysis notebook uses:
- gensim (Word2Vec / GloVe embeddings)
- matplotlib + seaborn (visualization)
- scikit-learn (dimensionality reduction, clustering)
- numpy + pandas (data manipulation)

All analysis dependencies go in requirements.txt in the project root.

## Workflow

1. Read this file and README.md before starting any task.
2. Do not modify files in anagrammer/ unless explicitly asked — treat it as a dependency. Anagrammer improvements happen in the anagrammer repo, not here.
3. The notebook should import from the anagrammer package. If imports need sys.path adjustments, put them in the first cell of the notebook and document why.
4. All generated figures should be saved to outputs/ with descriptive filenames (e.g., `temperature_diversity.png`, `embedding_clusters.png`).
5. When creating visualizations, use a consistent style: seaborn's default theme, clear axis labels, descriptive titles. Figures should be interpretable without reading surrounding text.
6. Run the notebook top-to-bottom before finishing to ensure reproducibility. Use random seeds wherever randomness is involved.

## Notebook Guidelines

The analysis notebook should read as a narrative, not a code dump. Each section should have:
- A markdown cell explaining *what* we're investigating and *why*
- Code cells that are concise and well-commented
- A markdown cell interpreting the results and connecting to course concepts

Sections of the notebook (planned):
1. **Introduction**: What is the anagrammer? What course concepts does it connect to?
2. **Ablation study**: Impact of each improvement (cross-boundary scoring, dictionary filtering, temperature, syllable swaps if implemented). Show before/after comparisons.
3. **Temperature and diversity**: How does temperature affect output diversity vs. quality? Visualize the tradeoff.
4. **Dataset comparison**: Do the male/female/both models produce measurably different outputs? What does this tell us about the training data?
5. **Embedding analysis**: Where do generated names land relative to real names in embedding space? (Exploratory — results may or may not be informative.)
6. **Limitations and future work**: What the model can't do, connections to attention/seq2seq bottleneck, cultural/ethical considerations around name generation.

## Constraints

- The anagram invariant is sacred: every output must use exactly the input letters. Any analysis that generates names should verify this.
- Figures and tables are the primary evidence. Claims in markdown cells should be supported by visible results.
- Leave the bulk of the discussion sections for me to write -- your primary job is to write the code and outline the notebook.
