"""Distortion metrics shared across all pipelines."""

import numpy as np


def calculate_mse(original, restored):
    """Mean squared error between two arrays of identical shape."""
    original = np.asarray(original)
    restored = np.asarray(restored)
    return np.mean((original - restored) ** 2)


def calculate_list_mse(list1, list2):
    """Mean squared error between two lists of arrays (stacked first)."""
    list1 = np.array(list1)
    list2 = np.array(list2)
    return np.mean((list1 - list2) ** 2)
