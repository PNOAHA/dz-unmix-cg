# Detrital-Zircon Provenance Unmixing with Supervised NMF — Code Repository

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20371892.svg)](https://doi.org/10.5281/zenodo.20371892) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)

This repository contains the analysis, figure-generation, and manuscript-build scripts that underlie the paper:

> **Detrital-Zircon Provenance Unmixing with Supervised NMF: A Forward Modelling Framework Validated on Cretaceous Basins of Northeast Asia**
>
> Lujia Pan (潘路加). School of Mathematical Sciences, Hebei Normal University, Shijiazhuang, China.
> Submitted to *Computers & Geosciences* (Elsevier), 2026.

The companion code archive (this repository, with intermediate result files and rendered figures) is mirrored on Zenodo:

> Pan, L. (2026). *Detrital-zircon provenance unmixing with supervised NMF — supplementary code and data.* Zenodo. https://doi.org/10.5281/zenodo.20371892

(DOI is currently Reserved in Draft state and will be formally published upon manuscript acceptance; the Reserved DOI is the stable identifier cited in the manuscript.)

## What is in here

```
.
├── README.md                         this file
├── LICENSE                           MIT
├── requirements.txt                  Python dependencies (numpy, scipy, scikit-learn, matplotlib, pytest)
├── package.json                      Node dependency for the docx manuscript build
├── .gitignore                        Python + Node + Office artifacts excluded
│
├── Python pipeline (flat root layout — run from this directory)
│   ├── qn2025106_cli.py              entry point: python qn2025106_cli.py all
│   ├── dz_unmixing_experiment.py     core algorithm (supervised + unsupervised NMF)
│   ├── sensitivity_scan.py           75-config sensitivity scan harness
│   ├── case_study_demo.py            4-basin K1 case-study driver
│   ├── fig_paper_cg_figures_en.py    English Fig 5 / 6 / 7 (KDE, heatmap, alpha-effect)
│   ├── fig1_NEAsia_basemap.py        Fig 1 NE-Asia tectonic basemap
│   ├── fig2_framework.py             Fig 2 three-layer architecture
│   ├── fig3_forward_model.py         Fig 3 forward operator schematic
│   ├── fig4_workflow.py              Fig 4 inversion pipeline
│   ├── render_equations_cg.py        6 LaTeX equations → PNG (Computer Modern via mathtext)
│   ├── check_citations.py            in-text vs reference-list bidirectional audit
│   ├── polish_audit.py               vague-discourse + Tier-4 polish audit
│   └── consistency_check.py          terminology / abbreviation consistency
│
├── Manuscript build (Node)
│   └── build_cg_manuscript.js        single command builds the .docx for EM submission
│
├── data/ (intermediate results)
│   ├── sensitivity_results.csv       75-config scan, all metrics
│   ├── sensitivity_results.json
│   ├── sensitivity_summary.md
│   ├── dz_unmixing_results.json      5-fold CV results (unsup vs sup NMF)
│   ├── case_study_results.json       4-basin K1 case study (true vs predicted weights)
│   └── case_study_data/              4 basin sample CSVs (literature-calibrated synthetic)
│
├── figures/ (rendered figures + 6 equation PNGs)
│   ├── Fig1_NEAsia_basemap.{png,pdf,svg,eps}     tectonic basemap (Section 6.1)
│   ├── Fig2_framework.{png,pdf,svg,eps}          three-layer architecture (Section 3.4)
│   ├── Fig3_forward_model.{png,pdf,svg,eps}      forward operator schematic (Section 3.2)
│   ├── Fig4_workflow.{png,pdf,svg,eps}           inversion pipeline (Section 4.4)
│   ├── Fig5_sources_en.{png,svg}                 source endmember KDEs (Section 6.1)
│   ├── Fig6_sensitivity_en.{png,svg}             alpha x bandwidth heatmap (Section 5.3)
│   ├── Fig7_alpha_effect_en.{png,svg}            Dirichlet alpha effect (Section 5.3)
│   └── Eq_1.png ... Eq_6.png                     6 displayed equations (LaTeX-rendered)
│
└── tests/
    └── test_dz_unmixing.py           pytest unit tests
```

Data CSV/JSON files sit alongside the Python scripts at the repository root (matching the convention used by the analysis pipeline). Figure outputs are written to `figures/`.

## Quick-start reproduction (~3 minutes)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the full analysis pipeline (experiment -> sensitivity -> case study -> figures)
python qn2025106_cli.py all

# (Optional) Build the .docx manuscript
npm install               # one-time, fetches docx@^8
node build_cg_manuscript.js
```

The pipeline reproduces every number, table, and figure reported in the manuscript.

## Key results (from the paper)

| Result | Number | Section |
|---|---|---|
| Top-1 dominant-source accuracy (supervised) | **0.9897 ± 0.004** | §4 Table 1 |
| Top-1 dominant-source accuracy (unsupervised baseline) | 0.9495 ± 0.018 | §4 Table 1 |
| Weight MAE (supervised) | 0.0202 ± 0.001 | §4 Table 1 |
| 75-configuration sensitivity envelope (5 seeds × 3 α × 5 bandwidths) | **[0.977, 0.996]** | §5 Table 2 |
| 4-basin case-study weight MAE | **0.032** | §6 Table 3 |
| Dominant-source recovery | **3 of 4** samples | §6 Table 3 |
| Recommended default | α = 1.0, bandwidth = 12 Ma | §5.4 |

## Citing this work

If you use the code, data, or figures from this repository, please cite both the paper and the dataset:

```bibtex
@article{pan2026detrital,
  author  = {Pan, Lujia},
  title   = {Detrital-Zircon Provenance Unmixing with Supervised NMF:
             A Forward Modelling Framework Validated on Cretaceous Basins
             of Northeast Asia},
  journal = {Computers \& Geosciences},
  year    = {2026},
  note    = {Manuscript submitted}
}

@dataset{pan2026detrital_data,
  author    = {Pan, Lujia},
  title     = {Detrital-zircon provenance unmixing with supervised NMF
               --- supplementary code and data},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20371892}
}
```

## Funding

This research was supported by the Hebei Provincial Department of Education Research Project (Grant No. QN2025106, 2024–2027).

## License

MIT License — see [LICENSE](LICENSE) for full text. Free for academic and commercial use with attribution.

## Contact

Lujia Pan (潘路加)
- Institutional: peter205834@hebtu.edu.cn
- Personal: panlujia234@gmail.com
- ORCID: [0009-0004-2103-0193](https://orcid.org/0009-0004-2103-0193)
- Affiliation: School of Mathematical Sciences, Hebei Normal University, Shijiazhuang, China
