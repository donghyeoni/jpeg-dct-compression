"""Custom sum/difference (Haar-like) subband decomposition.

Each 1-D step pairs adjacent samples ``a, b`` into a *sum* channel ``a + b`` and
a *difference* channel ``a - b``. Applying this horizontally then vertically
(or vice versa) and recursing produces a multi-level subband pyramid. The
inverse rebuilds the samples via ``(sum + diff) / 2`` and ``(sum - diff) / 2``.

These operations are ports of the loop-based routines from the original
Project2 notebooks, preserved as-is (integer arithmetic, per-channel loops).
"""

import numpy as np


def process_horizontal(img):
    """Horizontal sum/difference split.

    Returns ``(I_A, I_B)`` where ``I_A`` holds pairwise sums and ``I_B`` holds
    pairwise differences along the width axis. Input shape ``(H, W, C)`` ->
    two arrays of shape ``(H, W // 2, C)``.
    """
    H, W, C = img.shape
    I_A = np.zeros((H, W // 2, C), dtype=np.int32)
    I_B = np.zeros((H, W // 2, C), dtype=np.int32)
    for c in range(C):
        for y in range(H):
            for x in range(0, W, 2):
                I_A[y, x // 2, c] = img[y, x, c] + img[y, x + 1, c]
                I_B[y, x // 2, c] = img[y, x, c] - img[y, x + 1, c]
    return I_A, I_B


def process_vertical(img):
    """Vertical sum/difference split.

    Returns ``(I_C, I_D)`` where ``I_C`` holds pairwise sums and ``I_D`` holds
    pairwise differences along the height axis. Input shape ``(H, W, C)`` ->
    two arrays of shape ``(H // 2, W, C)``.
    """
    H, W, C = img.shape
    I_C = np.zeros((H // 2, W, C), dtype=np.int32)
    I_D = np.zeros((H // 2, W, C), dtype=np.int32)
    for c in range(C):
        for y in range(0, H, 2):
            for x in range(W):
                I_C[y // 2, x, c] = img[y, x, c] + img[y + 1, x, c]
                I_D[y // 2, x, c] = img[y, x, c] - img[y + 1, x, c]
    return I_C, I_D


def restore_horizontal(I_A, I_B):
    """Inverse of :func:`process_horizontal`."""
    H, W_half, C = I_A.shape
    W = W_half * 2
    restored = np.zeros((H, W, C), dtype=np.int32)
    for c in range(C):
        for y in range(H):
            for x in range(W_half):
                restored[y, 2 * x, c] = (I_A[y, x, c] + I_B[y, x, c]) // 2
                restored[y, 2 * x + 1, c] = (I_A[y, x, c] - I_B[y, x, c]) // 2
    return restored


def restore_vertical(I_C, I_D):
    """Inverse of :func:`process_vertical`."""
    H_half, W, C = I_C.shape
    H = H_half * 2
    restored = np.zeros((H, W, C), dtype=np.int32)
    for c in range(C):
        for x in range(W):
            for y in range(H_half):
                restored[2 * y, x, c] = (I_C[y, x, c] + I_D[y, x, c]) // 2
                restored[2 * y + 1, x, c] = (I_C[y, x, c] - I_D[y, x, c]) // 2
    return restored


def _decompose_1d(image, step, levels):
    """Apply a single-direction transform ``step`` recursively ``levels`` times.

    ``step`` is either :func:`process_horizontal` or :func:`process_vertical`.
    Returns a flat list of ``2 ** levels`` subbands in the traversal order used
    by the original notebooks (breadth-first over the sum/difference tree).
    """
    subbands = [image]
    for _ in range(levels):
        next_level = []
        for band in subbands:
            lo, hi = step(band)
            next_level.extend([lo, hi])
        subbands = next_level
    return subbands


def decompose(image, levels=3, order="vertical_first"):
    """Full 2-D multi-level sum/difference decomposition.

    Applies ``levels`` recursions in one direction, then ``levels`` recursions
    in the other for every resulting subband. With ``levels=3`` this yields
    ``8 * 8 = 64`` subbands, matching the notebook pipeline.

    Parameters
    ----------
    image : ndarray, shape (H, W, C)
    levels : int
        Number of recursion levels per direction.
    order : {"vertical_first", "horizontal_first"}
        Which direction is decomposed first.

    Returns
    -------
    list of ndarray
        ``(2 ** levels) ** 2`` subband images.
    """
    if order == "vertical_first":
        first, second = process_vertical, process_horizontal
    elif order == "horizontal_first":
        first, second = process_horizontal, process_vertical
    else:
        raise ValueError("order must be 'vertical_first' or 'horizontal_first'")

    first_bands = _decompose_1d(image, first, levels)
    result = []
    for band in first_bands:
        result.extend(_decompose_1d(band, second, levels))
    return result


def _reconstruct_1d(subbands, restore_step):
    """Inverse of :func:`_decompose_1d` for a single direction."""
    bands = list(subbands)
    while len(bands) > 1:
        merged = []
        for i in range(0, len(bands), 2):
            merged.append(restore_step(bands[i], bands[i + 1]))
        bands = merged
    return bands[0]


def reconstruct(subbands, levels=3, order="vertical_first"):
    """Inverse of :func:`decompose`.

    Parameters
    ----------
    subbands : list of ndarray
        Output of :func:`decompose` (must be ``(2 ** levels) ** 2`` bands).
    levels : int
    order : {"vertical_first", "horizontal_first"}
        Must match the order used for decomposition.
    """
    if order == "vertical_first":
        first_restore, second_restore = restore_vertical, restore_horizontal
    elif order == "horizontal_first":
        first_restore, second_restore = restore_horizontal, restore_vertical
    else:
        raise ValueError("order must be 'vertical_first' or 'horizontal_first'")

    group = 2 ** levels
    merged_first = []
    for i in range(0, len(subbands), group):
        merged_first.append(_reconstruct_1d(subbands[i:i + group], second_restore))
    return _reconstruct_1d(merged_first, first_restore)
