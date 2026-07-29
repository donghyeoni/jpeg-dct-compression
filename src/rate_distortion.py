"""Rate-distortion sweeps, RD-curve plotting, and optimal-QP search."""

import numpy as np
import matplotlib.pyplot as plt

from .jpeg_codec import image_compress, image_decompress
from .entropy import count_bits
from .metrics import calculate_mse, calculate_list_mse

TOTAL_PIXELS = 512 * 512  # rate normalization used throughout the notebooks


def sweep_blocks(blocks, luminance_table, chrominance_table, QP_values,
                 use_dct=True, block_size=8, reconstruct_fn=None, reference=None):
    """Sweep a list of QP values over a list of 3-channel blocks/subbands.

    For each QP, every block's Y channel is coded with ``luminance_table`` and
    its U, V channels with ``chrominance_table``. Rate is total bits divided by
    ``512 * 512``.

    Distortion is computed in one of two ways:

    * If ``reconstruct_fn`` and ``reference`` are given, the restored blocks are
      reassembled into a full image via ``reconstruct_fn`` and compared to
      ``reference`` with MSE (block-DCT JPEG pipeline).
    * Otherwise, the MSE is taken directly between the stacks of original and
      restored blocks (subband compression pipeline).

    Returns
    -------
    (rate_list, distortion_list) : tuple of lists
    """
    rate_list, distortion_list = [], []
    for qp in QP_values:
        restored_blocks = []
        size = 0
        for block in blocks:
            cY = image_compress(block[:, :, 0], luminance_table, qp, use_dct)
            cU = image_compress(block[:, :, 1], chrominance_table, qp, use_dct)
            cV = image_compress(block[:, :, 2], chrominance_table, qp, use_dct)

            dY = image_decompress(cY, luminance_table, qp, use_dct, block_size)
            dU = image_decompress(cU, chrominance_table, qp, use_dct, block_size)
            dV = image_decompress(cV, chrominance_table, qp, use_dct, block_size)

            restored_blocks.append(np.stack((dY, dU, dV), axis=2))
            size += count_bits(cY) + count_bits(cU) + count_bits(cV)

        if reconstruct_fn is not None and reference is not None:
            restored = reconstruct_fn(restored_blocks)
            distortion_list.append(calculate_mse(reference, restored))
        else:
            distortion_list.append(calculate_list_mse(blocks, restored_blocks))

        rate_list.append(size / TOTAL_PIXELS)
    return rate_list, distortion_list


def find_optimal_qp(subbands, quant_table, channel, qp_range=range(1, 300),
                    alpha=0.05, beta=0.95, block_size=64, use_dct=False):
    """Per-subband QP that minimizes ``cost = alpha * MSE + beta * rate``.

    Searches ``qp_range`` for a single channel index (0=Y, 1=U, 2=V) across all
    subbands. Returns an array of the optimal QP per subband.
    """
    optimal = np.zeros(len(subbands))
    for j, sub in enumerate(subbands):
        min_cost = float("inf")
        best_qp = None
        for qp in qp_range:
            compressed = image_compress(sub[:, :, channel], quant_table, qp, use_dct)
            decompressed = image_decompress(compressed, quant_table, qp, use_dct, block_size)
            mse_value = calculate_mse(sub[:, :, channel], decompressed)
            rate = count_bits(compressed) / (block_size * block_size)
            cost = alpha * mse_value + beta * rate
            if cost < min_cost:
                min_cost = cost
                best_qp = qp
        optimal[j] = best_qp
    return optimal


def plot_rd_curve(rate_list, distortion_list, labels=None, label_prefix="QP",
                  title="Rate-Distortion Curve", save_path=None):
    """Plot an MSE-vs-bpp rate-distortion curve with per-point annotations."""
    plt.figure(figsize=(10, 6))
    plt.plot(rate_list, distortion_list, marker="o", linestyle="-", color="b")
    if labels is not None:
        for i, lab in enumerate(labels):
            plt.text(rate_list[i] + 0.05, distortion_list[i] + 0.05,
                     f"{label_prefix}={lab}", fontsize=9, ha="left", va="bottom")
    plt.xlabel("Rate (Bits per Pixel)", loc="right")
    plt.ylabel("Distortion (MSE)", loc="top")
    plt.title(title)
    plt.grid(True)
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
