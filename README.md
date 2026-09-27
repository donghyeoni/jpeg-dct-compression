# JPEG / DCT Image Compression

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)

Lossy image compression on a 512x512 test image, comparing a
**custom sum/difference subband decomposition** against a **textbook block-DCT
JPEG pipeline**. The full coding chain is implemented from scratch: transform,
quantization, zig-zag scan, unary entropy coding, and the exact inverse. QP is
swept to plot rate-distortion curves (bits-per-pixel vs MSE), and a per-subband
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
so QP alone sets the step size) and then decoded. The decoded subbands are
reconstructed into an image (clipped to `[0, 255]`), and distortion is the MSE
against the input image. The script reports rate and distortion at a single
QP, sweeps a list of QP values to plot a rate-distortion curve, and searches
for the **optimal per-subband QP** of each channel (Y, U, V) that minimizes
`cost = alpha * MSE + beta * rate` on that subband, then plots an RD curve as
those QPs are scaled. **No DCT** is used in this pipeline.

### 3. Block-DCT JPEG (`experiments/03_block_dct_jpeg.py`)

A true JPEG-style codec. The image (YUV) is split into `8 x 8` blocks; each block
runs the full chain **level shift (-128) -> 2-D DCT -> quantize (standard JPEG
luminance/chrominance tables) -> zig-zag -> unary-encode**, and the inverse. QP
is swept, the full image is rebuilt at each QP (rounded and clipped to
`[0, 255]`), and the rate-distortion curve is plotted.

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
├── assets/                 # committed test image + RD-curve figures (shown below)
├── docs/                   # project report (PDF)
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the experiments (add `--image <path>` to use your own image):

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

All numbers and figures below are from the test image.

### 1. Subband transform — invertibility

3-level sum/difference decomposition (64 subbands), both scan orders,
reconstructed:

| Order | Reconstruction MSE |
| --- | --- |
| horizontal-first | 0.0 |
| vertical-first | 0.0 |

### 2. Subband compression — rate-distortion

Flat unit quantization tables with a single QP for every subband:

| QP | MSE | rate (bpp) |
| --- | --- | --- |
| 139 | 7.99 | 6.42 |
| 160 | 9.63 | 5.96 |
| 192 | 12.47 | 5.44 |
| 240 | 17.49 | 4.93 |
| 310 | 24.71 | 4.47 |
| 450 | 38.69 | 3.98 |

Per-subband optimal QPs of each channel (minimizing
`cost = alpha * MSE + beta * rate`), scaled by a factor `SV`:

| SV | MSE | rate (bpp) |
| --- | --- | --- |
| 3.1 | 4.55 | 5.86 |
| 3.5 | 5.65 | 5.52 |
| 4.0 | 6.93 | 5.19 |
| 5.0 | 9.85 | 4.73 |
| 6.0 | 13.80 | 4.43 |
| 7.7 | 20.52 | 4.09 |

![subband QP sweep](assets/rd_subband_qp.png)
![subband scaled RD](assets/rd_subband_scaled.png)

### 3. Block-DCT JPEG — rate-distortion

8x8 block DCT with level shift and the standard JPEG luminance/chrominance
tables:

| QP | MSE | rate (bpp) |
| --- | --- | --- |
| 1 | 15.56 | 4.18 |
| 2 | 26.25 | 3.58 |
| 3 | 35.36 | 3.39 |
| 5 | 53.75 | 3.23 |
| 10 | 108.30 | 3.11 |
| 20 | 234.44 | 3.05 |

![block DCT RD](assets/rd_block_dct.png)

## Notes

- The subband transform uses integer arithmetic with `// 2` in the inverse;
  for integer inputs `a + b` and `a - b` have the same parity, so
  reconstruction is exact.
- Unary coding here is a simple variable-length scheme, not an optimal entropy
  coder; its total code length is used only as a bit-rate estimate. Rate is
  normalized by `512 * 512` pixels throughout.
- A project report is in `docs/`.
