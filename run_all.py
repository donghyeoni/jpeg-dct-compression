"""Regenerate every committed artifact under ``results/`` in one command.

The original notebooks operated on ``lena.bmp``, which is not redistributed
with this repository. To make the pipeline reproducible with **no external
data**, this script synthesizes a deterministic 512x512 test image (fixed seed)
and runs all three experiments on it:

* ``results/input_synthetic.png``   -- the generated 512x512 test image
* ``results/01_subband_transform.log``
* ``results/02_subband_compression.log`` + ``rd_subband_qp.png`` / ``rd_subband_scaled.png``
* ``results/03_block_dct_jpeg.log``      + ``rd_block_dct.png``

The original notebook figures (on lena) are preserved under
``results/notebook_reference/`` for provenance.

Usage
-----
    python run_all.py
"""

import os
import subprocess
import sys

import cv2
import numpy as np

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(REPO_ROOT, "results")


def make_synthetic_image(size=512, seed=0):
    """A deterministic 512x512 BGR image with gradients, shapes and texture.

    Designed to contain both smooth regions and high-frequency detail so the
    rate-distortion behaviour of the codec is meaningful.
    """
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size]
    r = (xx / size * 255).astype(np.float32)
    g = (yy / size * 255).astype(np.float32)
    b = ((np.sin(xx / 16.0) + np.cos(yy / 16.0)) * 63 + 128).astype(np.float32)
    img = np.stack([b, g, r], axis=2)
    # a few solid discs (smooth low-frequency content)
    for _ in range(6):
        cx, cy = rng.integers(0, size, 2)
        rad = int(rng.integers(30, 90))
        color = rng.integers(0, 256, 3).astype(np.float32)
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= rad ** 2
        img[mask] = color
    # fine speckle texture (high-frequency content)
    img += rng.normal(0, 12, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def run(name, args):
    log_path = os.path.join(OUT_DIR, f"{name}.log")
    print(f"  {name} ...")
    proc = subprocess.run([sys.executable] + args, cwd=REPO_ROOT,
                          capture_output=True, text=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(proc.stdout)
        if proc.stderr:
            f.write("\n[stderr]\n" + proc.stderr)
    if proc.returncode != 0:
        print(f"    WARNING: {name} exited with {proc.returncode} (see log)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.environ["MPLBACKEND"] = "Agg"

    img_path = os.path.join(OUT_DIR, "input_synthetic.png")
    cv2.imwrite(img_path, make_synthetic_image())
    print(f"Synthetic input written to {os.path.relpath(img_path, REPO_ROOT)}")

    run("01_subband_transform",
        ["experiments/01_subband_transform.py", "--image", img_path, "--levels", "3"])
    run("02_subband_compression",
        ["experiments/02_subband_compression.py", "--image", img_path,
         "--save-dir", OUT_DIR])
    run("03_block_dct_jpeg",
        ["experiments/03_block_dct_jpeg.py", "--image", img_path,
         "--save-dir", OUT_DIR])

    print("Done. Artifacts under results/.")


if __name__ == "__main__":
    main()
