#!/usr/bin/env python3
"""Make Android launcher icons (legacy, round, adaptive) from one square PNG.

Usage: python3 native/make_icons.py native/icon-source.png android/app/src/main/res
Runs in the GitHub Actions build, after `npx cap add android`.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter

SRC, RES = sys.argv[1], sys.argv[2]
LEGACY = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
ADAPT = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}

im = Image.open(SRC).convert("RGB")
im = im.resize((1024, 1024), Image.LANCZOS)

# Keep the picture exactly as designed (nothing is cropped). Only the white outside the
# picture's own rounded corners is made transparent.
mask = im.convert("L").point(lambda v: 255 if v >= 238 else 0)      # near-white
for corner in ((0, 0), (1023, 0), (0, 1023), (1023, 1023)):
    ImageDraw.floodfill(mask, corner, 128, thresh=0)
outside = mask.point(lambda v: 255 if v == 128 else 0).filter(ImageFilter.MaxFilter(5))   # grow 2px to hide the white fringe
alpha = outside.point(lambda v: 0 if v else 255).filter(ImageFilter.GaussianBlur(0.8))
art_rgba = im.convert("RGBA")
art_rgba.putalpha(alpha)
art = im                                                              # opaque version (used on top of backgrounds)


# background for round / adaptive icons: the artwork's own blue, as a soft vertical gradient
def gradient(size, top=(10, 168, 253), bottom=(3, 40, 200)):
    g = Image.new("RGB", (1, 256))
    for y in range(256):
        t = y / 255.0
        g.putpixel((0, y), tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3)))
    return g.resize((size, size), Image.BILINEAR)


blur = gradient(1024)


def rounded(img, radius_frac):
    s = img.size[0]
    m = Image.new("L", (s * 4, s * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, s * 4 - 1, s * 4 - 1), radius=int(s * 4 * radius_frac), fill=255)
    out = img.convert("RGBA")
    out.putalpha(m.resize((s, s), Image.LANCZOS))
    return out


def circle(img):
    s = img.size[0]
    m = Image.new("L", (s * 4, s * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, s * 4 - 1, s * 4 - 1), fill=255)
    out = img.convert("RGBA")
    out.putalpha(m.resize((s, s), Image.LANCZOS))
    return out


def save(path, img):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


for d, s in LEGACY.items():
    base = os.path.join(RES, "mipmap-" + d)
    save(os.path.join(base, "ic_launcher.png"), art_rgba.resize((s, s), Image.LANCZOS))
    canvas = blur.resize((s, s), Image.LANCZOS)
    k = int(s * 0.80)
    inner = art_rgba.resize((k, k), Image.LANCZOS)
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(inner, ((s - k) // 2, (s - k) // 2))
    save(os.path.join(base, "ic_launcher_round.png"), circle(canvas))

for d, s in ADAPT.items():
    base = os.path.join(RES, "mipmap-" + d)
    save(os.path.join(base, "ic_launcher_background.png"), blur.resize((s, s), Image.LANCZOS).convert("RGB"))
    k = int(s * 0.56)                       # whole picture inside the area every launcher shape keeps
    inner = art_rgba.resize((k, k), Image.LANCZOS)
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    layer.alpha_composite(inner, ((s - k) // 2, (s - k) // 2))
    save(os.path.join(base, "ic_launcher_foreground.png"), layer)

# the adaptive-icon xml points at the generated background / foreground images
anydpi = os.path.join(RES, "mipmap-anydpi-v26")
os.makedirs(anydpi, exist_ok=True)
xml = ('<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
       '    <background android:drawable="@mipmap/ic_launcher_background"/>\n'
       '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n</adaptive-icon>\n')
for n in ("ic_launcher.xml", "ic_launcher_round.xml"):
    with open(os.path.join(anydpi, n), "w") as f:
        f.write(xml)
print("icons written to", RES)
