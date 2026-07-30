# JPEG / DCT Image Compression

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)

Lossy image compression on the standard **Lena** test image, comparing a
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

## Dataset

The original notebooks used the standard **Lena** test image (`lena.bmp`,
512x512 color). That image has historically restricted / ambiguous licensing
and is **not redistributed here**.

To keep the pipeline **reproducible with no external data**, `run_all.py`
synthesizes a deterministic 512x512 test image (fixed seed) and runs all three
experiments on it — the committed results under `results/` are produced this
way. You can still pass any 512x512 color image via `--image <path>` (e.g. your
own `data/lena.bmp`) to reproduce the original-style curves.

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
│   └── io_utils.py         # image loading (replaces Colab/Drive paths)
├── experiments/
│   ├── 01_subband_transform.py
│   ├── 02_subband_compression.py
│   └── 03_block_dct_jpeg.py
├── run_all.py              # synthesize a 512x512 image + run all 3 experiments -> results/
├── results/                # committed artifacts (logs, RD-curve PNGs, synthetic input)
│   └── notebook_reference/ # figures/logs preserved from the original Lena notebooks
├── docs/                   # project report (PDF)
├── data/                   # optional: drop your own lena.bmp here (not tracked)
├── requirements.txt
├── RESULTS.md
└── README.md
```

## Setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -r requirements.txt
```

Then place `lena.bmp` in `data/`.

## Usage

Reproduce everything under `results/` on a synthetic image (no data needed):

```bash
python run_all.py
```

Or run experiments individually on your own image:

```bash
# 1. Subband transform: reconstruction MSE for both orders
python experiments/01_subband_transform.py --image data/lena.bmp --levels 3

# 2. Subband compression: single-QP report, QP sweep, optimal-QP search
python experiments/02_subband_compression.py --image data/lena.bmp --save-dir results

# 3. Block-DCT JPEG: QP sweep and RD curve
python experiments/03_block_dct_jpeg.py --image data/lena.bmp --save-dir results
```

Common flags: `--no-plot` skips the matplotlib windows, and `--save-dir <dir>`
saves the RD-curve PNGs instead of (or in addition to) displaying them.

## Notes

- The `src/` modules consolidate helpers that were copy-pasted across the three
  original notebooks (`process_horizontal/vertical`, `quantize`, `zigzag`,
  `unary_encode/decode`, `calculate_mse`, ...). Algorithms are preserved as-is,
  including the loop-based integer transforms.
- The subband transform uses integer arithmetic with `// 2` in the inverse, so
  reconstruction is near-lossless but not guaranteed bit-exact for odd values.
- Unary coding here is a simple variable-length scheme, not an optimal entropy
  coder; its total code length is used only as a bit-rate estimate. Rate is
  normalized by `512 * 512` pixels throughout, matching the original notebooks.
- The optimal-QP search in experiment 2 scans hundreds of QP values per subband
  and is intentionally slow.
- Rate-distortion curves and logs are committed under `results/` (generated by
  `run_all.py` on the synthetic image) — see [RESULTS.md](RESULTS.md).
- The original Colab notebooks have been removed; their embedded figures and
  logs (on the Lena image) are preserved under `results/notebook_reference/`.
  A project report is in `docs/`.
