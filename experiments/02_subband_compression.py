"""Experiment 2: subband compression with QP sweep and optimal-QP search.

Takes the 3-level (vertical-then-horizontal) decomposition of the Lena image in
YUV, giving 64 sub-images of size 64x64. Each channel of each sub-image is
compressed via quantize -> zig-zag -> unary-encode using unit quantization
tables, then decoded. The script:

  1. Reports rate and distortion at a single QP.
  2. Sweeps a list of QP values and plots the rate-distortion curve.
  3. Searches for the per-subband optimal QP (minimizing alpha*MSE + beta*rate)
     and plots an RD curve as the found QPs are scaled.

No DCT is used in this pipeline.

Usage:
    python experiments/02_subband_compression.py --image data/lena.bmp
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.io_utils import load_image
from src.subband import decompose
from src.quantization import unit_quant_table
from src.jpeg_codec import image_compress, image_decompress
from src.entropy import count_bits
from src.metrics import calculate_mse, calculate_list_mse
from src.rate_distortion import (sweep_blocks, find_optimal_qp, plot_rd_curve,
                                 TOTAL_PIXELS)

BLOCK = 64
QP_VALUES = [139, 160, 192, 240, 310, 450]
SCALING_VALUES = [3.1, 3.5, 4, 5, 6, 7.7]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="data/lena.bmp", help="Path to lena.bmp")
    parser.add_argument("--single-qp", type=float, default=100, help="QP for the single-point report")
    parser.add_argument("--no-plot", action="store_true", help="Skip RD-curve plotting")
    parser.add_argument("--save-dir", default=None, help="Directory to save RD-curve PNGs")
    args = parser.parse_args()

    image_yuv = load_image(args.image, color_space="yuv")
    subbands = decompose(image_yuv, levels=3, order="vertical_first")
    print(f"Decomposed into {len(subbands)} subbands of shape {subbands[0].shape}")

    lum = unit_quant_table(BLOCK)
    chrom = unit_quant_table(BLOCK)

    # 1. Single-QP report ----------------------------------------------------
    restored_list, size = [], 0
    for sub in subbands:
        cY = image_compress(sub[:, :, 0], lum, args.single_qp, use_dct=False)
        cU = image_compress(sub[:, :, 1], chrom, args.single_qp, use_dct=False)
        cV = image_compress(sub[:, :, 2], chrom, args.single_qp, use_dct=False)
        dY = image_decompress(cY, lum, args.single_qp, use_dct=False, block_size=BLOCK)
        dU = image_decompress(cU, chrom, args.single_qp, use_dct=False, block_size=BLOCK)
        dV = image_decompress(cV, chrom, args.single_qp, use_dct=False, block_size=BLOCK)
        restored_list.append(np.stack((dY, dU, dV), axis=2))
        size += count_bits(cY) + count_bits(cU) + count_bits(cV)
    print(f"QP={args.single_qp}: total bits={size}, "
          f"rate={size / TOTAL_PIXELS:.4f}, "
          f"MSE={calculate_list_mse(subbands, restored_list):.4f}")

    # 2. QP sweep ------------------------------------------------------------
    rate_list, distortion_list = sweep_blocks(
        subbands, lum, chrom, QP_VALUES, use_dct=False, block_size=BLOCK)
    print("\nQP sweep (QP, MSE, rate):")
    for qp, d, r in zip(QP_VALUES, distortion_list, rate_list):
        print(f"  {qp}\t{d:.4f}\t{r:.4f}")

    if not args.no_plot:
        save = os.path.join(args.save_dir, "rd_subband_qp.png") if args.save_dir else None
        plot_rd_curve(rate_list, distortion_list, labels=QP_VALUES,
                      title="Subband Compression Rate-Distortion Curve", save_path=save)

    # 3. Optimal per-subband QP search + scaled RD curve ---------------------
    print("\nSearching optimal per-subband QP (this is slow)...")
    optimal_lum = find_optimal_qp(subbands, lum, channel=0, block_size=BLOCK, use_dct=False)
    optimal_chrom = find_optimal_qp(subbands, chrom, channel=1, block_size=BLOCK, use_dct=False)
    print("optimal QP (luminance):", optimal_lum)
    print("optimal QP (chrominance):", optimal_chrom)

    rate_list2, distortion_list2 = [], []
    for sv in SCALING_VALUES:
        restored, size = [], 0
        for i, sub in enumerate(subbands):
            qp_l, qp_c = optimal_lum[i] * sv, optimal_chrom[i] * sv
            cY = image_compress(sub[:, :, 0], lum, qp_l, use_dct=False)
            cU = image_compress(sub[:, :, 1], chrom, qp_c, use_dct=False)
            cV = image_compress(sub[:, :, 2], chrom, qp_c, use_dct=False)
            dY = image_decompress(cY, lum, qp_l, use_dct=False, block_size=BLOCK)
            dU = image_decompress(cU, chrom, qp_c, use_dct=False, block_size=BLOCK)
            dV = image_decompress(cV, chrom, qp_c, use_dct=False, block_size=BLOCK)
            restored.append(np.stack((dY, dU, dV), axis=2))
            size += count_bits(cY) + count_bits(cU) + count_bits(cV)
        distortion_list2.append(calculate_list_mse(subbands, restored))
        rate_list2.append(size / TOTAL_PIXELS)
        print(f"  SV={sv}\tMSE={distortion_list2[-1]:.4f}\trate={rate_list2[-1]:.4f}")

    if not args.no_plot:
        save = os.path.join(args.save_dir, "rd_subband_scaled.png") if args.save_dir else None
        plot_rd_curve(rate_list2, distortion_list2, labels=SCALING_VALUES,
                      label_prefix="SV",
                      title="Subband RD Curve (scaled optimal QP)", save_path=save)


if __name__ == "__main__":
    main()
