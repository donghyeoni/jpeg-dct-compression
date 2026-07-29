"""Splitting an image into fixed-size blocks and stitching them back."""

import numpy as np


def split_image_into_blocks(image, block_size):
    """Split ``(H, W, C)`` image into a row-major list of ``(bs, bs, C)`` blocks.

    Assumes ``H`` and ``W`` are exact multiples of ``block_size``.
    """
    blocks = []
    height, width, _ = image.shape
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            blocks.append(image[y:y + block_size, x:x + block_size, :])
    return blocks


def restore_image_from_blocks(block_list, image_size=512, block_size=8, channels=3):
    """Reassemble a row-major list of blocks into a full image.

    The output dtype is ``uint8`` to match the original pipeline.
    """
    restored = np.zeros((image_size, image_size, channels), dtype=np.uint8)
    idx = 0
    for y in range(0, image_size, block_size):
        for x in range(0, image_size, block_size):
            restored[y:y + block_size, x:x + block_size, :] = block_list[idx]
            idx += 1
    return restored
