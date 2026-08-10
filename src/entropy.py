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
    unary_encoded = []
    for value in zigzag_result:
        if value >= 0:
            unary_encoded.append("1" * value + "0")
        else:
            unary_encoded.append("1" * abs(value) + "0" + "-")
    return unary_encoded


def unary_decode(compressed_image):
    """Inverse of :func:`unary_encode`."""
    decoded = []
    for code in compressed_image:
        if code.endswith("-"):
            decoded.append(-(len(code) - 2))
        else:
            decoded.append(len(code) - 1)
    return np.array(decoded)


def count_bits(compressed):
    """Total number of characters (bits) across a list of unary codes."""
    return sum(len(code) for code in compressed)
