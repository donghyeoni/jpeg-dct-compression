# Data

This directory is optional: `run_all.py` generates a synthetic test image and
needs no external data.

When run without `--image`, the individual experiment scripts default to the
standard **Lena** test image at `data/lena.bmp` (512x512, color). That image is
**not included** in the repository — supply your own copy and place it here as
`lena.bmp`, or pass any 512x512 color image via `--image`.

See the "Dataset" section of the top-level [README](../README.md) for details
and redistribution caveats.
