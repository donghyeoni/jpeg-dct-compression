"""Quantization and the standard JPEG quantization tables.

Two families of tables are provided:

* The standard 8x8 JPEG luminance / chrominance tables, used by the block-DCT
  pipeline (``src/jpeg_codec.py``).
* Flat "unit" tables (all-ones) at an arbitrary block size, used by the subband
  compression pipeline where the QP alone controls the step size.
"""

import numpy as np

# Standard JPEG 8x8 luminance quantization table (Annex K).
LUMINANCE_QUANT_TABLE = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99],
])

# Standard JPEG 8x8 chrominance quantization table (Annex K).
CHROMINANCE_QUANT_TABLE = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
])


def unit_quant_table(size=64):
    """Flat all-ones quantization table of shape ``(size, size)``.

    Used by the subband pipeline, where the quantization step is set purely by
    the QP scalar rather than a perceptual table.
    """
    return np.ones((size, size))


def quantize(image, quant_table, QP):
    """Divide by (table * QP) and round to the nearest integer."""
    adjusted_quant_table = quant_table * QP
    return np.round(image / adjusted_quant_table).astype(int)


def dequantize(quantized_image, quant_table, QP):
    """Inverse of :func:`quantize` (multiply by table * QP)."""
    adjusted_quant_table = quant_table * QP
    return (quantized_image * adjusted_quant_table).astype(float)
