"""Rate-distortion sweeps, RD-curve plotting, and optimal-QP search."""

import os

import numpy as np
import matplotlib.pyplot as plt

from .jpeg_codec import image_compress, image_decompress
from .entropy import count_bits, unary_length
from .metrics import calculate_mse, calculate_list_mse

TOTAL_PIXELS = 512 * 512  # rate is normalized by the full-image pixel count


def sweep_blocks(blocks, luminance_table, chrominance_table, QP_values,
                 use_dct=True, block_size=8, reconstruct_fn=None, reference=None):
    """Sweep a list of QP values over a list of 3-channel blocks/subbands.

    For each QP, every block's Y channel is coded with ``luminance_table`` and
    its U, V channels with ``chrominance_table``. Rate is total bits divided by
    ``512 * 512``.

    Distortion is computed in one of two ways:

    * If ``reconstruct_fn`` and ``reference`` are given, the restored blocks are
      reassembled into a full image via ``reconstruct_fn`` and compared to
      ``reference`` with MSE (both experiment pipelines).
    * Otherwise, the MSE is taken directly between the stacks of original and
      restored blocks.

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
                    alpha=0.05, beta=0.95, block_size=64):
    """Per-subband QP that minimizes ``cost = alpha * MSE + beta * rate``.

    Searches ``qp_range`` for a single channel index (0=Y, 1=U, 2=V) across all
    subbands. Returns an array of the optimal QP per subband.
    """
    qps = np.array(list(qp_range))
    steps = quant_table * qps[:, None, None]
    optimal = np.zeros(len(subbands))
    for j, sub in enumerate(subbands):
        band = sub[:, :, channel]
        quantized = np.round(band / steps).astype(int)
        restored = quantized.astype(float) * steps
        mse = ((band - restored) ** 2).mean(axis=(1, 2))
        rate = unary_length(quantized, axis=(1, 2)) / (block_size * block_size)
        optimal[j] = qps[np.argmin(alpha * mse + beta * rate)]
    return optimal


def plot_rd_curve(rate_list, distortion_list, labels=None, label_prefix="QP",
                  title="Rate-Distortion Curve", save_path=None):
    """Plot an MSE-vs-bpp rate-distortion curve with per-point annotations.

    If ``save_path`` is given the figure is written there; otherwise it is
    shown interactively.
    """
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
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
