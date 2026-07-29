"""Single-channel compress / decompress orchestration.

Both project pipelines share the same tail: (optional DCT) -> quantize ->
zig-zag scan -> unary encode, and its exact inverse. The only differences are
whether a DCT is applied and the block size of the zig-zag scan:

* Block-DCT JPEG pipeline: ``use_dct=True``, ``block_size=8``.
* Subband compression pipeline: ``use_dct=False``, ``block_size=64``.
"""

from .dct import apply_2d_dct, apply_2d_idct
from .quantization import quantize, dequantize
from .zigzag import zigzag, inverse_zigzag
from .entropy import unary_encode, unary_decode


def image_compress(image, quant_table, QP, use_dct=True):
    """Compress a single 2-D channel into a list of unary codes.

    Parameters
    ----------
    image : ndarray, 2-D
        One channel of one block / subband.
    quant_table : ndarray
        Quantization table matching ``image``'s shape.
    QP : float
        Quality parameter scaling the quantization table.
    use_dct : bool
        Apply a 2-D DCT before quantization (block-DCT JPEG). Set ``False`` for
        the subband pipeline, which quantizes the spatial-domain subband.
    """
    if use_dct:
        image = apply_2d_dct(image)
    image = quantize(image, quant_table, QP)
    zigzag_result = zigzag(image)
    return unary_encode(zigzag_result)


def image_decompress(compressed_image, quant_table, QP, use_dct=True, block_size=8):
    """Inverse of :func:`image_compress`.

    ``block_size`` must equal the side length of the quantized grid (8 for the
    block-DCT pipeline, 64 for the subband pipeline).
    """
    zigzag_result = unary_decode(compressed_image)
    dezigzagged = inverse_zigzag(zigzag_result, size=block_size)
    dequantized = dequantize(dezigzagged, quant_table, QP)
    if use_dct:
        return apply_2d_idct(dequantized)
    return dequantized
