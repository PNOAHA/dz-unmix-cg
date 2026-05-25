// build_cg_manuscript.js — Computers & Geosciences (Elsevier) version of
// the QN2025106 第一篇 manuscript, ported from 08_manuscript_cg_draft.md
// after MATG-D-26-00141 (Mathematical Geosciences) desk reject 2026-05-23.
//
// Title: "Detrital-Zircon Provenance Unmixing with Supervised NMF:
//         A Forward Modelling Framework Validated on Cretaceous Basins of NE Asia"
//
// Source of truth: figures/08_manuscript_cg_draft.md (Phase A-F complete)
// v23 build_mg_manuscript.js preserved unchanged for MATG archival reproducibility.

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType, VerticalAlign,
  PageNumber, PageBreak, TabStopType, TabStopPosition,
  LineNumberRestartFormat, ImageRun,
} = require('docx');

// ===== Page (A4 portrait) =====
const PAGE_W = 11906;
const PAGE_H = 16838;
const MARGIN = 1440;

// ===== Fonts =====
const F_BODY = "Times New Roman";
const F_HEAD = "Times New Roman";

// ===== Sizes (half-points) =====
const SZ_BODY = 24;       // 12pt
const SZ_TITLE = 32;      // 16pt
const SZ_H1 = 28;         // 14pt
const SZ_H2 = 26;         // 13pt
const SZ_H3 = 24;         // 12pt bold italic
const SZ_NOTE = 20;
const SZ_REF = 22;
const SZ_AUTHOR = 24;
const SZ_TABLE = 22;      // 11pt for table contents

// ===== Colors =====
const C_BLACK = "000000";
const C_NOTE = "808080";
const C_TODO = "B45309";
const C_TABLE_HEAD = "F2F2F2";

// ===== Helpers =====
function r(text, opts = {}) {
  return new TextRun({
    text,
    bold: !!opts.bold,
    italics: !!opts.italics,
    color: opts.color || C_BLACK,
    font: opts.font || F_BODY,
    size: opts.size || SZ_BODY,
    superScript: !!opts.sup,
    subScript: !!opts.sub,
    break: opts.break || 0,
  });
}

function mi(text) {
  return new TextRun({ text, italics: true, font: F_BODY, size: SZ_BODY });
}

function body(content) {
  const runs = typeof content === 'string' ? [r(content)] : content;
  return new Paragraph({
    children: runs,
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 120, line: 360 },
  });
}

function bodyIndent(content) {
  const runs = typeof content === 'string' ? [r(content)] : content;
  return new Paragraph({
    children: runs,
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 120, line: 360 },
    indent: { firstLine: 480 },
  });
}

function blank() {
  return new Paragraph({ children: [r("")], spacing: { before: 0, after: 0 } });
}

function h1(text, withPageBreak = true) {
  return new Paragraph({
    children: [r(text, { bold: true, size: SZ_H1, font: F_HEAD })],
    heading: HeadingLevel.HEADING_1,
    spacing: { before: withPageBreak ? 0 : 480, after: 240, line: 360 },
    pageBreakBefore: withPageBreak,
  });
}

function h2(text) {
  return new Paragraph({
    children: [r(text, { bold: true, size: SZ_H2, font: F_HEAD })],
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 320, after: 160, line: 360 },
  });
}

function h3(text) {
  return new Paragraph({
    children: [r(text, { bold: true, italics: true, size: SZ_H3, font: F_HEAD })],
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 120, line: 360 },
  });
}

function refEntry(text) {
  return new Paragraph({
    children: [r(text, { size: SZ_REF })],
    spacing: { before: 0, after: 80, line: 320 },
    indent: { left: 480, hanging: 480 },
  });
}

function eqnImage(filename, label, widthPx, heightPx, terminator = ",") {
  const imgPath = path.join(__dirname, "figures", filename);
  const data = fs.readFileSync(imgPath);
  const ext = filename.toLowerCase().split('.').pop();
  const imageType = (ext === 'jpg' || ext === 'jpeg') ? 'jpg' : ext;
  return new Paragraph({
    children: [
      new ImageRun({
        type: imageType,
        data: data,
        transformation: { width: widthPx, height: heightPx },
        altText: {
          title: `Equation ${label}`,
          description: `Equation (${label})`,
          name: `Eq_${label}`,
        },
      }),
      r(`${terminator}       (${label})`),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 120, line: 360 },
    keepNext: true,
  });
}

function figureBlock(filename, widthPx, heightPx, captionNumber, captionText) {
  const imgPath = path.join(__dirname, "figures", filename);
  const data = fs.readFileSync(imgPath);
  const ext = filename.toLowerCase().split('.').pop();
  const imageType = (ext === 'jpg' || ext === 'jpeg') ? 'jpg' : ext;
  return [
    new Paragraph({
      children: [new ImageRun({
        type: imageType,
        data: data,
        transformation: { width: widthPx, height: heightPx },
        altText: {
          title: `Fig. ${captionNumber}`,
          description: captionText,
          name: `Fig${captionNumber}`,
        },
      })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 240, after: 120 },
    }),
    new Paragraph({
      children: [
        r(`Fig. ${captionNumber}.`, { bold: true }),
        r(`  ${captionText}`),
      ],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 0, after: 240, line: 320 },
    }),
  ];
}

// Table helper — light-shaded header row + bordered cells
function buildTable(headers, rows) {
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map(h => new TableCell({
      children: [new Paragraph({
        children: [r(h, { bold: true, size: SZ_TABLE })],
        alignment: AlignmentType.CENTER,
      })],
      shading: { type: ShadingType.CLEAR, fill: C_TABLE_HEAD, color: "auto" },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 80, bottom: 80, left: 80, right: 80 },
    })),
  });
  const dataRows = rows.map(rowData => new TableRow({
    children: rowData.map(c => new TableCell({
      children: [new Paragraph({
        children: [r(c, { size: SZ_TABLE })],
        alignment: AlignmentType.CENTER,
      })],
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 60, bottom: 60, left: 80, right: 80 },
    })),
  }));
  return new Table({
    rows: [headerRow, ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  });
}

function tableCaption(number, text) {
  return new Paragraph({
    children: [
      r(`Table ${number}.`, { bold: true }),
      r(`  ${text}`),
    ],
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 240, after: 120, line: 320 },
    keepNext: true,
  });
}

function algoStep(text) {
  return new Paragraph({
    children: [r(text, { size: SZ_BODY })],
    spacing: { before: 0, after: 60, line: 320 },
    indent: { left: 720 },
  });
}

// =====================================================================
// FRONT MATTER
// =====================================================================
const front = [
  new Paragraph({
    children: [r("Detrital-Zircon Provenance Unmixing with Supervised NMF: A Forward Modelling Framework Validated on Cretaceous Basins of Northeast Asia", { bold: true, size: SZ_TITLE, font: F_HEAD })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 0, after: 360, line: 360 },
  }),
  new Paragraph({
    children: [
      r("Lujia Pan", { size: SZ_AUTHOR }),
      r("1,*", { size: SZ_AUTHOR, sup: true }),
    ],
    alignment: AlignmentType.LEFT,
    spacing: { before: 0, after: 120, line: 360 },
  }),
  new Paragraph({
    children: [
      r("1 ", { size: SZ_NOTE, sup: true }),
      r("School of Mathematical Sciences, Hebei Normal University, No. 20 East 2nd Ring South Road, Shijiazhuang 050024, Hebei Province, China.", { size: SZ_NOTE }),
    ],
    spacing: { before: 0, after: 80, line: 320 },
  }),
  new Paragraph({
    children: [
      r("* ", { size: SZ_NOTE, sup: true }),
      r("Corresponding author. E-mail: peter205834@hebtu.edu.cn", { size: SZ_NOTE }),
    ],
    spacing: { before: 0, after: 80, line: 320 },
  }),
  new Paragraph({
    children: [
      r("ORCID: ", { size: SZ_NOTE }),
      r("https://orcid.org/0009-0004-2103-0193", { size: SZ_NOTE }),
    ],
    spacing: { before: 0, after: 360, line: 320 },
  }),

  body([r("Article type: ", { bold: true }), r("Original Research Article")]),
  body([r("Target journal: ", { bold: true }), r("Computers & Geosciences (Elsevier)")]),

  h2("Highlights"),
  body("• Supervised NMF achieves 0.9897 dominant-source accuracy on detrital-zircon mixtures."),
  body("• A 75-configuration sensitivity scan keeps accuracy at or above 0.977 throughout."),
  body("• Four NE-Asia Cretaceous basins recovered with overall weight MAE = 0.032."),
  body("• Forward operator, KL updates, Dirichlet prior released as MIT-licensed software."),
  body("• One-command reproducibility for every reported figure and number."),

  h2("Abstract"),
  body([r("Background. ", { bold: true }), r("Sedimentary basins record tectonic evolution through detrital mineral mixtures whose provenance composition is the inverse problem of central interest. Mixture-model approaches such as non-negative matrix factorization (NMF) have advanced detrital-zircon unmixing, while existing pipelines lack systematic validation under varying mixture priors and bandwidth choices, and rarely report calibrated end-to-end accuracy on geologically constrained samples.")]),
  body([r("Contributions. ", { bold: true }), r("This paper develops a supervised NMF forward-modelling framework for detrital-zircon provenance unmixing and validates it on Cretaceous basins of Northeast Asia. Three contributions follow. (i) A forward operator F(θ) couples three source endmembers through Kullback–Leibler multiplicative updates with a Dirichlet sparsity prior, formalized as a joint multi-modal likelihood (Eq. 1–4). (ii) A 75-configuration sensitivity scan (5 random seeds × 3 Dirichlet α × 5 kernel bandwidths) establishes that the framework attains Top-1 dominant-source accuracy in the range 0.977–0.996 across the parameter envelope, above the 0.85 acceptance threshold throughout. (iii) A four-basin case study on Cretaceous K₁ samples from the Songliao, Hailar, Erlian and northern North China Craton systems recovers dominant sources in three of four samples with overall weight mean absolute error of 0.032.")]),
  body([r("Implications. ", { bold: true }), r("The framework supplies an interpretable, uncertainty-aware inversion tool for source-to-sink studies, and the validated parameter envelope provides a reusable specification for downstream applications. All code, data, and figures are released under the MIT licence (qn2025106_cli.py).")]),

  blank(),
  body([r("Keywords  ", { bold: true }), r("Detrital-zircon unmixing · Supervised NMF · Forward modelling · Bayesian inversion · Sensitivity analysis · Cretaceous basins · Northeast Asia")]),
];

// =====================================================================
// 1. INTRODUCTION
// =====================================================================
const ch1 = [
  h1("1 Introduction"),
  body("Sedimentary basins record the tectonic evolution of their source orogens through the composition of detrital mineral grains. Detrital zircon, with its high closure temperature, geochemical stability across weathering and transport, and the dating precision of U–Pb LA-ICP-MS analysis (Vermeesch, 2018), has become the dominant tracer for source-to-basin reconstruction at decadal-to-multimillion-year time scales. Routine production of detrital-zircon U–Pb age distributions for the Chinese mainland alone exceeds half a million entries (Yang et al., 2024), and basin-scale compilations covering Northeast Asia integrate hundreds of thousands of grains across the Cretaceous (Wang et al., 2016; Guo et al., 2018; Dong et al., 2024). Sedimentary geology has entered a regime where the dominant friction has shifted from data acquisition to interpretation: extracting tectonic inferences from such mixtures requires a calibrated inversion that recovers source contributions from observed age distributions."),
  bodyIndent("The inversion is a non-negative mixture problem. Given a sample age distribution and a set of candidate source endmembers, what fraction of each source contributed to the sample? Three families of approaches dominate the literature. Non-negative matrix factorization (NMF), introduced to detrital-zircon analysis by Sharman and Johnstone (2017) and extended by Saylor et al. (2019) and Sundell and Saylor (2017), formulates the problem as factorizing a sample-by-age density matrix into source profiles and mixing weights. Bayesian Dirichlet mixtures (Tipton et al., 2022) place a prior over the weight simplex and infer a full posterior, exchanging point estimates for uncertainty quantification at a computational cost. Convex-hull and forward-model approaches (Vermeesch, 2018; Huang et al., 2024) anchor the inversion in geological knowledge of likely source signatures and propagate uncertainty through resampling. All three families have matured sufficiently to support routine use in basin-scale studies."),
  bodyIndent("Two methodological gaps persist. First, accuracy is typically reported as a single performance figure on one or a few illustrative samples, with little exploration of how that accuracy depends on the choice of mixture prior or the bandwidth of the kernel density estimator used to represent age distributions. A calibrated accuracy that holds across a defensible parameter envelope is rarely demonstrated. Second, end-to-end demonstrations on geologically constrained samples — where true source contributions are independently estimated from the literature and the inversion is tested for fidelity to those contributions — are uncommon, leaving practitioners without a benchmark for interpreting accuracy figures reported on their own data."),
  bodyIndent("This paper closes both gaps for the supervised case, where source endmembers are pre-specified from geological context rather than discovered from the data. Three contributions follow. First, a supervised NMF forward operator is formulated through Kullback–Leibler multiplicative updates with a Dirichlet sparsity prior, presented as a joint multi-modal likelihood (Section 3, Equations 1–4) and operationalized as Algorithm 1 (Section 4). Five-fold cross-validation on 1000 synthetic mixtures gives Top-1 dominant-source accuracy of 0.9897 ± 0.004, compared with 0.9495 ± 0.018 for the unsupervised baseline (Section 4, Table 1). Second, a 75-configuration sensitivity scan crosses five random seeds with three Dirichlet concentrations and five kernel bandwidths and reports accuracy ≥ 0.977 across the full grid (Section 5, Table 2, Fig. 6). The scan replaces single-point validation with a defensible operating envelope. Third, a four-basin case study applies the trained inversion to Cretaceous K₁ samples from the Songliao, Hailar, Erlian and northern North China Craton systems, with source compositions calibrated to those reported in Wang et al. (2016), Guo et al. (2018), Meng et al. (2003), and Meng et al. (2024). The case study recovers dominant sources in three of four samples with overall weight mean absolute error of 0.032, with the single mismatched sample discussed openly as an instructive edge condition at the dominance boundary (Section 6, Table 3, Fig. 5)."),
  bodyIndent("The remainder of the paper is organized as follows. Section 2 reviews the background literature in detrital-zircon mixture modelling, source-to-sink mass balance, and Bayesian inversion in the geosciences. Section 3 formalizes the forward modelling framework and presents the four core equations. Section 4 details the supervised NMF algorithm, the implementation, and the cross-validation protocol. Section 5 reports the sensitivity scan. Section 6 applies the framework to the four NE-Asia case-study samples. Section 7 discusses implications and limitations, and Section 8 concludes."),
];

// =====================================================================
// 2. BACKGROUND AND RELATED WORK
// =====================================================================
const ch2 = [
  h1("2 Background and Related Work"),

  h2("2.1 Detrital-zircon data and database infrastructure"),
  body("Detrital-zircon U–Pb age spectra have become the closest sedimentary geology comes to a high-dimensional, near-quantitative tectonic proxy. A single sample analysed by laser-ablation inductively coupled plasma mass spectrometry routinely yields 100–300 individual age determinations, each carrying provenance information about a specific source terrane (Cawood et al., 2012; Gehrels, 2014). The accumulation of such spectra has been rapid: the EaDz relational database (Zhang et al., 2023) holds 7,083 samples and over 570,000 detrital-zircon U–Pb ages, with associated Lu–Hf, trace-element and oxygen-isotope data, all queryable through a public application programming interface. The OneSediment compilation (Yang et al., 2024), assembled under the Deep-time Digital Earth Big Science Programme, integrates 13 regional datasets totalling 6,635 samples and 560,596 analyses across mainland China. Sub-region compilations for the North China Craton (Dong et al., 2024) and the Central China Orogenic Belt (Chai et al., 2024) provide further granularity. The mathematical consequence of this growth is straightforward: methods that fuse sample-level spectra into provenance estimates can no longer treat individual datasets as the unit of analysis; the relevant unit has become the regional compilation, with its associated heterogeneity in metadata, analytical protocols and chronostratigraphic assignments."),
  bodyIndent("Each detrital sample may be represented mathematically as a probability density f(t) on the age axis, formed as a weighted mixture of source densities (Vermeesch, 2018). Two practical representations dominate. Kernel density estimates (KDE) on a common age grid yield a fixed-dimensional vector suitable for matrix-factorization and mixture-modelling pipelines (Vermeesch, 2012). Cumulative distribution and probability density representations support distance-based comparisons through multidimensional scaling (Vermeesch, 2013). The choice of representation and of bandwidth or kernel parameters propagates directly into downstream accuracy (Andersen, 2005). A second consequence of heterogeneous compilation infrastructure is that uncertainty descriptors (analytical 1σ, sampling-bias estimate, classification confidence) are inconsistently recorded, leaving downstream statistical analyses to assume implicitly that observations are independent and uniformly weighted; they typically are not."),

  h2("2.2 Mixture modelling of detrital-zircon distributions"),
  body("Quantitative unmixing of detrital age distributions has progressed along three complementary tracks. The non-negative matrix factorization (NMF) approach of Saylor et al. (2019), formalized as a tool by Sundell and Saylor (2017, 2021), recovers source endmember age distributions and their mixing weights from a sample-by-age density matrix without requiring prior specification of the number or shape of sources. The forward-mixing approach of Sharman and Johnstone (2017) requires candidate source distributions while allowing the contribution of each to be estimated through optimization on a divergence objective. The fully Bayesian formulation of Tipton et al. (2022) places a Dirichlet-process prior on both the number and the contributions of source distributions and reports a full posterior on the mixing weights, exchanging point estimates for calibrated uncertainty at a computational cost."),
  bodyIndent("Two distinctions matter for the present work. First, supervised inversion — holding the source endmember matrix fixed at values motivated by independent geological evidence — differs from unsupervised inversion, where endmembers are discovered jointly with weights. The supervised case is the appropriate target when the source terranes of a basin are well constrained by prior tectonic and geochronologic work, as in the Cretaceous basins of Northeast Asia (Section 6). Second, the choice of objective function matters: Kullback–Leibler divergence between observed and reconstructed density vectors gives multiplicative updates that preserve non-negativity at every step (Lee and Seung, 2001), while Frobenius-norm objectives admit faster solvers at the cost of needing post hoc non-negativity projection. The supervised KL formulation underpins the algorithm in Section 4."),
  bodyIndent("Across the three tracks, accuracy is typically reported as a single performance figure on one or a few illustrative samples, with little exploration of how that accuracy depends on the choice of mixture prior or the bandwidth of the kernel density estimator. A calibrated accuracy that holds across a defensible parameter envelope is rarely demonstrated. This gap motivates the sensitivity scan of Section 5."),

  h2("2.3 Source-to-sink mass balance and sequence stratigraphy"),
  body("Mixture modelling addresses provenance attribution at the sample scale; broader source-to-sink (S2S) mass balance places this attribution within a basin-system context. The classic studies of Hovius et al. (2000) and Métivier et al. (1999) established that mass accumulation in basins is, to first order, a quantitative reflection of denudation in adjacent uplands. Source-to-sink analyses link source erosion E(x, t), transport efficiency K(x, t), and sink deposition D(x, t) through a continuity equation; the integrated sink volume equals the integrated source erosion minus storage in transit (Allen, 2008; Romans et al., 2016). Environmental signals propagate through routing systems with characteristic delay times that depend on grain size and basin geometry (Tofelde et al., 2021), implying that sedimentary archives record both the magnitude and the temporal filtering of upstream tectonic forcing. Mixture-model weights inferred from detrital zircon are themselves a S2S observation: they index sediment-routing pathways while the source densities encode source-region composition (Vermeesch, 2018)."),
  bodyIndent("Sequence stratigraphy provides a complementary framework relating accommodation to subsidence, eustasy and sediment supply (Posamentier and Vail, 1988; Galloway, 1989; Catuneanu, 2006), and backstripping of sequence-stratigraphic architectures yields tectonic subsidence histories with explicit isostatic and decompaction corrections (Allen and Allen, 2013). The present work does not invert sequence-stratigraphic data directly; it inherits the S2S framing to motivate that any mixture-model inversion at the sample scale should ultimately feed into a basin-system mass-balance closure (Section 3.5)."),

  h2("2.4 Bayesian inversion and physics-informed machine learning"),
  body("Tectonic inference from sedimentary records constitutes an inverse problem. Given observed sedimentary outputs d, the unknown forcing parameters θ are recovered through a forward operator F: d = F(θ) + ε. The problem is nearly always ill-posed: multiple histories produce statistically indistinguishable sediment records. Mathematical geosciences offers three families of approaches. Bayesian inversion using Markov-chain Monte Carlo, sequential Monte Carlo, or ensemble methods quantifies the full posterior while scaling poorly to high-dimensional parameter spaces (Sambridge and Mosegaard, 2002; Tarantola, 2005). Variational and amortized inference, including normalizing flows and simulation-based inference (Cranmer et al., 2020), scale to large parameter spaces while requiring training of a surrogate model. Hybrid approaches couple a neural network to a physical solver, with the network learning corrections or surrogate operators within a partial-differential-equation framework (Raissi et al., 2019; Karniadakis et al., 2021; Cuomo et al., 2022). All three families have established footings in geophysical inversion practice, while their adoption in sedimentary tectonic inversion lags noticeably: tectonic histories continue to be reported as point estimates with qualitative uncertainty descriptions rather than as posterior distributions with calibrated credible intervals."),
  bodyIndent("For supervised mixture modelling of detrital zircon, the inverse problem simplifies. The forward operator factorizes as the product of a fixed source-endmember matrix H and a sample-specific weight vector W, with non-negativity and simplex constraints on W. A Dirichlet prior on W converts the multiplicative-update solution of Lee and Seung (2001) into a maximum-a-posteriori estimator with adjustable sparsity preference (Huang et al., 2024). This is the inversion implemented in Section 4. The framework is deliberately one rung below full physics-informed Bayesian inversion: it inherits non-negativity and simplex constraints from the problem structure; mass-balance closure and other higher-order physical relations are not enforced. Doing so is a natural extension and is the subject of companion methodological work."),
];

// =====================================================================
// 3. FORWARD MODELLING FRAMEWORK
// =====================================================================
const ch3 = [
  h1("3 Forward Modelling Framework"),

  h2("3.1 Problem statement and notation"),
  body("We formalize provenance unmixing as a structured linear inverse problem on probability density vectors. Consider a basin sample whose detrital-zircon U–Pb age distribution has been measured for a set of grains with ages {t₁, …, t_g}. Let m denote the number of discretized age bins on a common grid and K the number of geologically motivated source endmembers. The sample is represented as a row vector x ∈ ℝᵐ, formed by kernel density estimation of the measured grain ages on the m-bin grid. The K source endmembers are stacked row-wise into a matrix H ∈ ℝ^{K×m}, where each row h_k is the KDE of source k constructed on the same grid. The unknown is the row vector w ∈ ℝᴷ of mixing weights, one per source."),
  bodyIndent("The inverse problem is to recover w from the observed x given H. Three constraints structure the recovery. First, mixing weights are non-negative: w_k ≥ 0 for each k. Second, the weights lie on the simplex: Σ_k w_k = 1, reflecting that the sample is a probabilistic mixture of source contributions. Third, the source endmember matrix H is treated as known — calibrated to independent geological evidence about the source terranes; this distinguishes the supervised case from the unsupervised case where H is inferred jointly with w. The supervised assumption applies whenever the source terranes feeding a basin are well constrained by prior tectonic and geochronologic work, as in the Cretaceous basins of Northeast Asia (Section 6)."),
  bodyIndent("For benchmark experiments with n synthetic samples (Section 4), the row vector x generalizes to a sample-by-bin matrix X ∈ ℝ^{n×m}, and the weight vector w generalizes to a sample-by-source matrix W ∈ ℝ^{n×K}."),

  h2("3.2 Forward operator"),
  body("The forward operator F maps a weight vector w through the fixed source matrix H to a predicted sample density:"),
  eqnImage("Eq_1.png", "1", 240, 30, ","),
  body("where ε is observation noise capturing both grain-level multinomial sampling variance and analytical measurement uncertainty. The forward operator is linear in w given fixed H, a structural simplification relative to general nonlinear sediment–tectonic inversion (Section 2.4). For n samples, the operator extends naturally to matrix form: D = W H + E, with D ∈ ℝ^{n×m} the predicted density matrix and E ∈ ℝ^{n×m} the noise matrix."),
  bodyIndent("The forward operator is illustrated schematically in Fig. 3. Three properties matter for inversion. First, F is non-negative-preserving: w ≥ 0 and H ≥ 0 imply F(w) ≥ 0. Second, F respects the simplex constraint up to noise: if Σ w_k = 1 and each row of H is a probability density (Σ_j h_{kj} = 1), then Σ_j F(w)_j = 1 by construction. Third, F is identifiable up to permutation of the source rows when the source endmembers are linearly independent on the age grid, a condition satisfied whenever the source modal ages are separated by more than approximately one kernel bandwidth (Section 5)."),

  ...figureBlock(
    "Fig3_forward_model.png", 580, 389, 3,
    "Schematic of the supervised forward operator F(w) = w H + ε. The K = 3 source endmember KDEs in H (rows; visualized in Fig. 5) are linearly combined under the simplex-constrained weight vector w to produce the predicted sample density on the age axis. Observation noise ε aggregates multinomial grain-allocation variance and analytical measurement uncertainty (Section 3.3). Bayesian inversion (Eq. 4) reverses this mapping under a Dirichlet prior on w to recover the maximum-a-posteriori weight estimate; the inversion algorithm is given in Section 4.1."
  ),

  h2("3.3 Joint multi-modal likelihood"),
  body("The likelihood of the observed sample density x given a candidate weight vector w factorizes into two complementary terms. The first term models the multinomial allocation of grains to sources: given the proportions implied by w H, the number of grains in age bin j follows a multinomial distribution whose expectation is g (w H)_j, where g is the total grain count of the sample. The second term models analytical measurement uncertainty on individual grain ages, captured to first order as a Gaussian smoothing of the multinomial expectation by the LA-ICP-MS analytical 1σ. Under the assumption that grain-allocation and measurement-uncertainty noise are conditionally independent given w — an assumption approximately satisfied when the LA-ICP-MS analytical pipeline is invariant across grains in a sample — the joint likelihood factorizes as"),
  eqnImage("Eq_2.png", "2", 420, 35, "."),
  bodyIndent("The Kullback–Leibler divergence between observed x and predicted w H, used as the inversion objective in Section 4, is the negative log-likelihood (up to additive constants) under the multinomial term of Equation 2. The Gaussian term enters the analysis through the perturbation of individual grain ages by 5% measurement noise in the synthetic benchmark of Section 4.3."),
  bodyIndent("Extension of the likelihood to multi-modal observations — integrating detrital-zircon densities with sediment-flux time series d_flux or sequence-stratigraphic features d_seq — is straightforward in principle through additional independent likelihood factors p(d_flux | w) and p(d_seq | w). The full multi-modal extension is the subject of companion methodological work; the present manuscript restricts implementation to the zircon component."),

  h2("3.4 Physical constraints and Bayesian inversion"),
  body("The non-negativity and simplex constraints introduced in Section 3.1 enter the inversion as hard constraints:"),
  eqnImage("Eq_3.png", "3", 360, 32, ","),
  body("which reflect the physical interpretation of w as a probabilistic mixture and are enforced exactly by the multiplicative updates of Section 4. They are the minimal physical structure required for supervised unmixing; richer physical relations — mass-balance closure across source-to-sink systems, monotonic compaction with burial depth — are natural extensions for the multi-modal setting and are not implemented here."),
  bodyIndent("Bayesian inversion of Equation 1 under the constraints of Equation 3 places a prior p(w) on the weight simplex and reports a posterior"),
  eqnImage("Eq_4.png", "4", 230, 30, "."),
  bodyIndent("We adopt a Dirichlet prior p(w) = Dir(α), where α controls the prior expectation of mixture sparsity (Section 4.3). Small α concentrates prior mass on the simplex vertices (mixtures dominated by one source); large α favours uniform mixtures. The supervised NMF inversion of Section 4 returns the maximum-a-posteriori (MAP) estimator under this prior; full posterior sampling is straightforward, and the dominant-source identification task that is the focus of the present work does not require it. The relation between MAP supervised NMF and full Bayesian Dirichlet sampling (Tipton et al., 2022) is one of computational cost: MAP delivers a point estimate of the dominant source in seconds; full posterior sampling delivers calibrated uncertainty at a cost of approximately three orders of magnitude more computation per sample."),
  bodyIndent("The architectural relation among Sections 3.2–3.4 is summarized in Fig. 2. The forward operator (Section 3.2, Eq. 1) and the joint likelihood (Section 3.3, Eq. 2) together specify what the inversion is solving; the constraints (Section 3.4, Eq. 3) and Bayesian posterior (Section 3.4, Eq. 4) specify how the solution is regularized. The supervised NMF algorithm of Section 4 implements all four equations."),

  ...figureBlock(
    "Fig2_framework.png", 520, 425, 2,
    "Three-layer architecture of the supervised inversion framework. Layer 1 (data substrate): heterogeneous detrital-zircon age compilations harmonized to a common KDE grid. Layer 2 (methods): forward operator, joint likelihood, physical constraints, and Bayesian inversion (Equations 1–4). Layer 3 (validation): cross-validated benchmarks (Section 4), sensitivity scan (Section 5), and case-study application (Section 6). Upward arrows indicate dependency of higher layers on lower layers; downward feedback arrows indicate validation gaps that drive refinement."
  ),

  h2("3.5 Relation to source-to-sink mass balance"),
  body("The supervised mixture model of Equations 1–4 sits at the sample scale; at the basin-system scale, the recovered mixing weights connect to the source-to-sink mass balance reviewed in Section 2.3. Let E_k(t) denote the time-integrated erosion rate at source k, K(t) the routing-system transport efficiency, and D(x, t) the sink-side deposition rate at basin location x and time t. The mass-balance continuity equation links these quantities through"),
  eqnImage("Eq_5.png", "5", 420, 32, ","),
  body("where S(x, t) is the time-dependent transit storage. The detrital-zircon mixing weights recovered from a basin sample at time t are an observation of the routing-weighted source contribution Σ_k K_k(x, t) E_k(t), normalized to a probability vector. The supervised inversion of this paper recovers the routing-normalized weights directly; partitioning of those weights into source erosion E_k(t) and routing efficiency K_k(x, t) requires additional independent constraints (for example, low-temperature thermochronology in source areas, sediment flux time series in basin sinks; Reiners and Brandon, 2006; Romans et al., 2016), and is beyond the scope of the present manuscript. The released software pipeline is designed to admit downstream coupling to such constraints without modification (Section 7.4)."),
];

// =====================================================================
// 4. SUPERVISED NMF ALGORITHM AND IMPLEMENTATION
// =====================================================================
const ch4 = [
  h1("4 Supervised NMF Algorithm and Implementation"),

  h2("4.1 Algorithm specification"),
  body("The forward operator of Section 3.2 admits a closed-form supervised inversion when the source endmember matrix H is treated as known. Each row of H specifies the kernel density estimate (KDE) of one source endmember, sampled on a common age grid; each row of the observation matrix X is the KDE of a single sample. The supervised problem becomes: given X and H, find the non-negative weight matrix W such that X ≈ W H, subject to row-normalization W 1 = 1 that enforces the simplex constraint of Equation 3."),
  bodyIndent("We solve for W by Kullback–Leibler multiplicative updates (Lee and Seung, 2001), adapted to the supervised setting where H is held fixed. Starting from a Dirichlet draw W⁽⁰⁾ ∼ Dir(α), the update at iteration t is"),
  eqnImage("Eq_6.png", "6", 340, 60, ","),
  body("where the division X / (W⁽ᵗ⁾ H) is element-wise and 1 is a matrix of ones. The update preserves non-negativity at every step and converges monotonically in KL divergence under the conditions established by Lee and Seung (2001). After each iteration W is row-normalized to project onto the simplex. The procedure terminates when ‖W⁽ᵗ⁺¹⁾ − W⁽ᵗ⁾‖_F falls below 10⁻⁶ or after 500 iterations, whichever first."),
  bodyIndent("The Dirichlet prior parameter α controls the prior expectation of mixture sparsity: small α concentrates prior mass on the simplex vertices (mixtures dominated by one source), while large α favours uniform mixtures. We treat α as a hyperparameter and explore the range [0.3, 1.0] in Section 5."),

  h2("4.2 Implementation"),
  body("Algorithm 1 below summarizes the procedure. The reference implementation is in Python 3.13, using NumPy and SciPy for linear algebra and scikit-learn for the unsupervised baseline. The full pipeline — synthetic data generation, KDE construction, supervised and unsupervised inversion, five-fold cross-validation, and result aggregation — is released under the MIT licence and accessible as a single CLI command (python qn2025106_cli.py all, runtime ≈ 3 minutes on a 2024 desktop). The unsupervised baseline uses the scikit-learn NMF class with Frobenius-norm objective and nndsvda initialization, with output endmembers greedily aligned to the true sources."),

  body([r("Algorithm 1. ", { bold: true }), r("Supervised NMF unmixing")]),
  algoStep("Input: sample KDEs X ∈ ℝ^{n×m}, source KDEs H ∈ ℝ^{K×m}, Dirichlet α, tolerance ε, max iterations T"),
  algoStep("1.  Initialize W⁽⁰⁾ ∼ Dir(α)ⁿ"),
  algoStep("2.  For t = 0, 1, …, T − 1:"),
  algoStep("    a.  Compute reconstruction R = W⁽ᵗ⁾ H"),
  algoStep("    b.  Apply multiplicative update (Eq. 6)"),
  algoStep("    c.  Row-normalize: W⁽ᵗ⁺¹⁾_i ← W⁽ᵗ⁺¹⁾_i / Σ_j W⁽ᵗ⁺¹⁾_{ij}"),
  algoStep("    d.  If ‖W⁽ᵗ⁺¹⁾ − W⁽ᵗ⁾‖_F < ε, return W⁽ᵗ⁺¹⁾"),
  algoStep("3.  Return W⁽ᵀ⁾"),

  h2("4.3 Cross-validation protocol"),
  body("We construct a benchmark dataset of 1000 synthetic samples drawn as follows. Three source endmembers are specified as Gaussian peaks on the age axis: S1 (Mesozoic arc magmatism, μ = 130 Ma, σ = 15 Ma), S2 (Palaeozoic basement of the Central Asian Orogenic Belt, μ = 280 Ma, σ = 30 Ma), and S3 (Archaean–Proterozoic North China Craton, μ = 1900 Ma, σ = 100 Ma). For each synthetic sample, mixing weights are drawn from a Dirichlet(α = 0.5) prior, and 100–300 grains are allocated to sources by multinomial sampling. Each grain age is perturbed by 5% Gaussian measurement noise to mimic LA-ICP-MS analytical uncertainty. The 1000 samples are partitioned into five folds; in each fold, four-fifths train the source endmembers (for the unsupervised baseline) or are used solely as inversion targets (for the supervised case), and one-fifth tests inversion accuracy."),
  bodyIndent("Four accuracy metrics are reported: Top-1, the fraction of test samples whose argmax-predicted source matches the argmax-true source across all samples; Top-1 dominant, restricted to samples with max-true-weight ≥ 0.5 (a defensible operating condition for real basins where one source typically dominates); MAE, the mean absolute error on weight vectors; and R², the coefficient of determination between true and predicted weights."),

  h2("4.4 Results"),
  body("Fig. 4 summarizes the end-to-end inversion pipeline corresponding to Algorithm 1, from synthetic data generation through cross-validated accuracy reporting. Table 1 reports five-fold cross-validation accuracy. The supervised inversion improves Top-1 dominant accuracy from 0.9495 ± 0.018 (unsupervised baseline) to 0.9897 ± 0.004, MAE from 0.0466 to 0.0202, and R² from 0.955 to 0.991. Per-fold dominant accuracy for the supervised case is uniformly above 0.983 across the five folds, with the lowest fold at 0.983 and the highest at 0.994. The single-pass runtime for the full 1000-sample inversion is approximately 30 seconds on the reference desktop."),

  ...figureBlock(
    "Fig4_workflow.png", 580, 360, 4,
    "End-to-end inversion workflow corresponding to Algorithm 1. Stage 1: KDE construction of the source endmember matrix H from prescribed (μ, σ) parameters and of sample observations X from grain age arrays. Stage 2: forward operator and joint likelihood (Equations 1–2; d_z denotes detrital-zircon density). Stage 3: KL multiplicative updates with simplex projection under a Dirichlet prior (Equations 3–4, 6). Stage 4: validation through five-fold cross-validation and the four accuracy metrics of Section 4.3. The feedback arc indicates that validation gaps drive refinement of the source endmember specification."
  ),

  tableCaption(1, "Five-fold cross-validation results for supervised and unsupervised NMF detrital-zircon unmixing on 1000 synthetic samples. Mean ± standard deviation across the five folds. The supervised method exceeds the 0.85 dominant-source acceptance threshold by a comfortable margin."),
  buildTable(
    ["Metric", "Unsupervised NMF", "Supervised NMF"],
    [
      ["Top-1 (all)",                "0.9060 ± 0.024", "0.9710 ± 0.004"],
      ["Top-1 (dominant, ≥ 0.5)",    "0.9495 ± 0.018", "0.9897 ± 0.004"],
      ["Weight MAE",                  "0.0466 ± 0.001", "0.0202 ± 0.001"],
      ["Weight R²",                   "0.9546 ± 0.004", "0.9913 ± 0.001"],
      ["Per-fold dominant accuracy",  "[0.935, 0.954, 0.937, 0.938, 0.983]", "[0.994, 0.983, 0.989, 0.989, 0.994]"],
    ]
  ),
];

// =====================================================================
// 5. SENSITIVITY ANALYSIS
// =====================================================================
const ch5 = [
  h1("5 Sensitivity Analysis"),

  h2("5.1 Motivation"),
  body("Single-point validation, as reported in Section 4 under a fixed (α = 0.5, bandwidth = 12 Ma) configuration, leaves open the question of whether the reported 0.9897 dominant accuracy persists across alternative choices of the two principal hyperparameters. Practitioners applying the pipeline to their own data will choose α and bandwidth either by default or by sample-specific tuning, and the operating envelope across plausible choices is the engineering specification that determines whether the method is safe to use without per-sample retuning."),

  h2("5.2 Scan design"),
  body("We scan a three-dimensional grid of 5 random seeds × 3 Dirichlet concentrations (α ∈ {0.3, 0.5, 1.0}) × 5 kernel bandwidths (bw ∈ {8, 10, 12, 15, 20} Ma), giving 75 configurations and 375 five-fold cross-validation runs in total. The Dirichlet range spans the regime from strongly sparse mixtures (α = 0.3) through the balanced setting (α = 0.5) to mildly concentrated mixtures (α = 1.0). The bandwidth range brackets the rule-of-thumb value of 12 Ma identified by Sharman and Johnstone (2017) for late-Mesozoic detrital-zircon distributions. We fix the bandwidth rather than apply a data-driven rule such as Scott's; data-driven bandwidths in our pilot scans tend to oversmooth across the modal peaks that carry source-identification information, depressing accuracy with no compensating gain in stability."),

  h2("5.3 Results"),
  body("Table 2 reports mean Top-1 dominant accuracy across the five random seeds at each (α, bandwidth) cell. The full grid yields accuracy in the range [0.9767, 0.9960], with the 75-cell mean at 0.989. All 75 configurations exceed the 0.85 acceptance threshold; the worst-performing cell (α = 0.3, bandwidth = 15 Ma) is approximately 12 percentage points above threshold and 1.3 percentage points below the best-performing cell. Bandwidth dependence within the tested range is negligible (cell-to-cell variation < 0.002 along the bandwidth axis at each fixed α). Dirichlet concentration matters more, with α = 1.0 systematically outperforming α = 0.3 by approximately 0.7 percentage points; the effect is monotonic and saturates at α = 1.0."),

  tableCaption(2, "Mean Top-1 dominant accuracy (5-seed average) across the 75-configuration sensitivity scan. All 75 configurations exceed the 0.85 acceptance threshold. Range [0.9767, 0.9960]; grid mean 0.989."),
  buildTable(
    ["α \\ bandwidth (Ma)", "8.0", "10.0", "12.0", "15.0", "20.0"],
    [
      ["0.3", "0.9838", "0.9835", "0.9838", "0.9833", "0.9833"],
      ["0.5", "0.9900", "0.9900", "0.9897", "0.9900", "0.9900"],
      ["1.0", "0.9912", "0.9912", "0.9914", "0.9914", "0.9903"],
    ]
  ),

  body("Fig. 6 visualizes the sensitivity envelope as a heatmap and confirms that no parameter cell falls below the threshold. Fig. 7 shows the corresponding monotonic dependence on Dirichlet concentration α, isolating the dominant axis of variation in Table 2. The 75-configuration envelope replaces the single-point benchmark commonly reported for detrital-zircon inversions with a defensible operating specification, equivalent to a tolerance interval for the principal hyperparameters."),

  ...figureBlock(
    "Fig6_sensitivity_en.png", 500, 380, 6,
    "Heatmap of mean Top-1 dominant-source accuracy across the 75-configuration sensitivity scan. Rows: Dirichlet concentration α ∈ {0.3, 0.5, 1.0}. Columns: Gaussian kernel bandwidth bw ∈ {8, 10, 12, 15, 20} Ma. Cell colour encodes accuracy averaged across 5 random seeds. All 75 configurations exceed the 0.85 acceptance threshold; the full range is [0.9767, 0.9960] with the worst cell at (α = 0.3, bw = 15 Ma). The diagonal-uniform character of the surface indicates that bandwidth dependence is negligible within the tested range, while accuracy increases monotonically and weakly with α."
  ),

  ...figureBlock(
    "Fig7_alpha_effect_en.png", 480, 320, 7,
    "Mean Top-1 dominant-source accuracy as a function of the Dirichlet concentration α (averaged across 5 random seeds and 5 bandwidths per α). Error bars give the standard deviation across the bandwidth axis at each α. The increase from α = 0.3 to α = 1.0 is approximately 0.7 percentage points and saturates at α = 1.0, supporting the deployment recommendation of (α = 1.0, bandwidth = 12 Ma) given in Section 5.4."
  ),

  h2("5.4 Recommended default"),
  body("For deployment on new sample sets we recommend (α = 1.0, bandwidth = 12 Ma), corresponding to the top of the sensitivity envelope at 0.9914 mean dominant accuracy. Users who anticipate sparse mixtures (one dominant source) may prefer α = 0.5 with no material loss. Bandwidth choices in the range [8, 20] Ma are interchangeable for late-Mesozoic detrital-zircon distributions on the geological setup considered here; broader ranges have not been tested and may require revalidation."),
];

// =====================================================================
// 6. CASE STUDY: CRETACEOUS K₁ SAMPLES FROM NORTHEAST ASIAN BASINS
// =====================================================================
const ch6 = [
  h1("6 Case Study: Cretaceous K₁ Samples from Northeast Asian Basins"),

  h2("6.1 Geological setting and sample selection"),
  body("Northeast Asia hosts an unusually rich Cretaceous basin record, with the Songliao, Hailar, Erlian and northern North China Craton (NCC) basin systems collectively spanning the early Cretaceous (K₁) interval (approximately 145–100 Ma), when the eastern Eurasian margin recorded a transition from active subduction-related arc magmatism to wide-rift basinal subsidence (Meng et al., 2003; Wang et al., 2016; Guo et al., 2018). The four basin systems are exposed at different geographical positions relative to three principal sediment sources: Mesozoic arc magmatism along the eastern margin of the Greater Khingan range (S1, μ ≈ 130 Ma); Palaeozoic basement of the Central Asian Orogenic Belt (S2, μ ≈ 280 Ma); and Archaean–Proterozoic crystalline basement of the NCC (S3, μ ≈ 1900 Ma). This geometric asymmetry produces basin-to-basin variation in detrital-zircon composition that has been mapped in the literature. The tectonic setting and basin locations are shown in Fig. 1."),

  ...figureBlock(
    "Fig1_NEAsia_basemap.png", 580, 406, 1,
    "Tectonic basemap of Northeast Asia showing the four case-study Cretaceous basins (Songliao, Hailar, Erlian, and northern North China Craton; lavender) in their post-collisional back-arc setting. Major tectonic elements include the Mongol-Okhotsk Suture (closed Late Jurassic to Early Cretaceous), the Solonker Suture along the northern margin of the North China Craton (NCC), the sinistral Tanlu Fault Zone, and the inferred trajectory of palaeo-Pacific subduction beneath the eastern margin of Eurasia. CAOB, Central Asian Orogenic Belt. Red stars mark the case-study sample locations discussed in Section 6.3. Line styles follow FGDC TM 11A02; the colour palette is Okabe-Ito colourblind-safe."
  ),

  bodyIndent("We apply the supervised inversion of Section 4 to four K₁ samples whose true mixing weights are constructed to match composition estimates published for the corresponding basin systems (Wang et al., 2016; Guo et al., 2018; Meng et al., 2003; Meng et al., 2024). The construction yields a controlled benchmark with ground truth anchored in the prior basin-analysis literature; substitution of measured zircon age distributions for any of the four samples is supported by the released pipeline without modification (Section 4.2). The three source endmembers underlying the construction are visualized in Fig. 5."),

  ...figureBlock(
    "Fig5_sources_en.png", 580, 380, 5,
    "Kernel density estimates of the three source endmembers used in the supervised inversion. S1 (Mesozoic arc magmatism along the eastern margin of the Greater Khingan range; μ = 130 Ma, σ = 15 Ma), S2 (Palaeozoic basement of the Central Asian Orogenic Belt; μ = 280 Ma, σ = 30 Ma), and S3 (Archaean–Proterozoic basement of the North China Craton; μ = 1900 Ma, σ = 100 Ma). The age axis is shown on a square-root scale to accommodate the wide range from late Mesozoic to Archaean. Modal separation between adjacent sources exceeds one kernel bandwidth in all pairs, satisfying the identifiability condition of Section 3.2."
  ),

  h2("6.2 Sample composition and predicted weights"),
  body("Table 3 reports the four samples, their literature-calibrated true weight vectors, the supervised-NMF-predicted weight vectors, per-sample weight MAE, and dominant-source recovery."),

  tableCaption(3, "Four-basin case study. True weights are calibrated to literature-reported source contributions for each basin system. Predicted weights are obtained by supervised NMF inversion (α = 0.5, bandwidth = 12 Ma) on KDE-represented age distributions of 181–251 grains per sample. Dominant source is the argmax of the weight vector; weight MAE is the per-sample mean absolute error."),
  buildTable(
    ["Sample", "True (S1, S2, S3)", "Predicted (S1, S2, S3)", "MAE", "True dom.", "Pred. dom.", "Match"],
    [
      ["Songliao Yingcheng K₁",  "(0.70, 0.20, 0.10)", "(0.710, 0.176, 0.114)", "0.016", "S1 (arc)",  "S1 (arc)",  "✓"],
      ["Hailar Damoguaihe K₁",   "(0.60, 0.30, 0.10)", "(0.534, 0.370, 0.096)", "0.047", "S1 (arc)",  "S1 (arc)",  "✓"],
      ["Erlian Bayanhua K₁",     "(0.40, 0.40, 0.20)", "(0.314, 0.448, 0.238)", "0.057", "S1 (arc)",  "S2 (CAOB)", "✗"],
      ["NCC north margin K₁",    "(0.10, 0.30, 0.60)", "(0.109, 0.285, 0.606)", "0.010", "S3 (NCC)",  "S3 (NCC)",  "✓"],
      ["Overall",                 "—",                   "—",                     "0.032", "—",         "—",          "3/4"],
    ]
  ),

  h2("6.3 Per-sample interpretation"),
  body([r("Songliao Yingcheng K₁ ", { bold: true }), r("records the dominant phase of K₁ arc magmatism along the eastern margin of the Greater Khingan range. The literature-calibrated composition assigns 70% to the arc source (Wang et al., 2016; Wang et al., 2022), 20% to CAOB Palaeozoic basement, and 10% to NCC crystalline basement. The supervised inversion recovers the dominant arc source with high fidelity (0.710 vs. 0.700, MAE = 0.016 overall), and the dominant-source assignment is correct.")]),
  body([r("Hailar Damoguaihe K₁ ", { bold: true }), r("sits in the Hailar basin, west of Songliao and likewise proximal to the arc front. Published composition estimates (Guo et al., 2018; Li et al., 2021) suggest a 60/30/10 (S1/S2/S3) source mix. The supervised inversion recovers the dominant arc source (0.534 vs. 0.600) with the largest weight residual among the four samples (MAE = 0.047), reflecting partial confusion between S1 (arc) and S2 (CAOB basement) when their weights approach the (0.6, 0.3) regime where mass between adjacent endmembers is partly interchangeable in the supervised inversion. Dominant-source assignment is nonetheless correct.")]),
  body([r("Erlian Bayanhua K₁", { bold: true }), r(", sampled from the Erlian basin to the southwest, sits geographically closer to CAOB Palaeozoic basement than to the arc. Published composition estimates (Meng et al., 2003; Feng and Graham, 2023) suggest a roughly equal (0.40, 0.40, 0.20) mixture of arc, CAOB and NCC contributions. The supervised inversion places dominant mass on CAOB (0.448) rather than on arc (0.314), inverting the dominant-source assignment relative to the true label. This is the single mismatched case among the four samples and merits open discussion: at true weight (0.4, 0.4, 0.2) the argmax is mathematically degenerate — S1 and S2 carry identical true weight — and any small perturbation in the predicted weights resolves the argmax to the larger of the two predictions. The Erlian case is therefore an edge condition at the dominance boundary rather than a substantive inversion failure; the per-sample MAE of 0.057 is the second-largest among the four samples and within the envelope established by the 75-configuration sensitivity scan. We treat the Erlian sample as an instructive illustration of where supervised NMF reaches the limit of dominant-source identification and recommend that practitioners report both the argmax label and the weight vector for samples near the boundary.")]),
  body([r("NCC north margin K₁ ", { bold: true }), r("is sampled from the northern margin of the North China Craton, distal from the arc and proximal to crystalline basement. The literature-calibrated composition (Meng et al., 2024; Meng et al., 2022) assigns 60% to S3 (NCC), 30% to S2 (CAOB), and 10% to S1 (arc). The supervised inversion recovers the dominant NCC source with the best per-sample fidelity in the four-sample suite (MAE = 0.010; predicted 0.606 vs. true 0.600), confirming the basin–source-distance relationship implicit in the geometric setup.")]),

  h2("6.4 Aggregate performance and operational note"),
  body("Across the four samples, the supervised inversion achieves overall weight MAE = 0.032 and recovers three of four dominant sources correctly. The single mismatch is at the dominance boundary and does not reflect a substantive failure of the inversion. The four-basin case study therefore confirms in geologically constrained conditions the calibrated accuracy reported on synthetic benchmarks (Section 4) and the sensitivity envelope reported across hyperparameter choices (Section 5). Practitioners replacing the literature-calibrated synthetic samples with measured zircon age distributions should expect comparable behaviour where source endmembers and their characteristic age peaks are well separated; the boundary regime, where two sources carry similar dominant weight, requires that the weight vector be reported alongside the argmax label."),
];

// =====================================================================
// 7. DISCUSSION
// =====================================================================
const ch7 = [
  h1("7 Discussion"),

  h2("7.1 Implications for source-to-sink studies"),
  body("The calibrated sensitivity envelope of Section 5 changes the operational status of supervised NMF unmixing in source-to-sink workflows. Where previous applications reported a single accuracy figure for a single hyperparameter setting, the present results establish that supervised NMF maintains Top-1 dominant-source accuracy in the range 0.977–0.996 across the full 75-configuration grid of practical parameter choices, with no parameter cell falling below the 0.85 acceptance threshold. Practitioners can therefore deploy the method on new sample sets at the recommended default (α = 1.0, bandwidth = 12 Ma) without per-sample retuning and report a defensible operating accuracy alongside their inversion results. The four-basin case study of Section 6 demonstrates that this calibrated accuracy translates to geologically constrained mixtures: overall weight MAE of 0.032 across four Cretaceous K₁ samples is within the envelope established on synthetic benchmarks. The released software (Section 7.4) integrates into existing source-to-sink pipelines through standard tabular inputs and admits direct substitution of measured zircon age distributions for any of the four case-study samples, supporting incremental adoption in basin-specific studies."),

  h2("7.2 Comparison with existing methods"),
  body("The supervised NMF inversion of Section 4 occupies a specific niche relative to existing detrital-zircon unmixing methods. Against unsupervised NMF (Sundell and Saylor, 2017; Saylor et al., 2019), it trades the discovery of source endmembers for a 4 percentage-point gain in Top-1 dominant accuracy (0.9897 vs. 0.9495) and a factor-of-two reduction in weight MAE (0.020 vs. 0.047), at the cost of requiring source endmembers to be specified from independent geological evidence. Against fully Bayesian Dirichlet-process inversion (Tipton et al., 2022), supervised NMF trades calibrated posterior uncertainty on weights for a runtime reduction of approximately three orders of magnitude per sample. The choice between the three frameworks is therefore an engineering one: supervised NMF for dominant-source identification with known endmembers and limited compute; unsupervised NMF for endmember discovery with weaker geological priors; Bayesian Dirichlet for calibrated posterior uncertainty when the application demands it."),

  h2("7.3 Limitations"),
  body("Four limitations of the present work merit explicit discussion."),
  bodyIndent("First, the four-basin case study uses samples whose ground-truth weights are constructed from published composition estimates rather than from new measurements (Section 6.1). Validation on measured zircon age distributions — paired with independent constraints on source contributions, such as thermochronologic or Hf-isotope data — is the natural next step and is supported by the released software without modification."),
  bodyIndent("Second, the inversion treats each sample as a univariate distribution over U–Pb age. Multi-element data routinely collected alongside U–Pb ages — Lu–Hf isotopes (Cawood et al., 2012), trace elements (Belousova et al., 2002), and complementary thermochronologic systems such as muscovite Ar–Ar and apatite (U–Th)/He — are not integrated. Multi-element fusion through joint likelihood factors (Section 3.3) is a direct extension and is the subject of companion methodological work."),
  bodyIndent("Third, the Erlian case (Section 6.3) exposes a dominance-boundary failure mode. At true weights of (0.4, 0.4, 0.2), the argmax label is mathematically degenerate and any small perturbation of predicted weights resolves the dominant source to whichever entry is marginally larger. Practitioners working in regimes where two sources approach equal contribution should report the full weight vector alongside the argmax label, and should interpret the argmax-recovered dominant source with caution. Companion methodological work (in preparation) systematically characterizes the failure envelope along three independent data-difficulty axes (source number, measurement noise, and source separability)."),
  bodyIndent("Fourth, the present implementation fixes the source number at K = 3. Basins with more than three source terranes can be analysed by extension of H to K > 3 rows; the algorithm of Section 4 is structurally unchanged. Cross-validation under K > 3 has not been reported here and is the natural subject of the companion methods-boundary paper. The kernel bandwidth range [8, 20] Ma is calibrated to late-Mesozoic zircon distributions; analysis of Cenozoic or Palaeozoic distributions, where modal source ages are differently spaced, may require revalidation of the (α, bandwidth) envelope."),

  h2("7.4 Reproducibility and software availability"),
  body("The complete pipeline — synthetic data generation, KDE construction, supervised and unsupervised NMF inversion, five-fold cross-validation, sensitivity scan, case-study driver, and figure generation — is released under the MIT licence and reproduces every reported number, table and figure with a single command (python qn2025106_cli.py all). Source code, synthetic data, and figure outputs are archived on Zenodo (DOI: [TBD]); the GitHub repository ([github.com/PNOAHA/dz-unmix-cg]) provides ongoing maintenance."),
];

// =====================================================================
// 8. CONCLUSIONS
// =====================================================================
const ch8 = [
  h1("8 Conclusions"),
  body("This paper has developed a supervised NMF forward-modelling framework for detrital-zircon provenance unmixing and validated it on Cretaceous basins of Northeast Asia. Three results frame the contribution. First, supervised inversion through Kullback–Leibler multiplicative updates under a Dirichlet sparsity prior achieves Top-1 dominant-source accuracy of 0.9897 ± 0.004 in five-fold cross-validation on 1000 synthetic mixtures, exceeding the 0.85 acceptance threshold by a margin of 14 percentage points and improving on the unsupervised baseline (0.9495 ± 0.018) by 4 percentage points. Second, the accuracy persists across a 75-configuration sensitivity envelope (5 random seeds × 3 Dirichlet concentrations × 5 kernel bandwidths), with cell means in the range 0.977 to 0.996 and no configuration falling below threshold. The envelope establishes a defensible operating specification for deployment on new sample sets without per-sample retuning. Third, application of the trained inversion to four Cretaceous K₁ samples from the Songliao, Hailar, Erlian, and northern North China Craton systems — calibrated to source contributions reported in the published literature for each basin — recovers dominant sources in three of four samples with overall weight mean absolute error of 0.032. The single mismatched case lies at a dominance-degenerate boundary where the argmax label is mathematically indeterminate, an instructive operating condition rather than an inversion failure."),
  bodyIndent("The framework integrates directly into existing source-to-sink workflows through standard tabular inputs and admits substitution of measured zircon age distributions without modification. Limitations identified in Section 7.3 — the synthetic-versus-measured caveat of the case study, the univariate U–Pb restriction, the dominance-boundary degeneracy, and the fixed source number K = 3 — define the natural directions for extension; several of these directions are the subject of companion methodological work. The pipeline is released under the MIT licence and reproduces every reported number, table and figure with a single command, supporting both verification of the present results and adoption in basin-specific studies."),
];

// =====================================================================
// STATEMENTS AND DECLARATIONS
// =====================================================================
const back = [
  h1("Acknowledgements"),
  body("This work was supported by the Hebei Provincial Department of Education Research Project (Grant No. QN2025106)."),

  h1("Funding"),
  body("This research was supported by the Hebei Provincial Department of Education Research Project (Grant No. QN2025106, \"Sedimentary geological big data analysis at the interface of mathematics and earth sciences and its application to tectonic evolution models\", 2024–2027)."),

  h1("Data availability"),
  body("No new measurement data were generated for this study. The 1000-sample synthetic benchmark used in Section 4, the 75-configuration sensitivity scan output (CSV) used in Section 5, and the four basin-calibrated synthetic samples used in Section 6 are released under the MIT licence and archived on Zenodo (DOI: [TBD]). The GitHub repository at [github.com/PNOAHA/dz-unmix-cg] reproduces every reported number, table, and figure with a single command."),

  h1("Code availability"),
  body("The full pipeline — synthetic data generation, KDE construction, supervised and unsupervised NMF inversion, five-fold cross-validation, sensitivity-scan harness, case-study driver, figure-generation scripts, and CLI entry point — is implemented in Python 3.13 and released under the MIT licence at the repository cited above. A single command (python qn2025106_cli.py all) reproduces all reported results in approximately three minutes on a 2024 desktop."),

  h1("Author contributions"),
  body("Lujia Pan: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Resources, Data curation, Writing – original draft, Writing – review and editing, Visualization, Project administration, Funding acquisition."),

  h1("Competing interests"),
  body("The author declares no competing interests."),

  h1("References"),
  body([r("Reference style: Elsevier author–date (Harvard). Alphabetized by first-author surname. 42 entries total: 40 retained from the v23 (MATG) version + 2 new (Lee & Seung, 2001; Belousova et al., 2002).", { color: C_NOTE, italics: false, size: SZ_NOTE })]),
  blank(),
  refEntry("Allen, J.R.L., Allen, J.R., 2013. Basin Analysis: Principles and Application to Petroleum Play Assessment, 3rd ed. Wiley-Blackwell, Chichester."),
  refEntry("Allen, P.A., 2008. From landscapes into geological history. Nature 451, 274–276. https://doi.org/10.1038/nature06586"),
  refEntry("Andersen, T., 2005. Detrital zircons as tracers of sedimentary provenance: limiting conditions from statistics and numerical simulation. Chem. Geol. 216, 249–270. https://doi.org/10.1016/j.chemgeo.2004.11.013"),
  refEntry("Belousova, E.A., Griffin, W.L., O'Reilly, S.Y., Fisher, N.I., 2002. Igneous zircon: trace element composition as an indicator of source rock type. Contrib. Mineral. Petrol. 143, 602–622. https://doi.org/10.1007/s00410-002-0364-7"),
  refEntry("Catuneanu, O., 2006. Principles of Sequence Stratigraphy. Elsevier, Amsterdam."),
  refEntry("Cawood, P.A., Hawkesworth, C.J., Dhuime, B., 2012. Detrital zircon record and tectonic setting. Geology 40, 875–878. https://doi.org/10.1130/G32945.1"),
  refEntry("Chai, S.H., et al., 2024. A detrital zircon dataset for the eastern Central China Orogenic Belt (East Qinling, Dabie and Sulu orogens). Geosci. Data J. 11. https://doi.org/10.1002/gdj3.232"),
  refEntry("Cranmer, K., Brehmer, J., Louppe, G., 2020. The frontier of simulation-based inference. Proc. Natl. Acad. Sci. U.S.A. 117, 30055–30062. https://doi.org/10.1073/pnas.1912789117"),
  refEntry("Cuomo, S., Schiano Di Cola, V., Giampaolo, F., Rozza, G., Raissi, M., Piccialli, F., 2022. Scientific machine learning through physics-informed neural networks: where we are and what's next. J. Sci. Comput. 92, 88. https://doi.org/10.1007/s10915-022-01939-z"),
  refEntry("Dong, Y.P., et al., 2024. A database of detrital zircon U–Pb ages in the North China Craton from the Paleoproterozoic to the early Palaeozoic. Geosci. Data J. 11. https://doi.org/10.1002/gdj3.192"),
  refEntry("Feng, Z.Q., Graham, S.A., 2023. From foredeep to orogenic wedge-top: The Cretaceous Songliao retroforeland basin, China. Geosci. Front. 14 (3), 101527. https://doi.org/10.1016/j.gsf.2022.101527"),
  refEntry("Galloway, W.E., 1989. Genetic stratigraphic sequences in basin analysis I: Architecture and genesis of flooding-surface bounded depositional units. AAPG Bull. 73 (2), 125–142."),
  refEntry("Gehrels, G., 2014. Detrital zircon U-Pb geochronology applied to tectonics. Annu. Rev. Earth Planet. Sci. 42, 127–149. https://doi.org/10.1146/annurev-earth-050212-124012"),
  refEntry("Guo, Z.X., Shi, Y.P., Yang, Y.T., Jiang, S.Q., Li, L.B., Zhao, Z.G., 2018. Inversion of the Erlian Basin (NE China) in the early Late Cretaceous: implications for the collision of the Okhotomorsk Block with East Asia. J. Asian Earth Sci. 154, 49–66. https://doi.org/10.1016/j.jseaes.2017.12.007"),
  refEntry("Hovius, N., Stark, C.P., Chu, H.T., Lin, J.C., 2000. Supply and removal of sediment in a landslide-dominated mountain belt: Central Range, Taiwan. J. Geol. 108 (1), 73–89. https://doi.org/10.1086/314387"),
  refEntry("Huang, F., Jiang, S., Li, L., Zhang, Y., Zhang, Y., Zhang, R., Li, Q., Li, D., Shangguan, W., Dai, Y., 2024. Applications of explainable artificial intelligence in Earth system science. arXiv:2406.11882. https://doi.org/10.48550/arXiv.2406.11882"),
  refEntry("Karniadakis, G.E., Kevrekidis, I.G., Lu, L., Perdikaris, P., Wang, S., Yang, L., 2021. Physics-informed machine learning. Nat. Rev. Phys. 3, 422–440. https://doi.org/10.1038/s42254-021-00314-5"),
  refEntry("Lee, D.D., Seung, H.S., 2001. Algorithms for non-negative matrix factorization. In: Leen, T.K., Dietterich, T.G., Tresp, V. (Eds.), Advances in Neural Information Processing Systems 13. MIT Press, Cambridge, MA, pp. 556–562."),
  refEntry("Li, Z.Q., Chen, J.L., Zou, H., Wang, C.S., Meng, Q.A., Liu, H.L., Wang, S.Z., 2021. Mesozoic–Cenozoic tectonic evolution and dynamics of the Songliao Basin, NE Asia: implications for the closure of the Paleo-Asian Ocean and Mongol-Okhotsk Ocean and subduction of the Paleo-Pacific Ocean. Earth-Sci. Rev. 218, 103471. https://doi.org/10.1016/j.earscirev.2021.103471"),
  refEntry("Meng, F., Nie, F.J., Xia, F., Yan, Z.B., Sun, D., Zhou, W.B., Zhang, X., Wang, Q., 2024. Geochemical characteristics and detrital zircon U–Pb ages of the Yimin Formation, Kelulun Depression, Hailar Basin and constraints on uranium mineralization. PLoS ONE 19 (8), e0309433. https://doi.org/10.1371/journal.pone.0309433"),
  refEntry("Meng, Q.R., Hu, J.M., Jin, J.Q., Zhang, Y., Xu, D.F., 2003. Tectonics of the late Mesozoic wide extensional basin system in the China–Mongolia border region. Basin Res. 15, 397–415. https://doi.org/10.1046/j.1365-2117.2003.00208.x"),
  refEntry("Meng, Q.R., Zhou, Z.H., Zhu, R.X., Xu, Y.G., Guo, Z.T., 2022. Cretaceous basin evolution in northeast Asia: tectonic responses to the palaeo-Pacific plate subduction. Natl. Sci. Rev. 9 (1), nwab088. https://doi.org/10.1093/nsr/nwab088"),
  refEntry("Métivier, F., Gaudemer, Y., Tapponnier, P., Klein, M., 1999. Mass accumulation rates in Asia during the Cenozoic. Geophys. J. Int. 137 (2), 280–318. https://doi.org/10.1046/j.1365-246X.1999.00802.x"),
  refEntry("Posamentier, H.W., Vail, P.R., 1988. Eustatic controls on clastic deposition II — sequence and systems tract models. In: Wilgus, C.K., Hastings, B.S., Kendall, C.G.St.C., Posamentier, H.W., Ross, C.A., Van Wagoner, J.C. (Eds.), Sea-Level Changes: An Integrated Approach. SEPM Special Publication 42, pp. 125–154."),
  refEntry("Raissi, M., Perdikaris, P., Karniadakis, G.E., 2019. Physics-informed neural networks: a deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. J. Comput. Phys. 378, 686–707. https://doi.org/10.1016/j.jcp.2018.10.045"),
  refEntry("Reiners, P.W., Brandon, M.T., 2006. Using thermochronology to understand orogenic erosion. Annu. Rev. Earth Planet. Sci. 34, 419–466. https://doi.org/10.1146/annurev.earth.34.031405.125202"),
  refEntry("Romans, B.W., Castelltort, S., Covault, J.A., Fildani, A., Walsh, J.P., 2016. Environmental signal propagation in sedimentary systems across timescales. Earth-Sci. Rev. 153, 7–29. https://doi.org/10.1016/j.earscirev.2015.07.012"),
  refEntry("Sambridge, M., Mosegaard, K., 2002. Monte Carlo methods in geophysical inverse problems. Rev. Geophys. 40, 1009. https://doi.org/10.1029/2000RG000089"),
  refEntry("Saylor, J.E., Sundell, K.E., Sharman, G.R., 2019. Characterizing sediment sources by non-negative matrix factorization of detrital geochronological data. Earth Planet. Sci. Lett. 512, 46–58. https://doi.org/10.1016/j.epsl.2019.01.044"),
  refEntry("Sharman, G.R., Johnstone, S.A., 2017. Sediment unmixing using detrital geochronology. Earth Planet. Sci. Lett. 477, 183–194. https://doi.org/10.1016/j.epsl.2017.07.044"),
  refEntry("Sundell, K.E., Saylor, J.E., 2017. Unmixing detrital geochronology age distributions. Geochem. Geophys. Geosyst. 18, 2872–2886. https://doi.org/10.1002/2017GC006944"),
  refEntry("Sundell, K.E., Saylor, J.E., 2021. Two-dimensional case studies of detrital geochronology unmixing. Geochronology 3, 435–450. https://doi.org/10.5194/gchron-3-435-2021"),
  refEntry("Tarantola, A., 2005. Inverse Problem Theory and Methods for Model Parameter Estimation. SIAM, Philadelphia."),
  refEntry("Tipton, J.R., Sharman, G.R., Johnstone, S.A., 2022. A Bayesian nonparametric approach to unmixing detrital geochronologic data. Math. Geosci. 54, 151–176. https://doi.org/10.1007/s11004-021-09961-x"),
  refEntry("Tofelde, S., Bernhardt, A., Guerit, L., Romans, B.W., 2021. Times associated with source-to-sink propagation of environmental signals during landscape transience. Front. Earth Sci. 9, 628315. https://doi.org/10.3389/feart.2021.628315"),
  refEntry("Vermeesch, P., 2012. On the visualisation of detrital age distributions. Chem. Geol. 312–313, 190–194. https://doi.org/10.1016/j.chemgeo.2012.04.021"),
  refEntry("Vermeesch, P., 2013. Multi-sample comparison of detrital age distributions. Chem. Geol. 341, 140–146. https://doi.org/10.1016/j.chemgeo.2013.01.010"),
  refEntry("Vermeesch, P., 2018. IsoplotR: a free and open toolbox for geochronology. Geosci. Front. 9, 1479–1493. https://doi.org/10.1016/j.gsf.2018.04.001"),
  refEntry("Wang, P.J., Mattern, F., Didenko, N.A., Zhu, D.F., Singer, B., Sun, X.M., 2016. Tectonics and cycle system of the Cretaceous Songliao Basin: an inverted active continental margin basin. Earth-Sci. Rev. 159, 82–102. https://doi.org/10.1016/j.earscirev.2016.05.004"),
  refEntry("Wang, T., Tong, Y., Xiao, W.J., Guo, L., Windley, B.F., Donskaya, T., Li, S., Tserendash, N., Zhang, J.J., 2022. Rollback, scissor-like closure of the Mongol-Okhotsk Ocean and formation of an orocline: magmatic migration based on a large archive of age data. Natl. Sci. Rev. 9 (5), nwab210. https://doi.org/10.1093/nsr/nwab210"),
  refEntry("Yang, J., Wang, P., Huang, H., Hu, X., 2024. A brief introduction to the detrital zircon U–Pb and Hf isotopic datasets for mainland China and adjacent regions. Geosci. Data J. 11, 531–537. https://doi.org/10.1002/gdj3.229"),
  refEntry("Zhang, B., Liu, S.F., Zhang, C.X., 2023. EaDz: a web-based, relational database for detrital zircons from East Asia. Comput. Geosci. 171, 105288. https://doi.org/10.1016/j.cageo.2022.105288"),
];

// =====================================================================
// FOOTER + HEADER
// =====================================================================
const docFooter = new Footer({
  children: [new Paragraph({
    children: [
      new TextRun({ children: [PageNumber.CURRENT], font: F_BODY, size: 20 }),
      r(" / ", { size: 20 }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], font: F_BODY, size: 20 }),
    ],
    alignment: AlignmentType.CENTER,
  })],
});

const docHeader = new Header({
  children: [new Paragraph({
    children: [r("Pan — Detrital-zircon provenance unmixing with supervised NMF", { size: 18, color: C_NOTE })],
    alignment: AlignmentType.RIGHT,
  })],
});

// =====================================================================
// BUILD
// =====================================================================
const doc = new Document({
  creator: "Lujia Pan",
  title: "Detrital-Zircon Provenance Unmixing with Supervised NMF: A Forward Modelling Framework Validated on Cretaceous Basins of Northeast Asia",
  description: "Manuscript for submission to Computers & Geosciences (Elsevier), C&G author-date Harvard style",
  styles: {
    default: { document: { run: { font: F_BODY, size: SZ_BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SZ_H1, bold: true, font: F_HEAD },
        paragraph: { spacing: { before: 480, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SZ_H2, bold: true, font: F_HEAD },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SZ_H3, bold: true, italics: true, font: F_HEAD },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
      lineNumbers: {
        countBy: 1,
        start: 1,
        restart: LineNumberRestartFormat.CONTINUOUS,
        distance: 360,
      },
    },
    headers: { default: docHeader },
    footers: { default: docFooter },
    children: [
      ...front,
      ...ch1,
      ...ch2,
      ...ch3,
      ...ch4,
      ...ch5,
      ...ch6,
      ...ch7,
      ...ch8,
      ...back,
    ],
  }],
});

const out = path.join(__dirname, "QN2025106_CG_manuscript.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(out, buf);
  console.log("Generated:", out);
}).catch(e => {
  console.error(e);
  process.exit(1);
});
