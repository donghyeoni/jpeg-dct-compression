"""Experiment 1: sum/difference (Haar-like) subband transform.

Performs a 3-level sum/difference decomposition of the Lena image in both
orders (horizontal-first and vertical-first), reconstructs, and reports the
reconstruction MSE. No entropy coding is involved here -- this experiment only
verifies that the transform is (near) perfectly invertible.

Usage:
    python experiments/01_subband_transform.py --image data/lena.bmp --levels 3
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.io_utils import load_image
from src.subband import decompose, reconstruct
from src.metrics import calculate_mse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="data/lena.bmp", help="Path to lena.bmp")
    parser.add_argument("--levels", type=int, default=3, help="Decomposition levels per direction")
    args = parser.parse_args()

    image = load_image(args.image, color_space="rgb")
    print(f"Loaded image: shape={image.shape}")

    for order in ("horizontal_first", "vertical_first"):
        subbands = decompose(image, levels=args.levels, order=order)
        restored = reconstruct(subbands, levels=args.levels, order=order)
        mse = calculate_mse(image, restored)
        print(f"[{order}] {len(subbands)} subbands -> reconstruction MSE = {mse}")


if __name__ == "__main__":
    main()
