"""Experiment 3: textbook block-DCT JPEG codec with a QP sweep.

Splits the Lena image (YUV) into 8x8 blocks, then for each block applies the
full JPEG chain: 2-D DCT -> quantize (standard luminance/chrominance tables) ->
zig-zag -> unary-encode, and the inverse. Sweeps a list of QP values, rebuilds
the full image at each QP, and plots the rate-distortion curve.

Usage:
    python experiments/03_block_dct_jpeg.py --image data/lena.bmp
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.io_utils import load_image
from src.blocks import split_image_into_blocks, restore_image_from_blocks
from src.quantization import LUMINANCE_QUANT_TABLE, CHROMINANCE_QUANT_TABLE
from src.rate_distortion import sweep_blocks, plot_rd_curve

BLOCK = 8
QP_VALUES = [1, 2, 3, 5, 10, 20]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="data/lena.bmp", help="Path to lena.bmp")
    parser.add_argument("--no-plot", action="store_true", help="Skip RD-curve plotting")
    parser.add_argument("--save-dir", default=None, help="Directory to save the RD-curve PNG")
    args = parser.parse_args()

    image_yuv = load_image(args.image, color_space="yuv")
    blocks = split_image_into_blocks(image_yuv, BLOCK)
    print(f"Split into {len(blocks)} blocks of shape {blocks[0].shape}")

    def reconstruct_fn(restored_blocks):
        return restore_image_from_blocks(restored_blocks, image_size=512,
                                         block_size=BLOCK, channels=3)

    rate_list, distortion_list = sweep_blocks(
        blocks, LUMINANCE_QUANT_TABLE, CHROMINANCE_QUANT_TABLE, QP_VALUES,
        use_dct=True, block_size=BLOCK,
        reconstruct_fn=reconstruct_fn, reference=image_yuv)

    print("\nQP sweep (QP, MSE, rate):")
    for qp, d, r in zip(QP_VALUES, distortion_list, rate_list):
        print(f"  {qp}\t{d:.4f}\t{r:.4f}")

    if not args.no_plot:
        save = os.path.join(args.save_dir, "rd_block_dct.png") if args.save_dir else None
        plot_rd_curve(rate_list, distortion_list, labels=QP_VALUES,
                      title="Block-DCT JPEG Rate-Distortion Curve", save_path=save)


if __name__ == "__main__":
    main()
