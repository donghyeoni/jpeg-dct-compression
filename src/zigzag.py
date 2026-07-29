"""Zig-zag scan and its inverse, parameterized by block size.

The block-DCT pipeline scans 8x8 blocks; the subband pipeline scans 64x64
subband images. ``inverse_zigzag`` needs the block size explicitly since it
must allocate the output grid.
"""

import numpy as np


def zigzag(image):
    """Flatten a 2-D array into a 1-D array using a diagonal zig-zag scan."""
    rows, cols = image.shape
    result = []
    for d in range(rows + cols - 1):
        if d % 2 == 1:  # odd diagonal: bottom-up
            for i in range(max(0, d - cols + 1), min(d + 1, rows)):
                result.append(image[i, d - i])
        else:  # even diagonal: top-down
            for i in range(max(0, d - rows + 1), min(d + 1, cols)):
                result.append(image[d - i, i])
    return np.array(result)


def inverse_zigzag(arr, size=8):
    """Rebuild a ``(size, size)`` array from a zig-zag scanned 1-D array."""
    result = np.zeros((size, size), dtype=float)
    index = 0
    for d in range(size + size - 1):
        if d % 2 == 1:  # odd diagonal: bottom-up
            for i in range(max(0, d - size + 1), min(d + 1, size)):
                result[i, d - i] = arr[index]
                index += 1
        else:  # even diagonal: top-down
            for i in range(max(0, d - size + 1), min(d + 1, size)):
                result[d - i, i] = arr[index]
                index += 1
    return result
