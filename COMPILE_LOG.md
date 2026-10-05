# Build and verification log

This log records the checks for the current release package. It does not
contain upstream recordings or research-process notes.

## Release metadata

- Repository: https://github.com/rtb-1005/FairEDA
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.23167890
- Current archived release DOI: https://doi.org/10.5281/zenodo.23168617
- Manuscript build: 10 A4 pages

## Manuscript build

Command sequence:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Result: successful compilation, 10 A4 pages. The final LaTeX pass had no
undefined references, undefined citations, or multiply-defined labels. The
only remaining diagnostic is a font-size substitution warning from the TeX
distribution.

## Environment

- Python: 3.12.14
- numpy: 2.3.5
- pandas: 2.2.3
- scipy: 1.16.3
- matplotlib: 3.10.6
- pillow: 12.0.0
- TeX: TeX Live 2026 / BibTeX 0.99e

## Statistical checks

`python src/analysis/null_evidence_tests.py`:

- maximum BF01: 2.88; no model has BF01 > 3
- largest equivalence bound: +/-2.37 percentage points
- all five models pass TOST at the +/-3.32 percentage-point oracle bound
- oracle-repair benefit: +3.32 percentage points

`python src/analysis/participant_confound.py`:

- pooled difference: +11.25 percentage points, 95% CI [+1.52, +17.31]
- within-participant difference: +0.07 percentage points, 95% CI [-3.97, +4.10]
- 984 windows from 11 participants

## Figure checks

`python figures/source/nature_data_figures.py` generated eight data figures from
the frozen inputs. The built-in layout checks reported zero text outside the
page and zero text collisions for every figure. The plotting inputs were not
modified by the generator.

## Package scans

- absolute-path matches: 0
- credential-pattern matches: 0
- original EDABE or VR recording files: not included
- system metadata files: not included

The package contains the manuscript source and PDF, nine manuscript figure
PDFs, two editable PowerPoint schematics, analysis scripts, frozen derived
inputs, plotting sources, and the licenses and citation metadata needed for a
public release. The package does not include deleted historical versions or
upstream recordings.
