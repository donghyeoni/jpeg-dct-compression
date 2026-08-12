# JPEG / DCT Image Compression

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)

Lossy image compression on a 512x512 test image, comparing a
**custom sum/difference subband decomposition** against a **textbook block-DCT
JPEG pipeline**. The full coding chain is implemented from scratch: transform,
quantization, zig-zag scan, unary entropy coding, and the exact inverse. QP is
swept to plot rate-distortion curves (bits-per-pixel vs MSE), and a per-block
optimal-QP search minimizes a rate-distortion cost.

## Overview

The project builds up lossy compression from primitive operations and studies
the rate-distortion trade-off of two transform strategies. Everything runs on a
single 512x512 image; "rate" is measured as total unary-code bits divided by the
number of pixels, and "distortion" as mean squared error (MSE).

## The three pipelines

### 1. Subband transform (`experiments/01_subband_transform.py`)

A custom Haar-like **sum/difference** subband transform. Each 1-D step pairs
adjacent samples `a, b` into a *sum* channel `a + b` and a *difference* channel
`a - b`; the inverse recovers them via `(sum + diff) / 2` and `(sum - diff) / 2`.
Applying this recursively for 3 levels in one direction, then 3 levels in the
other, yields a `8 x 8 = 64` subband pyramid. This experiment runs both orders
(horizontal-first and vertical-first), reconstructs, and reports the
reconstruction MSE. **No entropy coding** is involved — it only demonstrates
invertibility of the transform.

Implemented in `src/subband.py`.

### 2. Subband compression (`experiments/02_subband_compression.py`)

Uses the 3-level (vertical-then-horizontal) decomposition to produce 64 sub-images
of size `64 x 64`, in YUV. Each channel of each sub-image is compressed with
**quantize -> zig-zag -> unary-encode** (using flat *unit* quantization tables,
so QP alone sets the step size) and then decoded. The script reports rate and
distortion at a single QP, sweeps a list of QP values to plot a rate-distortion
curve, and searches for the **optimal per-subband QP** that minimizes
`cost = alpha * MSE + beta * rate`, then plots an RD curve as those QPs are
scaled. **No DCT** is used in this pipeline.

### 3. Block-DCT JPEG (`experiments/03_block_dct_jpeg.py`)

A true JPEG-style codec. The image (YUV) is split into `8 x 8` blocks; each block
runs the full chain **2-D DCT -> quantize (standard JPEG luminance/chrominance
tables) -> zig-zag -> unary-encode**, and the inverse. QP is swept, the full
image is rebuilt at each QP, and the rate-distortion curve is plotted.

## Test image

No dataset is required. The committed test input is a 512x512 food photograph
([`assets/food.jpg`](assets/food.jpg)), which the experiment scripts use by
default. To run on a different picture, pass any 512x512 color image with
`--image <path>`.

## Project structure

```
jpeg-dct-compression/
├── src/
│   ├── subband.py          # sum/difference transform + multi-level decompose/reconstruct
│   ├── dct.py              # apply_2d_dct, apply_2d_idct (scipy.fftpack)
│   ├── quantization.py     # quantize/dequantize, standard JPEG tables + unit-table variant
│   ├── zigzag.py           # zigzag / inverse_zigzag (parameterized block size 8 vs 64)
│   ├── entropy.py          # unary_encode / unary_decode, bit-length counting
│   ├── blocks.py           # split_image_into_blocks, restore_image_from_blocks
│   ├── jpeg_codec.py       # image_compress / image_decompress orchestration
│   ├── rate_distortion.py  # QP sweeps, RD-curve plotting, optimal-QP cost search
│   ├── metrics.py          # calculate_mse, calculate_list_mse
│   └── io_utils.py         # image loading helpers
├── experiments/
│   ├── 01_subband_transform.py
│   ├── 02_subband_compression.py
│   └── 03_block_dct_jpeg.py
├── run_all.py              # run all 3 experiments on the test image -> results/
├── assets/                 # committed test image + RD-curve figures (shown below)
├── docs/                   # project report (PDF)
├── requirements.txt
└── README.md
```

Running `run_all.py` writes its logs and figures to an untracked `results/`
directory.

## Setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Reproduce everything under `results/` on the committed test image:

```bash
python run_all.py
```

Or run experiments individually (add `--image <path>` to use your own image):

```bash
# 1. Subband transform: reconstruction MSE for both orders
python experiments/01_subband_transform.py --levels 3

# 2. Subband compression: single-QP report, QP sweep, optimal-QP search
python experiments/02_subband_compression.py --save-dir results

# 3. Block-DCT JPEG: QP sweep and RD curve
python experiments/03_block_dct_jpeg.py --save-dir results
```

Common flags: `--no-plot` skips plotting entirely, and `--save-dir <dir>`
saves the RD-curve PNGs instead of displaying them interactively.

## Results

All numbers and figures below come from `python run_all.py` on the test
image.

### 1. Subband transform — invertibility

3-level sum/difference decomposition (64 subbands), both scan orders,
reconstructed:

| Order | Reconstruction MSE |
| --- | --- |
| horizontal-first | 0.0 |
| vertical-first | 0.0 |

The transform is perfectly invertible on the test image.

### 2. Subband compression — rate-distortion

Flat unit quantization tables with a single QP for every subband:

| QP | MSE | rate (bpp) |
| --- | --- | --- |
| 139 | 489.4 | 6.42 |
| 160 | 606.4 | 5.96 |
| 192 | 798.1 | 5.44 |
| 240 | 1102.7 | 4.93 |
| 310 | 1559.1 | 4.47 |
| 450 | 2464.8 | 3.98 |

Per-subband optimal QPs (minimizing `cost = alpha * MSE + beta * rate`),
scaled by a factor `SV` — much lower MSE at comparable rates:

| SV | MSE | rate (bpp) |
| --- | --- | --- |
| 3.1 | 248.6 | 5.90 |
| 3.5 | 307.8 | 5.56 |
| 4.0 | 388.0 | 5.23 |
| 5.0 | 568.6 | 4.76 |
| 6.0 | 823.3 | 4.45 |
| 7.7 | 1275.7 | 4.11 |

![subband QP sweep](assets/rd_subband_qp.png)
![subband scaled RD](assets/rd_subband_scaled.png)

### 3. Block-DCT JPEG — rate-distortion

Textbook 8x8 block DCT with the standard JPEG luminance/chrominance tables:

| QP | MSE | rate (bpp) |
| --- | --- | --- |
| 1 | 17.1 | 6.34 |
| 2 | 29.4 | 4.66 |
| 3 | 38.1 | 4.09 |
| 5 | 57.6 | 3.65 |
| 10 | 117.5 | 3.31 |
| 20 | 255.5 | 3.15 |

![block DCT RD](assets/rd_block_dct.png)

The block-DCT JPEG pipeline reaches far lower MSE at low bit-rates than the
flat subband scheme, as expected — the DCT concentrates energy into few
coefficients.

## Notes

- The subband transform uses integer arithmetic with `// 2` in the inverse, so
  reconstruction is near-lossless but not guaranteed bit-exact for odd values.
- Unary coding here is a simple variable-length scheme, not an optimal entropy
  coder; its total code length is used only as a bit-rate estimate. Rate is
  normalized by `512 * 512` pixels throughout.
- The optimal-QP search in experiment 2 scans hundreds of QP values per subband
  and is the slowest step of `run_all.py`.
- A project report is in `docs/`.
