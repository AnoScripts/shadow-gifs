"""Animated Minecraft-style button GIF (purple/pink gradient, wavy text).

usage: python mc_button_gif.py "Hello" [out.gif] [--scale 2] [--width 200]
Font is read from your installed Minecraft jar (%APPDATA%/.minecraft/versions).
"""
import argparse, colorsys, glob, io, json, math, os, zipfile
from PIL import Image

FRAMES, MS = 40, 60                                # 40 * 60ms = 2.4s loop
C1, C2 = (0x86, 0x5c, 0xff), (0xff, 0x5c, 0xd6)    # purple, pink
FILL, TOP, BOTTOM, EDGE = (93, 84, 104), (140, 118, 165), (60, 40, 70), (20, 4, 20)


def load_font():
    jars = sorted(glob.glob(os.path.expandvars(r"%APPDATA%\.minecraft\versions\*\*.jar")), key=os.path.getmtime)
    for jar in reversed(jars):
        z = zipfile.ZipFile(jar)
        try:
            prov = json.loads(z.read("assets/minecraft/font/include/default.json"))["providers"]
        except KeyError:
            continue
        p = next(p for p in prov if p["file"].endswith("font/ascii.png"))
        sheet = Image.open(io.BytesIO(z.read("assets/minecraft/textures/font/ascii.png"))).convert("RGBA")
        cw, ch = sheet.width // len(p["chars"][0]), sheet.height // len(p["chars"])
        glyphs = {}
        for row, line in enumerate(p["chars"]):
            for col, c in enumerate(line):
                g = sheet.crop((col * cw, row * ch, col * cw + cw, row * ch + ch))
                bbox = g.getchannel("A").getbbox()
                glyphs[c] = g.crop((0, 0, bbox[2] if bbox else 0, ch))
        glyphs[" "] = Image.new("RGBA", (3, ch))
        return glyphs, p.get("ascent", 7)
    raise SystemExit("No Minecraft jar with font found in %APPDATA%/.minecraft/versions")


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def grad(u):  # u in [0,1) -> purple..pink..purple, seamless
    return mix(C1, C2, (1 - math.cos(u * 2 * math.pi)) / 2)


def tint(glyph, color):
    out = Image.new("RGBA", glyph.size, color + (255,))
    out.putalpha(glyph.getchannel("A"))
    return out


def frame(text, glyphs, w, h, t):
    img = Image.new("RGB", (w, h), FILL)
    px = img.load()
    # bevel
    for x in range(1, w - 1):
        px[x, 1] = TOP
        px[x, h - 2] = px[x, h - 3] = BOTTOM
    # animated gradient outline running around the perimeter
    perim = [(x, 0) for x in range(w)] + [(w - 1, y) for y in range(1, h)] + \
            [(x, h - 1) for x in range(w - 2, -1, -1)] + [(0, y) for y in range(h - 2, 0, -1)]
    for i, (x, y) in enumerate(perim):
        u = (i / len(perim) * 2 - t) % 1                # 2 color waves around the border
        px[x, y] = mix(grad(u), EDGE, 0.15)
    # text: per-letter gradient + wave + MC drop shadow
    tw = sum(glyphs.get(c, glyphs["?"]).width + 1 for c in text) - 1
    x0, y0 = (w - tw) // 2, (h - 8) // 2
    for i, c in enumerate(text):
        g = glyphs.get(c, glyphs["?"])
        col = grad((i / max(len(text), 1) - t) % 1)
        dy = round(math.sin(2 * math.pi * (t * 2 - i / 8)))  # -1..1 px bob
        img.paste(tint(g, tuple(v // 4 for v in col)), (x0 + 1, y0 + dy + 1), g)
        img.paste(tint(g, col), (x0, y0 + dy), g)
        x0 += g.width + 1
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--width", type=int, help="button width in MC pixels (default: fit text)")
    a = ap.parse_args()
    glyphs, _ = load_font()
    tw = sum(glyphs.get(c, glyphs["?"]).width + 1 for c in a.text)
    w, h = a.width or max(tw + 40, 200), 20
    frames = [frame(a.text, glyphs, w, h, f / FRAMES).resize((w * a.scale, h * a.scale), Image.NEAREST)
              for f in range(FRAMES)]
    out = a.out or "".join(c for c in a.text if c.isalnum()) + ".gif"
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=MS, loop=0)
    print(out, frames[0].size)


if __name__ == "__main__":
    main()
