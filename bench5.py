#!/usr/bin/env python3
"""v5 full benchmark + ablation of the 4 new features."""
import io, os, sys, json, glob, subprocess, tempfile
import numpy as np
from PIL import Image
try:
    import pillow_avif  # noqa
    HAVE_AVIF = True
except Exception:
    HAVE_AVIF = False

ROOT = "/home/user/holocomp"
B4, B5 = f"{ROOT}/holocomp4", f"{ROOT}/holocomp5"
TMP = tempfile.mkdtemp(prefix="hc5_")
sys.path.insert(0, f"{ROOT}/bench")
from bench import psnr, ssim


def run_bin(binp, src, q, extra=(), ext="bin"):
    out, rec = f"{TMP}/a.{ext}", f"{TMP}/a.png"
    r = subprocess.run([binp, "roundtrip", "--in", src, "--out", out, "--quality", str(q),
                        "--recon", rec, *extra], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    d = dict(l.split(None, 1) for l in r.stdout.strip().splitlines())
    return int(d["bytes"]), np.array(Image.open(rec).convert("RGB")), float(d["enc_s"]), float(d.get("dec_s", 0))


def runpil(src, fmt, q, **kw):
    im = Image.open(src).convert("RGB")
    b = io.BytesIO(); im.save(b, format=fmt, quality=q, **kw); data = b.getvalue()
    return len(data), np.array(Image.open(io.BytesIO(data)).convert("RGB"))


QS = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95]
V5 = {
    "v5-full": (),
    "v5-no-angular": ("--no-angular",),
    "v5-no-dst": ("--no-dst",),
    "v5-no-richctx": ("--no-richctx",),
    "v5-no-perc": ("--no-perc",),
}

rows = []
for f in sorted(glob.glob(f"{ROOT}/bench/images/*.png")):
    orig = np.array(Image.open(f).convert("RGB"))
    px = orig.shape[0] * orig.shape[1]
    name = os.path.basename(f)
    print("==", name, flush=True)
    for vn, extra in V5.items():
        for q in QS:
            try:
                b, dec, es, ds = run_bin(B5, f, q, extra, "hc5")
                rows.append(dict(image=name, codec=vn, param=q, bytes=b, bpp=b * 8 / px,
                                 psnr=psnr(orig, dec), ssim=ssim(orig, dec), enc_s=es, dec_s=ds))
            except Exception as e:
                print("  fail", vn, q, e)
    for q in QS:
        try:
            b, dec, es, ds = run_bin(B4, f, q, (), "hc4")
            rows.append(dict(image=name, codec="v4", param=q, bytes=b, bpp=b * 8 / px,
                             psnr=psnr(orig, dec), ssim=ssim(orig, dec), enc_s=es, dec_s=ds))
        except Exception as e:
            print("  v4 fail", q, e)
    for q in [10, 20, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95]:
        b, dec = runpil(f, "JPEG", q, optimize=True, subsampling=2)
        rows.append(dict(image=name, codec="jpeg", param=q, bytes=b, bpp=b * 8 / px,
                         psnr=psnr(orig, dec), ssim=ssim(orig, dec), enc_s=0, dec_s=0))
        b, dec = runpil(f, "WEBP", q, method=6)
        rows.append(dict(image=name, codec="webp", param=q, bytes=b, bpp=b * 8 / px,
                         psnr=psnr(orig, dec), ssim=ssim(orig, dec), enc_s=0, dec_s=0))
    if HAVE_AVIF:
        for q in [20, 30, 40, 50, 60, 70, 80, 90]:
            try:
                b, dec = runpil(f, "AVIF", q, speed=6)
                rows.append(dict(image=name, codec="avif", param=q, bytes=b, bpp=b * 8 / px,
                                 psnr=psnr(orig, dec), ssim=ssim(orig, dec), enc_s=0, dec_s=0))
            except Exception as e:
                print("  avif fail", q, e)

json.dump(rows, open(f"{ROOT}/bench/results5.json", "w"), indent=1)
print("wrote", len(rows), "rows")
