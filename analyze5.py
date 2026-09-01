#!/usr/bin/env python3
import json, math
import numpy as np

ROOT = "/home/user/holocomp"
rows = json.load(open(f"{ROOT}/bench/results5.json"))
images = sorted({r["image"] for r in rows})


def curve(image, codec, metric="psnr"):
    pts = sorted((r["bpp"], r[metric]) for r in rows if r["image"] == image and r["codec"] == codec)
    out = []
    for b, q in pts:
        while out and q <= out[-1][1]:
            out.pop()
        out.append((b, q))
    return out


def bd_rate(ref, test):
    if len(ref) < 4 or len(test) < 4: return None
    lr = np.log10([p[0] for p in ref]); qr = np.array([p[1] for p in ref])
    lt = np.log10([p[0] for p in test]); qt = np.array([p[1] for p in test])
    lo, hi = max(qr.min(), qt.min()), min(qr.max(), qt.max())
    if hi - lo < 1e-6: return None
    pr, pt = np.polyfit(qr, lr, 3), np.polyfit(qt, lt, 3)
    ir = np.polyval(np.polyint(pr), [lo, hi]); ir = ir[1] - ir[0]
    it = np.polyval(np.polyint(pt), [lo, hi]); it = it[1] - it[0]
    return (10 ** ((it - ir) / (hi - lo)) - 1) * 100


def mean_bd(codec, metric="psnr", ref="jpeg"):
    v = [bd_rate(curve(im, ref, metric), curve(im, codec, metric)) for im in images]
    v = [x for x in v if x is not None]
    return np.mean(v) if v else float("nan")


NAME = {"v4": "v4", "v5-full": "v5 FULL",
        "v5-no-angular": "v5 without 33 angular modes", "v5-no-dst": "v5 without DST-VII",
        "v5-no-richctx": "v5 without rich contexts", "v5-no-perc": "v5 without perceptual lambda",
        "jpeg": "JPEG", "webp": "WebP", "avif": "AVIF"}
MAIN = ["v4", "v5-full", "jpeg", "webp", "avif"]

print("=" * 74)
print("BD-RATE vs JPEG   (negative = fewer bits for the same quality)")
print("=" * 74)
print(f"{'codec':<30}{'PSNR':>12}{'SSIM':>12}")
for c in MAIN:
    if c == "jpeg": continue
    print(f"  {NAME[c]:<28}{mean_bd(c,'psnr'):+11.1f}%{mean_bd(c,'ssim'):+11.1f}%")

print()
print("=" * 74)
print("ABLATION — what each feature contributes (BD-rate PSNR vs JPEG)")
print("=" * 74)
full = mean_bd("v5-full")
print(f"  {'v5 FULL':<36}{full:+8.1f}%")
for c, lab in [("v5-no-angular", "1. 33 angular modes"),
               ("v5-no-dst", "2. DST-VII transform"),
               ("v5-no-richctx", "3. rich 2-D contexts"),
               ("v5-no-perc", "4. perceptual lambda")]:
    w = mean_bd(c)
    print(f"  without {lab:<28}{w:+8.1f}%   -> worth {full - w:+5.1f} pts")
v4 = mean_bd("v4")
print(f"  {'v4 baseline':<36}{v4:+8.1f}%")
print(f"\n  Total improvement v4 -> v5 (PSNR): {full - v4:+.1f} pts")
print(f"  Total improvement v4 -> v5 (SSIM): {mean_bd('v5-full','ssim') - mean_bd('v4','ssim'):+.1f} pts")
print()
print("  SSIM ablation (perceptual lambda targets SSIM, not PSNR):")
for c, lab in [("v5-full","v5 FULL"),("v5-no-perc","v5 without perceptual lambda")]:
    print(f"    {lab:<34}{mean_bd(c,'ssim'):+8.1f}%")

print()
print("=" * 74)
print("PSNR AT MATCHED BITRATE (mean over 8 Kodak images)")
print("=" * 74)
targets = [0.15, 0.25, 0.5, 1.0, 1.5]
print(f"{'codec':<26}" + "".join(f"{f'{t}':>10}" for t in targets) + "   bpp")
for c in MAIN:
    line = f"{NAME[c]:<26}"
    for t in targets:
        vs = []
        for im in images:
            cv = curve(im, c, "psnr")
            if len(cv) < 2: continue
            b = [p[0] for p in cv]; q = [p[1] for p in cv]
            if t < min(b) or t > max(b): continue
            vs.append(np.interp(t, b, q))
        line += f"{(f'{np.mean(vs):.2f}' if len(vs) >= 4 else '--'):>10}"
    print(line)

print()
print("=" * 74)
print("SPEED (mean per 768x512 image)")
print("=" * 74)
for c in ["v4", "v5-full"]:
    e = [r["enc_s"] for r in rows if r["codec"] == c and r["enc_s"] > 0]
    d = [r["dec_s"] for r in rows if r["codec"] == c and r["dec_s"] > 0]
    if e:
        print(f"  {NAME[c]:<28} encode {np.mean(e):.3f}s   decode {np.mean(d) if d else 0:.3f}s")

# ------------------------------------------------------------------ plot
COL = {"v4": "#e67e22", "v5-full": "#111111", "jpeg": "#2980b9", "webp": "#27ae60", "avif": "#8e44ad"}
LBL = {"v4": "holocomp v4", "v5-full": "holocomp v5 (33 angular + DST + rich ctx)",
       "jpeg": "JPEG", "webp": "WebP", "avif": "AVIF"}

def plot(metric, fname, ylabel, ylim):
    W, H = 1220, 730; ml, mr, mt, mb = 78, 268, 58, 62
    pw, ph = W - ml - mr, H - mt - mb
    xlo, xhi = 0.06, 2.2; ylo, yhi = ylim
    X = lambda b: ml + (math.log10(b) - math.log10(xlo)) / (math.log10(xhi) - math.log10(xlo)) * pw
    Y = lambda v: mt + ph - (v - ylo) / (yhi - ylo) * ph
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="#fff"/>',
         f'<text x="{ml}" y="30" font-family="Helvetica,Arial" font-size="19" font-weight="bold">holocomp v5 — Kodak set, {ylabel}</text>',
         f'<text x="{ml}" y="49" font-family="Helvetica,Arial" font-size="12" fill="#666">35 directional intra modes, DST-VII, neighbour-conditioned contexts, perceptual RD. Higher-left is better.</text>']
    for b in [0.0625, 0.125, 0.25, 0.5, 1.0, 2.0]:
        x = X(b)
        s.append(f'<line x1="{x:.1f}" y1="{mt}" x2="{x:.1f}" y2="{mt+ph}" stroke="#eaeaea"/>')
        s.append(f'<text x="{x:.1f}" y="{mt+ph+20}" font-size="12" font-family="Helvetica,Arial" fill="#444" text-anchor="middle">{b:g}</text>')
    for i in range(8):
        v = ylo + (yhi - ylo) * i / 7; y = Y(v)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+pw}" y2="{y:.1f}" stroke="#eaeaea"/>')
        lab = f"{v:.0f}" if metric == "psnr" else f"{v:.3f}"
        s.append(f'<text x="{ml-10}" y="{y+4:.1f}" font-size="12" font-family="Helvetica,Arial" fill="#444" text-anchor="end">{lab}</text>')
    s.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="#999"/>')
    s.append(f'<text x="{ml+pw/2}" y="{H-16}" font-size="14" font-family="Helvetica,Arial" text-anchor="middle">bits per pixel (log)</text>')
    s.append(f'<text x="20" y="{mt+ph/2}" font-size="14" font-family="Helvetica,Arial" text-anchor="middle" transform="rotate(-90 20 {mt+ph/2})">{ylabel}</text>')
    grid = np.logspace(math.log10(0.07), math.log10(2.0), 44)
    for c in MAIN:
        acc = []
        for g in grid:
            vs = []
            for im in images:
                cv = curve(im, c, metric)
                if len(cv) < 2: continue
                b = [p[0] for p in cv]; q = [p[1] for p in cv]
                if g < min(b) or g > max(b): continue
                vs.append(np.interp(g, b, q))
            acc.append(np.mean(vs) if len(vs) >= 6 else None)
        pts = [(g, v) for g, v in zip(grid, acc) if v is not None]
        if len(pts) < 2: continue
        d = " ".join(("M" if i == 0 else "L") + f"{X(b):.1f},{Y(v):.1f}" for i, (b, v) in enumerate(pts))
        wd = 3.6 if c == "v5-full" else 2.2
        s.append(f'<path d="{d}" fill="none" stroke="{COL[c]}" stroke-width="{wd}"/>')
    lx, ly = ml + pw + 20, mt + 10
    s.append(f'<text x="{lx}" y="{ly}" font-size="13" font-weight="bold" font-family="Helvetica,Arial">Codec</text>')
    for i, c in enumerate(MAIN):
        yy = ly + 24 + i * 25
        s.append(f'<line x1="{lx}" y1="{yy-4}" x2="{lx+24}" y2="{yy-4}" stroke="{COL[c]}" stroke-width="3.4"/>')
        s.append(f'<text x="{lx+31}" y="{yy}" font-size="11.5" font-family="Helvetica,Arial">{LBL[c]}</text>')
    by = ly + 24 + len(MAIN) * 25 + 26
    s.append(f'<text x="{lx}" y="{by}" font-size="13" font-weight="bold" font-family="Helvetica,Arial">BD-rate vs JPEG</text>')
    k = 0
    for c in MAIN:
        if c == "jpeg": continue
        v = mean_bd(c, metric)
        col = "#1a7f37" if v < 0 else "#b3261e"
        yy = by + 24 + k * 21
        s.append(f'<text x="{lx}" y="{yy}" font-size="11.5" font-family="Helvetica,Arial">{LBL[c].split(" (")[0]}</text>')
        s.append(f'<text x="{lx+232}" y="{yy}" font-size="11.5" font-weight="bold" fill="{col}" font-family="Helvetica,Arial" text-anchor="end">{v:+.1f}%</text>')
        k += 1
    s.append('</svg>')
    open(f"{ROOT}/bench/{fname}", "w").write("\n".join(s))
    print("wrote", fname)

plot("psnr", "rd_v5_psnr.svg", "PSNR (dB, RGB)", (22, 44))
plot("ssim", "rd_v5_ssim.svg", "SSIM (luma)", (0.70, 1.00))
