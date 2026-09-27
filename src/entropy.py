"""Unary entropy coding of quantized coefficients.

A non-negative integer ``v`` is coded as ``v`` ones followed by a terminating
zero (``'1' * v + '0'``). Negative values use the same magnitude code with a
trailing ``'-'`` sign marker. This simple variable-length scheme is not an
optimal entropy coder, but its total code length gives a usable bit-rate
estimate.
"""

import numpy as np


def unary_encode(zigzag_result):
    """Encode a sequence of integers as a list of unary code strings."""
    return ["1" * v + "0" if v >= 0 else "1" * -v + "0-" for v in np.asarray(zigzag_result).tolist()]


def unary_decode(compressed_image):
    """Inverse of :func:`unary_encode`."""
    return np.array([-(len(code) - 2) if code.endswith("-") else len(code) - 1
                     for code in compressed_image])


def count_bits(compressed):
    """Total number of characters (bits) across a list of unary codes."""
    return sum(map(len, compressed))


def unary_length(values, axis=None):
    values = np.asarray(values)
    n = values.size if axis is None else int(np.prod([values.shape[a] for a in axis]))
    return np.abs(values).sum(axis=axis) + n + (values < 0).sum(axis=axis)
