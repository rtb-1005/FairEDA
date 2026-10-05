# FairEDA

Code and frozen derived inputs for reproducing the tables and figures in:

> Artifact removal improves electrodermal waveforms but not downstream classification in a virtual-reality balance task.

The repository contains the manuscript source, final vector figures, editable schematic sources, analysis scripts, and the derived inputs required by those scripts. It does not redistribute the upstream EDABE or VR balance-disturbance datasets.

## Repository layout

| Path | Contents |
| --- | --- |
| `paper/` | LaTeX source, bibliography, compiled figures, and compiled manuscript |
| `src/analysis/` | Reproducible null-evidence and participant-confound analyses |
| `figures/source/` | Frozen-input plotting and schematic builders |
| `figures/editable/` | Editable PowerPoint schematics |
| `data/derived/` | Derived tables and frozen window-level inputs used by the scripts |
| `data/figure_inputs/` | Frozen plotting inputs |
| `build/figures/` | Rebuilt data-figure PDFs, vector sources, raster proofs, and QC manifest |
| `COMPILE_LOG.md` | Build, numerical-check, figure-QC, and package-scan results |

## Manuscript mapping

| Manuscript object | Reproducible source |
| --- | --- |
| Tables 1-4 and the reported null-evidence checks | `src/analysis/null_evidence_tests.py`, `data/derived/null_evidence_tests_recomputed.csv` |
| Participant-confound analysis and Figure 9 | `src/analysis/participant_confound.py`, `data/derived/participant_confound_recomputed.json`, `build/figures/fig16_confound.pdf` |
| Figures 1-2 (schematics) | `figures/editable/fig01_design.pptx`, `figures/editable/fig02_architecture.pptx` |
| Figures 3-6 and 7-9 (manuscript figure PDFs) | `paper/figures/` |
| Rebuilt data figures and their frozen inputs | `figures/source/nature_data_figures.py`, `data/figure_inputs/`, `build/figures/` |

## Requirements

Python 3.12 or newer and a LaTeX installation with `pdflatex` and `bibtex` are recommended. Install the Python dependencies with:

```sh
python -m pip install -r requirements.txt
```

## Reproduce the reported checks

From the repository root:

```sh
python src/analysis/null_evidence_tests.py
python src/analysis/participant_confound.py
```

The scripts write their recomputed summaries under `data/derived/`. They operate on frozen derived inputs and do not train models or redistribute upstream recordings.

## Rebuild data figures

```sh
python figures/source/nature_data_figures.py --output build/figures
```

The generated PDFs are deterministic displays of the frozen inputs. The two schematics are native editable PowerPoint files in `figures/editable/`; their builder requires the bundled presentation runtime or a compatible Node.js installation.

## Build the manuscript

```sh
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Data access

The upstream datasets must be obtained from their original repositories under their stated licences:

- EDABE v2, Mendeley Data: https://doi.org/10.17632/w8fxrg4pv5.2
- VR balance-disturbance corpus, Zenodo: https://doi.org/10.5281/zenodo.14013468

No original dataset files are included here. The included files are derived or frozen analysis inputs prepared for the manuscript figures and checks.

## Reproducibility boundary

**Directly reproducible:** manuscript compilation, frozen-input figures, null-evidence checks, and participant-confound check.

**Requires upstream data and the training environment:** training or refitting the residual gate and regenerating upstream predictions.

**Not included:** trained model weights, full upstream recordings, and per-window prediction arrays that are not needed by the included frozen-input checks.

## Citation

Please cite the associated manuscript and this repository. The archived release has DOI [10.5281/zenodo.23167891](https://doi.org/10.5281/zenodo.23167891).
