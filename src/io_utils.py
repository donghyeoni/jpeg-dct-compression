"""Image loading helpers (replaces the Colab/Drive paths from the notebooks)."""

import os

import cv2
import numpy as np


def load_image(path, color_space="rgb"):
    """Load ``lena.bmp`` (or any image) and convert to a float32 array.

    Parameters
    ----------
    path : str
        Path to the image file supplied by the user (see the Dataset section of
        the README).
    color_space : {"rgb", "yuv", "gray"}
        Target color space. ``"gray"`` returns an ``int32`` ``(H, W, 1)`` array;
        the others return ``float32`` ``(H, W, 3)`` arrays.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Image not found: {path}. Place your own lena.bmp under data/ "
            "(the image is not redistributed with this repository)."
        )
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Failed to read image: {path}")

    if color_space == "rgb":
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32)
    if color_space == "yuv":
        return cv2.cvtColor(image, cv2.COLOR_BGR2YUV).astype(np.float32)
    if color_space == "gray":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.int32)
        h, w = gray.shape
        return gray.reshape(h, w, 1)
    raise ValueError("color_space must be 'rgb', 'yuv', or 'gray'")
