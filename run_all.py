"""Run all three experiments in one command.

Runs every experiment on the committed 512x512 test image
(``assets/food.jpg``), writing everything to the untracked ``results/``
directory:

* ``results/01_subband_transform.log``
* ``results/02_subband_compression.log`` + ``rd_subband_qp.png`` / ``rd_subband_scaled.png``
* ``results/03_block_dct_jpeg.log``      + ``rd_block_dct.png``

The committed figures under ``assets/`` (shown in the README) were produced
this way; regenerating them yields identical numbers.

Usage
-----
    python run_all.py
"""

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(REPO_ROOT, "results")
IMG_PATH = os.path.join(REPO_ROOT, "assets", "food.jpg")


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

    run("01_subband_transform",
        ["experiments/01_subband_transform.py", "--image", IMG_PATH, "--levels", "3"])
    run("02_subband_compression",
        ["experiments/02_subband_compression.py", "--image", IMG_PATH,
         "--save-dir", OUT_DIR])
    run("03_block_dct_jpeg",
        ["experiments/03_block_dct_jpeg.py", "--image", IMG_PATH,
         "--save-dir", OUT_DIR])

    print("Done. Artifacts under results/.")


if __name__ == "__main__":
    main()
