# holocomp — Rate–Distortion Optimised Image Codec

**Developer:** Daniele Rufo
**Year:** 2026

A dependency-free C++17 still-image codec built on rate–distortion optimised block
coding: quadtree partitioning, 35 directional intra prediction modes, adaptive
DCT-II/DST-VII selection, trellis quantisation and a context-adaptive binary
arithmetic coder.

On the Kodak test set it reduces bitrate against JPEG by **33.6 % at equal PSNR**
and **32.3 % at equal SSIM** — within two points of WebP in PSNR, ahead of WebP in
SSIM, and behind AVIF.

---

## Project history and scope

This repository began as *Holographic Image Compression via Sparse Representation
and Orthogonal Pursuit* (HIC), which decomposed images with Orthogonal Matching
Pursuit over a Kronecker-product DCT dictionary. That design is preserved in this
repository as version 1 and is still buildable, but it **has been superseded**.

Two findings drove the redesign, both documented in the current paper:

1. **The dictionary was orthonormal, not overcomplete.** For `D = C ⊗ C` with `C`
   an orthonormal DCT matrix, `DᵀD = I` holds exactly (measured deviation
   `1.2×10⁻⁷`, single-precision round-off). OMP over such a dictionary is
   *provably identical* to keeping the K largest transform coefficients — the
   greedy pursuit is redundant. Replacing it with `Dᵀy` plus a partial sort gives
   **byte-identical output 8× to 30× faster**, confirmed across 2 736
   configurations.

2. **The rate–distortion performance was far below JPEG.** Swept over all four
   tuning parameters, the best-case convex envelope of the v1 design sits at
   **+787.9 % BD-rate** against JPEG: it needs roughly 10× to 20× the bitrate of
   JPEG for equal quality.

Version 5 abandons the sparse-coding formulation entirely. The v1 sources remain
for reproducibility of the negative result.

---

## Measured performance

Bjøntegaard delta-rate against JPEG, averaged over the Kodak set.
**Negative is better** (less bitrate for the same quality).

| Codec                          | BD-rate (PSNR) | BD-rate (SSIM) |
| :----------------------------- | -------------: | -------------: |
| v1 (sparse coding, best tuning)|       +787.9 % |       +688.3 % |
| v2 (YCbCr, per-band quant.)    |         −2.2 % |         −3.1 % |
| v3 (run-length, intra, RDOQ)   |        −14.8 % |        −11.0 % |
| v4 (arithmetic coder, quadtree)|        −28.1 % |        −22.1 % |
| **v5 (current)**               |    **−33.6 %** |    **−32.3 %** |
| WebP (method 6)                |        −35.6 % |        −26.5 % |
| AVIF (speed 6)                 |        −45.3 % |        −40.6 % |

Mean PSNR (dB) at matched bitrate:

| bpp  | JPEG  | v4    | v5    | WebP  | AVIF  |
| :--- | ----: | ----: | ----: | ----: | ----: |
| 0.25 | 29.49 | 27.36 | 27.61 | 32.05 | 31.53 |
| 0.50 | 28.52 | 30.02 | 30.40 | 33.42 | 31.30 |
| 1.00 | 31.61 | 33.20 | 33.67 | 33.88 | 34.65 |
| 1.50 | 33.72 | 35.45 | 35.91 | 36.20 | 36.87 |

Encoding is multithreaded (wavefront over coding units). Decoding threads the
deblocking filter and the colour-conversion pass; the entropy stage is serial.

The wavefront is **bit-exact**: `--threads N` produces byte-identical output for
every N, verified across 3 images x 4 quality levels. Intra prediction of a CU
depends on the row above and the column to the left, so anti-diagonals can run
concurrently while entropy coding stays serial in raster order.

| threads | encode (2.46 MP) | speedup |
| :------ | ---------------: | ------: |
| 1       | 4.64 s           |  1.00x  |
| 2       | 2.50 s           |  1.85x  |

Measured on a 2-core sandbox; 93 % parallel efficiency.

### Speed presets

`--speed` trades a little compression for encoding time. Level 0 is the
reference and is bit-exact with the original exhaustive search; higher levels
add SATD-gap candidate pruning, early split termination, two-pass trellis
quantisation, a coarse-to-fine angular scan and a quadtree depth cap.

| speed | encode (2.46 MP, 2 cores) | size   | PSNR     |
| :---- | ------------------------: | -----: | -------: |
| 0     | 2244 ms                   | ref    | ref      |
| 2     | 1289 ms                   | +1.6 % | +0.02 dB |
| 3     | 1083 ms                   | +1.4 % | -0.06 dB |
| 4     |  551 ms                   | +2.6 % | -0.11 dB |

### Equal-quality comparison

Matched PSNR on a 2.46 Mpixel photograph of dense foliage (worst case for a
transform coder). Quality parameters bisected to hit each target; decode times
exclude file writing for every codec.

**At 25.5 dB:**

| codec          | ratio      | reduction | encode  | decode |
| :------------- | ---------: | --------: | ------: | -----: |
| v5 `--speed 0` | 26.8:1     | 96.26 %   | 2180 ms | 110 ms |
| v5 `--speed 4` | 25.5:1     | 96.07 %   |  521 ms | 112 ms |
| WebP method 6  | **29.0:1** | 96.55 %   |  490 ms |  37 ms |
| WebP method 4  | 27.8:1     | 96.40 %   |  227 ms |  37 ms |
| JPEG           | 20.9:1     | 95.23 %   |   17 ms |  11 ms |

Across targets from 24 to 28 dB, `--speed 4` relative to the anchors:

| PSNR   | bytes vs JPEG | bytes vs WebP m6 | encode vs WebP m6 | decode vs WebP m6 |
| :----- | ------------: | ---------------: | ----------------: | ----------------: |
| 24.0   | -14.0 %       | +10.6 %          | 1.30x             | 3.02x             |
| 25.5   | -17.8 %       | +13.9 %          | 1.06x             | 3.06x             |
| 27.0   | -16.8 %       | +14.3 %          | 1.06x             | 3.11x             |
| 28.0   | -16.2 %       | +17.6 %          | **0.91x**         | 3.15x             |

The codec consistently beats JPEG by 14-18 % in size at equal quality and
trails WebP by 11-18 %. Encoding is on par with WebP method 6 and faster at
high quality; decoding remains a stable 3x behind.

Rate is always reported as `R = 8B / (W·H)` bits per pixel, where `B` is the coded
file size. Ratios of the form *(source file size)/(coded size)* are not used: when
the source is a PNG or a RAW scan such a ratio measures the source container, not
the codec, and is not comparable across experiments.

---

## Build

No external dependencies beyond a C++17 compiler. Image I/O uses public-domain
`stb_image`, bundled in `third_party/`.

```bash
# Linux
g++ -O2 -std=c++17 -Ithird_party src/holocomp5.cpp -lm -o holocomp5

# Windows (MSVC)
cl /O2 /std:c++17 /Ithird_party src\holocomp5.cpp /Fe:holocomp5.exe

# Windows, cross-compiled from Linux
pip install ziglang
python3 -m ziglang c++ -O2 -std=c++17 -Ithird_party \
    -Wno-nullability-completeness -target x86_64-windows-gnu \
    src/holocomp5.cpp -o holocomp5-win-x86_64.exe
```

Prebuilt static binaries for Linux and Windows x86-64 are in `release/bin/`.
No DLLs, no OpenCV, no FFmpeg, no external `zstd` — the previous release required
all of these; this one requires none.

---

## Usage

The **command comes first**, before any option:

```bash
holocomp5 <command> [options]

# encode
holocomp5 encode --in image.png --out file.hc5 --quality 60

# decode
holocomp5 decode --in file.hc5 --out reconstructed.png

# encode, decode and report bpp / PSNR / SSIM in one pass
holocomp5 roundtrip --in image.png --out file.hc5 --quality 60 --recon out.png

# decoder robustness check
holocomp5 fuzz --in file.hc5 --iters 3000

# help
holocomp5 --help
```

Input may be PNG, JPEG, BMP, TGA or GIF. The compressed file is `.hc5`;
reconstructed images are always written as PNG, so `--out out.jpg` will not
produce a JPEG — use `--recon out.png`.

Omitting the command is the most common mistake:

```
holocomp5 --in foresta.jpg --out out.jpg --quality 60      # wrong, no command
holocomp5 roundtrip --in foresta.jpg --out foresta.hc5 \
          --quality 60 --recon rec.png                     # right
```

### Parameters

| Parameter   | Default | Description                                        |
| :---------- | :------ | :------------------------------------------------- |
| `--quality` | 50      | Rate control, 1–100. The only knob you normally need. |
| `--maxsize` | 16      | Quadtree root size (4, 8 or 16).                   |
| `--minsize` | 4       | Smallest leaf size.                                |
| `--lambda`  | 1.0     | Scale factor on the RD Lagrangian.                 |
| `--threads` | 0       | 0 = all cores, 1 = serial. Does not change output. |
| `--speed`   | 0       | 0 = reference quality, 1–4 progressively faster.   |

Unlike v1, **block size and coefficient count are not user parameters**. They are
chosen per block by the rate–distortion search, so there is no tuning to get right.

Ablation flags (`--no-angular`, `--no-dst`, `--no-richctx`, `--no-perc`,
`--no-pred`, `--no-rdoq`, `--no-deblock`, `--no-quadtree`) exist to reproduce the
paper's ablation table. All tools are enabled by default.

### Legacy v1 codec

```bash
holocomp v1 --patch 8 --k 12 --quant 10 --lowfreq 64 [--proj] [--recon]
```

`--proj` substitutes the projection for OMP; the output is byte-identical and the
encoder is an order of magnitude faster. Note that the parameter set recommended
in the original documentation (`--patch 20`) never appears on the optimal envelope
across the 2 736-configuration sweep; `--patch 8` dominates.

---

## Bitstream

`.hc5` files begin with a 26-byte header — magic `HCMPv5`, flags, quadtree bounds,
dimensions, quality — followed by a single arithmetic-coded payload carrying Y, Cb
and Cr. Roughly 250 adaptive contexts are used; **no probability or quantisation
tables are transmitted.**

Every decoded index and magnitude is bounds-checked. Fuzzing with 3 000 mutated
bitstreams (truncations, bit flips, multi-byte corruption) produced 58 successful
decodes, 2 942 clean rejections and **zero crashes**.

---


## Documentation

The current paper — `holocomp.pdf`, 6 pages — contains the full
mathematical treatment, including the formal proof of OMP/thresholding equivalence,
the comparison against JPEG, WebP and AVIF, and the per-tool ablation.

### Earlier publication (Zenodo)

The original HIC architecture is archived on Zenodo:

👉 **[Read the original paper on Zenodo](https://zenodo.org/records/20304000)**

> Rufo, D. (2026). *Holographic Image Compression via Sparse Representation and
> Orthogonal Pursuit in Transformed Spaces.* Zenodo.
> https://doi.org/10.5281/zenodo.20304000

That paper describes version 1. Its central claims — a 28:1 ratio at 35.85 dB, and
a coding gain from overcomplete sparse representation — are **not supported by the
measurements in this repository**. 28:1 is attainable, but at 22.7 dB; reaching
36 dB with the v1 design requires more than 2 bpp, i.e. a ratio below 12:1. See
Sections II and VII of the current paper.

---

## Known limitations

- Evaluation covers eight Kodak images — natural photography only. Behaviour on
  documents, synthetic graphics and screenshots is untested.
- AVIF remains ahead by roughly 12 BD-rate points on both metrics.
- Decoding is ~3× slower than WebP (112 ms vs 36 ms on 2.46 MP). Deblocking and
  the fused chroma-upsample/colour-conversion pass are threaded, but the
  arithmetic stream itself is inherently serial: further gains would require
  slicing the bitstream, which changes the format and costs a little
  compression.
- The transforms are scalar C++ with autovectorisation hints; no hand-written
  SIMD kernels.
- No progressive decode, no alpha channel.

---

## License and restrictions

- Released for demonstration and academic evaluation purposes.
- Commercial use, redistribution and reverse engineering are prohibited.
- For commercial licensing or custom implementations: xdaniele.rufox@gmail.com

`third_party/stb_image.h` and `stb_image_write.h` are public domain and carry
their own terms.

---

### Support my research 🚀

If you find this project useful for your benchmarks or academic evaluation,
consider supporting my independent research:

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/xdanielex272)
[![Donate with BTC](https://img.shields.io/badge/Donate-Bitcoin-orange.svg)](#)
[![Donate with USDT](https://img.shields.io/badge/Donate-Tether-green.svg)](#)

* **Bitcoin (BTC):** `bc1q4l9v8welwr6mp4g6uc2t7ex0n274malynq6yqj`
* **Tether (USDT - TRC20):** `TA3m7pqk1mTgZtFQHf7KufAqnaqsN95kPh`
