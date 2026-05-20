# Holographic Image Compression via Sparse Representation and Orthogonal Pursuit (HIC)
**Developer:** Daniele Rufo
**Year:** 2026

---

## 📌 Project Overview
This project introduces an innovative image compression framework based on Compressed Sensing theory and sparse representation. The algorithm utilizes an iterative decomposition via Orthogonal Matching Pursuit (OMP) applied to an overcomplete dictionary generated through Kronecker products of DCT bases.

Unlike traditional methods (such as JPEG), this "holographic" encoder treats the image as a superposition of frequency planes, eliminating blocking artifacts even at extreme compression ratios. It is particularly effective for preserving structural legibility in documents and high-frequency details.

For detailed mathematical foundations, dictionary construction, and performance analysis, please refer to the technical paper: holocomp.pdf.

---

## 💻 System Requirements
* OS: Windows 11 (64-bit).
* Dependencies: 
    * FFmpeg: Must be installed and added to the system PATH (required for decompression).
    * Zstd: zstd.exe must be located in the same directory as the executable.
* Libraries (DLLs): The following files must be present in the program folder:
    * opencv_world455.dll
    * opencv_videoio_ffmpeg455_64.dll

---

### 🌐 Official Academic Publication (Zenodo)
The theoretical foundations and algorithmic specifications of this architecture have been officially published and archived on **Zenodo**:

👉 **[Read the official paper on Zenodo](https://zenodo.org/records/20304000)**

**How to cite:**
Rufo, D. (2026). Holographic Image Compression via Sparse Representation and Orthogonal Pursuit in Transformed Spaces. Zenodo. https://doi.org/10.5281/zenodo.20304000

## 🚀 Usage Examples

### 1. Compression
The program generates a compressed file with the .dan extension.
planecombo_cli.exe compress --input "image.png" --output "compressed_file" --patch 20 --k 10 --quant 10 --lowfreq 32

### 2. Decompression
Reconstructs the original image from the .dan file.
planecombo_cli.exe decompress --input "compressed_file.dan" --output "reconstructed_image.png"

---

## ⚙️ Parameter Guide
The system allows for granular control over the quality/size trade-off:

| Parameter | Recommended | Description |
| :--- | :--- | :--- |
| --patch | 20 | PATCH_SIZE: Decreasing this improves quality but worsens the compression ratio. |
| --k | 10 | K_PLANES: Increasing this improves quality but worsens the compression ratio. |
| --quant | 10 | QUANT_BITS: Increasing this improves precision/quality but results in a larger file. |
| --lowfreq | 64 | LOW_FREQ: Increasing this preserves more chromatic detail but slows down processing and worsens the ratio. |

---

## 📊 Performance
* Baseline Mode: 28:1 compression ratio with a PSNR of 35.85 dB (high fidelity).
* Extreme Compression: Capable of exceeding 150:1 ratios while maintaining structural legibility, ideal for long-term archiving or ultra-low bandwidth transmissions.

---

## ⚠️ License and Restrictions
* Usage: This software is released for demonstration purposes only.
* Restrictions: Commercial use, redistribution, or reverse engineering is strictly prohibited.
* Commercial Licenses: To obtain the full source code or custom implementations, contact: xdaniele.rufox@gmail.com.

---

## 📂 Package Contents
* planecombo_cli.exe: Main application.
* zstd.exe: Compression utility.
* opencv_world455.dll / opencv_videoio_ffmpeg455_64.dll: Runtime libraries.
* holocomp.pdf: Full technical documentation.

---

---

### Support my Research 🚀
If you find this project useful for your benchmarks or academic evaluation, consider supporting my independent research:

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/xdanielex272)
[![Donate with BTC](https://img.shields.io/badge/Donate-Bitcoin-orange.svg)](#)
[![Donate with USDT](https://img.shields.io/badge/Donate-Tether-green.svg)](#)

* **Bitcoin (BTC):** `bc1q4l9v8welwr6mp4g6uc2t7ex0n274malynq6yqj`
* **Tether (USDT - TRC20):** `TA3m7pqk1mTgZtFQHf7KufAqnaqsN95kPh`

---
