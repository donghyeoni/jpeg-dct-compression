"""Experiment 2: subband compression with QP sweep and optimal-QP search.

Takes the 3-level (vertical-then-horizontal) decomposition of the input image
in YUV, giving 64 sub-images of size 64x64. Each channel of each sub-image is
compressed via quantize -> zig-zag -> unary-encode using unit quantization
tables, then decoded. The decoded subbands are reconstructed into an image
(clipped to [0, 255]) and compared with the input image. The script:

  1. Reports rate and distortion at a single QP.
  2. Sweeps a list of QP values and plots the rate-distortion curve.
  3. Searches for the per-subband optimal QP of each channel (minimizing
     alpha*MSE + beta*rate on the subband) and plots an RD curve as the found
     QPs are scaled.

No DCT is used in this pipeline.

Usage:
    python experiments/02_subband_compression.py
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.io_utils import load_image
from src.subband import decompose, reconstruct
from src.quantization import unit_quant_table
from src.jpeg_codec import image_compress, image_decompress
from src.entropy import count_bits
from src.metrics import calculate_mse
from src.rate_distortion import (sweep_blocks, find_optimal_qp, plot_rd_curve,
                                 TOTAL_PIXELS)

BLOCK = 64
LEVELS = 3
ORDER = "vertical_first"
QP_VALUES = [139, 160, 192, 240, 310, 450]
SCALING_VALUES = [3.1, 3.5, 4, 5, 6, 7.7]


def reconstruct_image(restored_subbands):
    return np.clip(reconstruct(restored_subbands, levels=LEVELS, order=ORDER), 0, 255)


def code_subbands(subbands, table, qps):
    restored, size = [], 0
    for sub, qp in zip(subbands, qps):
        channels = []
        for c in range(3):
            code = image_compress(sub[:, :, c], table, qp[c], use_dct=False)
            channels.append(image_decompress(code, table, qp[c], use_dct=False, block_size=BLOCK))
            size += count_bits(code)
        restored.append(np.stack(channels, axis=2))
    return restored, size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="assets/food.jpg", help="Path to a 512x512 color image")
    parser.add_argument("--single-qp", type=float, default=100, help="QP for the single-point report")
    parser.add_argument("--no-plot", action="store_true", help="Skip RD-curve plotting")
    parser.add_argument("--save-dir", default=None, help="Directory to save RD-curve PNGs")
    args = parser.parse_args()

    image_yuv = load_image(args.image, color_space="yuv")
    subbands = decompose(image_yuv, levels=LEVELS, order=ORDER)
    print(f"Decomposed into {len(subbands)} subbands of shape {subbands[0].shape}")

    table = unit_quant_table(BLOCK)

    # 1. Single-QP report ----------------------------------------------------
    restored, size = code_subbands(subbands, table, [(args.single_qp,) * 3] * len(subbands))
    print(f"QP={args.single_qp}: total bits={size}, "
          f"rate={size / TOTAL_PIXELS:.4f}, "
          f"MSE={calculate_mse(image_yuv, reconstruct_image(restored)):.4f}")

    # 2. QP sweep ------------------------------------------------------------
    rate_list, distortion_list = sweep_blocks(
        subbands, table, table, QP_VALUES, use_dct=False, block_size=BLOCK,
        reconstruct_fn=reconstruct_image, reference=image_yuv)
    print("\nQP sweep (QP, MSE, rate):")
    for qp, d, r in zip(QP_VALUES, distortion_list, rate_list):
        print(f"  {qp}\t{d:.4f}\t{r:.4f}")

    if not args.no_plot:
        save = os.path.join(args.save_dir, "rd_subband_qp.png") if args.save_dir else None
        plot_rd_curve(rate_list, distortion_list, labels=QP_VALUES,
                      title="Subband Compression Rate-Distortion Curve", save_path=save)

    # 3. Optimal per-subband QP search + scaled RD curve ---------------------
    print("\nSearching optimal per-subband QP...")
    optimal = [find_optimal_qp(subbands, table, channel=c, block_size=BLOCK) for c in range(3)]
    for name, qps in zip("YUV", optimal):
        print(f"optimal QP ({name}):", qps)

    rate_list2, distortion_list2 = [], []
    for sv in SCALING_VALUES:
        restored, size = code_subbands(subbands, table, np.stack(optimal, axis=1) * sv)
        distortion_list2.append(calculate_mse(image_yuv, reconstruct_image(restored)))
        rate_list2.append(size / TOTAL_PIXELS)
        print(f"  SV={sv}\tMSE={distortion_list2[-1]:.4f}\trate={rate_list2[-1]:.4f}")

    if not args.no_plot:
        save = os.path.join(args.save_dir, "rd_subband_scaled.png") if args.save_dir else None
        plot_rd_curve(rate_list2, distortion_list2, labels=SCALING_VALUES,
                      label_prefix="SV",
                      title="Subband RD Curve (scaled optimal QP)", save_path=save)


if __name__ == "__main__":
    main()
