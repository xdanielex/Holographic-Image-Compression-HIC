# holocomp — Rate–Distortion Optimised Image Codec

**Developer:** Daniele Rufo
**Year:** 2026

A dependency-free C++17 still-image codec built on rate–distortion optimised block
coding: quadtree partitioning, 35 directional intra prediction modes, adaptive
DCT-II/DST-VII selection, trellis quantisation and a context-adaptive binary
arithmetic coder.

**Current release: v6u** (`HCMPv6`) — one binary, with an optional archival mode
for scanned documents behind a single flag. On the Kodak test set it reduces bitrate
against JPEG by **37.1 % at equal PSNR** and **32.3 % at equal SSIM** — level with
WebP method 6 in PSNR (−36.6 % on the same measurement), ahead of WebP in SSIM,
and still behind AVIF.

v5 remains in the repository as `src/holocomp5.cpp`; its bitstream is *not*
compatible with v6.

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

## What is new in v6

Four tools were added after v5, each accepted or rejected on measured BD-rate
against a frozen baseline.

| tool | BD-rate vs v5 | status |
| :--- | ------------: | :----- |
| **32×32 coding units** | **−4.60 %** | default |
| **Cross-component chroma prediction (CCLM)** | −1.2 to −2.5 % | default |
| **Independently decodable slices** | −0.1 % | default (auto) |
| Multi-model CCLM (MMLM) | +0.1 to +0.6 % | opt-in `--mmlm` |
| Reference sample smoothing | −0.3 to +0.15 % | opt-in `--refsmooth` |
| PDPC | +0.7 to +1.6 % | **removed** |

**CCLM.** Chroma predicted as `a·Y + b` from the collocated reconstructed luma,
with `a,b` fitted by least squares on causal neighbours by both encoder and
decoder — only a one-bin flag is transmitted. Slope clamped to ±2.

**Slices.** Horizontal bands with reset contexts and their own arithmetic
streams, decoded in parallel. Luma and chroma get separate streams per slice so
no thread has to replay a band to reposition its coder. Default is adaptive:
≥16 CU rows per band, capped at 4.

**32×32 units.** The quadtree starts at 32×32; transforms, quantisation tables,
zigzag scans and per-size contexts were extended to a fourth size class. Largest
single gain, positive on all eight Kodak images — though neutral-to-negative on
dense foliage (+0.58 % on the `foresta` test image), where large partitions
cannot capture high-frequency texture.

**SIMD.** SSE2 kernels for the transforms, the horizontal deblocking pass and
the colour transform. SSE2 is baseline on x86-64, so there is no runtime
dispatch; a scalar fallback compiles on other targets.

Three of these are standard in modern video codecs. MMLM, PDPC and reference
smoothing did not pay for themselves at the block sizes and context granularity
used here, and are reported as negative results rather than quietly dropped.

## Measured performance

Bjøntegaard delta-rate against JPEG, averaged over the Kodak set.
**Negative is better** (less bitrate for the same quality).

| Codec                    | BD-rate (PSNR) | BD-rate (SSIM) |
| :----------------------- | -------------: | -------------: |
| **holocomp v6u**         |    **−36.8 %** |    **−30.5 %** |
| WebP (method 6)          |        −36.4 % |        −24.1 % |
| AVIF (speed 6)           |        −46.4 % |        −40.6 % |

v6 is level with WebP in PSNR — the 0.4-point difference is well inside the
spread of an eight-image set — and **6.4 points ahead in SSIM**. AVIF keeps a
clear advantage on both metrics. All three curves were measured over a PSNR
range that overlaps throughout, so the delta-rates are directly comparable.

Mean PSNR (dB) at matched bitrate:

| bpp  | JPEG  | v6    | WebP  | AVIF  |
| :--- | ----: | ----: | ----: | ----: |
| 0.25 | 29.49 | 30.77 | 30.65 | 28.48 |
| 0.50 | 28.49 | 30.52 | 30.41 | 31.19 |
| 1.00 | 31.55 | 33.74 | 33.74 | 34.59 |
| 1.50 | 33.64 | 35.06 | 36.09 | 36.80 |

### Speed and runtime

1920×1280 image, two cores, decode times exclude file writing for every codec:

| codec               | encode  | decode |
| :------------------ | ------: | -----: |
| v6 `--speed 0`      | 2244 ms |  79 ms |
| **v6 `--speed 4`**  |  551 ms |  79 ms |
| WebP (method 6)     |  587 ms |  34 ms |
| JPEG                |   18 ms |  10 ms |

Encoding is multithreaded (wavefront over coding units, **bit-exact** — the
thread count never changes the output). The decoder threads its slices, the
deblocking filter and the colour-conversion pass; the arithmetic stage is
inherently serial.

| threads | encode (2.46 MP) | speedup |
| :------ | ---------------: | ------: |
| 1       | 4.64 s           |  1.00×  |
| 2       | 2.50 s           |  1.85×  |

93 % parallel efficiency on two cores.

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

Matched PSNR on a 2.46 Mpixel photograph of dense foliage — a worst case for any
transform coder. Quality parameters bisected to hit each target.

| PSNR    | v6 bytes | ratio  | vs JPEG | vs WebP m6 |
| :------ | -------: | -----: | ------: | ---------: |
| 24.0 dB |  192 242 | 38.4:1 | −19.7 % |    +3.3 %  |
| 25.5 dB |  275 897 | 26.7:1 | −21.6 % |    +8.5 %  |
| 27.0 dB |  372 107 | 19.8:1 | −19.9 % |   +10.1 %  |
| 28.0 dB |  444 637 | 16.6:1 | −19.3 % |   +13.2 %  |

On this image v6 produces **about 20 % fewer bytes than JPEG** at equal quality
and trails WebP by 3–13 %. Dense foliage is where the codec is weakest: its
BD-rate here is far behind the Kodak average, because high-frequency texture
defeats large partitions and directional prediction alike.

Rate is always reported as `R = 8B / (W·H)` bits per pixel, where `B` is the coded
file size. Ratios of the form *(source file size)/(coded size)* are not used: when
the source is a PNG or a RAW scan such a ratio measures the source container, not
the codec, and is not comparable across experiments.

---

## Archival mode for scanned documents

The codec ships a single switch, **off by default**. With it off the encoder is
**byte-for-byte identical** to plain v6 at every quality (verified 50→100).

```bash
holocomp6u encode --in scan.png --out scan.hc6 --doc            # archival, quality 97
holocomp6u encode --in scan.png --out scan.hc6 --archival -q 99
holocomp6u encode --in photo.png --out photo.hc6 --quality 50   # normal, unchanged
```

**What it changes:** 4:4:4 chroma above quality 95, and a quantisation step floor
relaxed from 1.0 to 0.25 above quality 96. Both are encoder-side — the chroma
format is already in the header, so archival files decode with the standard
binary. Below ~3 bpp the flag does nothing.

**Why it exists.** Above 3 bpp all three 4:2:0 codecs stop improving: WebP
saturates near 35.9 dB, AVIF near 36.1 dB. On document scans the chroma planes
are not smooth — coloured stamps, ink bleed, ruled lines — so discarding three
quarters of them imposes a hard fidelity ceiling.

Four synthetic 1700×2200 pages at ~200 dpi (running text, numeric table, filled
form with signature, mixed text+photo), degraded with 0.35° rotation, paper
grain, uneven illumination and slight blur. **PSNR at matched file size:**

| bpp | normal | **archival** | WebP | AVIF | JPEG 4:4:4 |
| --: | -----: | -----------: | ---: | ---: | ---------: |
| 1.0 | 33.78 | 33.78 | 33.79 | 33.74 | 33.03 |
| 2.0 | 34.55 | 34.55 | 34.70 | 34.82 | 33.97 |
| 3.0 | 35.36 | **37.08** | 35.58 | 35.48 | 34.64 |
| 4.0 | 35.92 | **37.12** | 35.92 | 35.83 | 35.41 |
| 6.0 | 36.25 | **40.24** | 35.94 | 36.12 | 37.97 |

**+1.5 dB on WebP and AVIF at 3 bpp, +4.1 dB at 6 bpp** — the largest margin the
codec achieves over either anchor on any content class.

### The catch: SSIM

Archival mode wins on PSNR and **loses on SSIM**.

| bpp | normal | archival | WebP | AVIF |
| --: | -----: | -------: | ---: | ---: |
| 3.0 | 0.9831 | 0.9698 | 0.9804 | 0.9885 |
| 4.0 | 0.9925 | 0.9702 | 0.9908 | 0.9946 |
| 6.0 | 0.9969 | **0.9856** | 0.9912 | 0.9999 |

The sub-integer quantisation floor spends bits on coefficients that lower squared
error without adding perceptible structure — the perceptual lambda in reverse.
The two metrics rank the codecs differently here.

**Use it for pixel-accurate retention** — legal archives, OCR masters,
digitisation masters. **Do not use it** for material a person will look at, or
below 3 bpp where it does nothing.

---

## Build

No external dependencies beyond a C++17 compiler. Image I/O uses public-domain
`stb_image`, bundled in `third_party/`.

```bash
# Linux
g++ -O3 -march=x86-64-v2 -std=c++17 -Ithird_party src/holocomp6u.cpp -lm -pthread -o holocomp6u

# Windows (MSVC)
cl /O2 /std:c++17 /EHsc /Ithird_party src\holocomp6u.cpp /Fe:holocomp6u.exe

# Windows, cross-compiled from Linux
pip install ziglang
python3 -m ziglang c++ -O2 -std=c++17 -Ithird_party \
    -Wno-nullability-completeness -target x86_64-windows-gnu \
    src/holocomp6u.cpp -o holocomp6u-win-x86_64.exe
```

Prebuilt static binaries for Linux and Windows x86-64 are in `release/bin/`.
No DLLs, no OpenCV, no FFmpeg, no external `zstd` — the previous release required
all of these; this one requires none.

---

## Usage

The **command comes first**, before any option:

```bash
holocomp6u <command> [options]

# encode
holocomp6u encode --in image.png --out file.hc6 --quality 60

# decode
holocomp6u decode --in file.hc6 --out reconstructed.png

# encode, decode and report bpp / PSNR / SSIM in one pass
holocomp6u roundtrip --in image.png --out file.hc6 --quality 60 --recon out.png

# decoder robustness check
holocomp6u fuzz --in file.hc6 --iters 3000

# help
holocomp6u --help
```

Input may be PNG, JPEG, BMP, TGA or GIF. The compressed file is `.hc6`;
reconstructed images are always written as PNG, so `--out out.jpg` will not
produce a JPEG — use `--recon out.png`.

Omitting the command is the most common mistake:

```
holocomp6u --in foresta.jpg --out out.jpg --quality 60      # wrong, no command
holocomp6u roundtrip --in foresta.jpg --out foresta.hc6 \
          --quality 60 --recon rec.png                     # right
```

### Parameters

| Parameter   | Default | Description                                        |
| :---------- | :------ | :------------------------------------------------- |
| `--quality` | 50      | Rate control, 1–100. The only knob you normally need. |
| `--maxsize` | 32      | Quadtree root size (4, 8, 16 or 32).               |
| `--minsize` | 4       | Smallest leaf size.                                |
| `--lambda`  | 1.0     | Scale factor on the RD Lagrangian.                 |
| `--threads` | 0       | 0 = all cores, 1 = serial. Does not change output. |
| `--speed`   | 0       | 0 = reference quality, 1–4 progressively faster.   |
| `--slices`  | 0       | 0 = auto, N = fixed decodable bands.               |
| `--no-cclm` | off     | Disable cross-component chroma prediction.         |
| `--mmlm`    | off     | Multi-model CCLM (measured as a net loss).         |
| `--archival`| off     | Document mode: 4:4:4 + finer quant above q95.      |
| `--doc`     | off     | `--archival` with quality 97.                      |

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

`.hc6` files begin with a header — magic `HCMPv6`, flags, quadtree bounds,
dimensions, quality, slice count — followed by two length tables (luma and chroma,
one entry per slice) and then the arithmetic-coded slice payloads. Roughly 250
adaptive contexts are used; **no probability or quantisation tables are
transmitted.**

The format is **not compatible with v5**: `.hc5` files cannot be read by v6 and
vice versa.

Every decoded index and magnitude is bounds-checked, including the slice table.
Fuzzing with 2 500 mutated bitstreams (truncations, bit flips, multi-byte
corruption) produced clean rejections and **zero crashes**; AddressSanitizer runs
clean. Encoder and decoder reconstructions are byte-identical across nine
image × quality combinations.

---

## Repository layout

```
src/holocomp6u.cpp    current codec (~1400 lines, single translation unit)
src/holocomp6.cpp     v6 without archival mode
src/holocomp5.cpp     previous release, kept for reference
src/holocomp.cpp      v2 codec + legacy v1 sparse-coding pipeline
src/holocomp3.cpp     v3
src/holocomp4.cpp     v4
release6u/            prebuilt Linux + Windows executables, paper, this README
paper/                paper generator + 8 vector figures
bench/                benchmark harness and raw JSON results
third_party/          stb_image, stb_image_write (public domain)
```

Reproducing the published numbers:

```bash
python3 bench/bench5.py      # 976 rate–distortion points
python3 bench/analyze5.py    # BD-rate tables
python3 bench/bench_v1_sweep.py   # 2 736-configuration v1 sweep
```

---

## Documentation

The current paper — `release6/holocomp_v6u_paper.pdf`, 8 pages — contains the full
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

- The Windows executable is cross-compiled with zig and has been confirmed
  running on Windows 11. It is built from the same source as the Linux binary.
- Console output uses UTF-8; on legacy Windows codepages a few characters in the
  banner may render incorrectly. This is cosmetic.
- Evaluation covers eight Kodak images — natural photography only. Behaviour on
  documents, synthetic graphics and screenshots is untested.
- AVIF remains ahead by roughly 10 BD-rate points on both metrics.
- Decoding is ~2.2× slower than WebP (79 ms vs 34 ms on 2.46 MP). Slices,
  deblocking and the colour-conversion pass are threaded and the hot loops use
  SSE2, but the arithmetic decoder itself is serial by construction.
- Performance is uneven across content: level with WebP on the Kodak average,
  3–13 % behind on dense foliage, and ahead of both anchors on document scans
  above 3 bpp in archival mode.
- Archival mode trades SSIM for PSNR and is off by default for that reason.
- The document corpus is synthetic (rendered pages plus scan effects), not real
  scanner output.
- SIMD is SSE2 only. No AVX2 path, no runtime dispatch.
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
