"""Zig-zag scan and its inverse, parameterized by block size.

The block-DCT pipeline scans 8x8 blocks; the subband pipeline scans 64x64
subband images. ``inverse_zigzag`` needs the block size explicitly since it
must allocate the output grid.
"""

from functools import lru_cache

import numpy as np


@lru_cache(maxsize=None)
def _scan_order(rows, cols):
    order_r, order_c = [], []
    for d in range(rows + cols - 1):
        if d % 2 == 1:
            for i in range(max(0, d - cols + 1), min(d + 1, rows)):
                order_r.append(i)
                order_c.append(d - i)
        else:
            for i in range(max(0, d - rows + 1), min(d + 1, cols)):
                order_r.append(d - i)
                order_c.append(i)
    return np.array(order_r), np.array(order_c)


def zigzag(image):
    """Flatten a 2-D array into a 1-D array using a diagonal zig-zag scan."""
    return image[_scan_order(*image.shape)]


def inverse_zigzag(arr, size=8):
    """Rebuild a ``(size, size)`` array from a zig-zag scanned 1-D array."""
    result = np.zeros((size, size), dtype=float)
    result[_scan_order(size, size)] = arr[:size * size]
    return result
