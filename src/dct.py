"""2-D DCT / IDCT via separable 1-D transforms (scipy.fftpack)."""

from scipy.fftpack import dct, idct


def apply_2d_dct(image):
    """Orthonormal 2-D DCT of a 2-D array (applied along both axes)."""
    return dct(dct(image.T, norm="ortho").T, norm="ortho")


def apply_2d_idct(coefficients):
    """Orthonormal 2-D inverse DCT (inverse of :func:`apply_2d_dct`)."""
    return idct(idct(coefficients.T, norm="ortho").T, norm="ortho")
