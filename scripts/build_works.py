#!/usr/bin/env python3
"""Build static, indexable work pages, optimised images, sitemap and robots.txt
from the published Google Sheet. Run by .github/workflows/build-works.yml.
Never deletes or edits existing artwork files; only adds/refreshes generated output."""
import csv, io, json, os, re, sys, urllib.request, hashlib
from html import escape
from PIL import Image, ImageOps

SITE = "https://osmanrafaat.github.io/osman-fine-art"
SHEET = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vSiChHx_Y9xUhLWb42AXOVrqUMVSUa-G01laFnTo3IZgE2HLPnUSmpHiZhBy79rluBUyYvshSuCDreI/pub?output=csv")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "img"); ORIG = os.path.join(ROOT, "originals"); WORK = os.path.join(ROOT, "work")
for d in (IMG, ORIG, WORK): os.makedirs(d, exist_ok=True)

MAX_BYTES = 40 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 120_000_000
ALLOWED_HOSTS = ("lh3.googleusercontent.com", "drive.google.com", "docs.google.com", "osmanrafaat.github.io")

def get(url):
    from urllib.parse import urlparse
    u = urlparse(url)
    if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
        raise ValueError("host not allowed: " + str(u.hostname))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=60).read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES: raise ValueError("file too large")
    return data

def slug(s, i):
    t = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60]
    i = re.sub(r"[^0-9]", "", i) or "x"
    return f"{i}-{t}" if t else i

def drive_id(u):
    m = re.search(r"googleusercontent\.com/d/([\w-]+)", u or "") or re.search(r"[?&]id=([\w-]+)", u or "")
    return m.group(1) if m else None

def svg_to_png(path, i):
    """Some older works are SVG files wrapping one embedded raster image; extract it losslessly."""
    import base64
    txt = open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r'href="data:image/(?:png|jpe?g);base64,([^"]+)"', txt)
    if not m: return None
    out = os.path.join(ORIG, f"derived-from-svg-{i}.png")
    if not os.path.exists(out): open(out, "wb").write(base64.b64decode(m.group(1)))
    return out

def source_image(row):
    """Return local path of the full-size source image, fetching/caching it if remote."""
    u = row["image"].strip()
    if not u: return None
    if u.startswith(SITE + "/"): u = u[len(SITE) + 1:]
    if not u.startswith("http"):
        if ".." in u or u.startswith("/"): return None
        p = os.path.join(ROOT, u)
        return svg_to_png(p, row["id"]) if p.endswith(".svg") and os.path.exists(p) else (p if os.path.exists(p) else None)
    p = os.path.join(ORIG, f"drive-{re.sub(r'[^0-9]', '', row['id'])}.jpg")  # raw downloaded bytes
    if os.path.exists(p) and os.path.getsize(p) > 1000: return p
    did = drive_id(u)
    url = f"https://lh3.googleusercontent.com/d/{did}=s0" if did else u
    data = get(url)
    open(p, "wb").write(data)
    return p

def derive(row, src):
    i = row["id"]; out = {}
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    for name, w, fmt, q in (("1600", 1600, "WEBP", 82), ("600", 600, "WEBP", 78), ("og", 1200, "JPEG", 84)):
        ext = "webp" if fmt == "WEBP" else "jpg"
        p = os.path.join(IMG, f"{i}-{name}.{ext}")
        if not os.path.exists(p):
            c = im.copy()
            if c.width > w: c = c.resize((w, round(c.height * w / c.width)), Image.LANCZOS)
            c.save(p, fmt, quality=q)
        out[name] = f"img/{i}-{name}.{ext}"
    out["w"], out["h"] = im.size
    return out

def read_rows():
    rows = list(csv.reader(io.StringIO(get(SHEET).decode("utf-8"))))
    h = [x.strip().lower() for x in rows[0]]
    res = []
    for r in rows[1:]:
        r = r + [""] * (len(h) - len(r))
        d = {k: r[j].strip() for j, k in enumerate(h)}
        if d.get("id") and d.get("image") and d.get("type") not in ("about", "archive"): res.append(d)
    return res

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Osman Rafaat</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Osman Rafaat | Visual Artist">
<meta property="og:title" content="{title} | Osman Rafaat"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld}</script>
<style>
:root{{--bg:#f5f2eb;--ink:#1c1a17;--accent:#8b7355}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,Arial,sans-serif;line-height:1.6}}
a{{color:inherit}}.skip{{position:absolute;left:-999px}}.skip:focus{{left:8px;top:8px;background:#fff;padding:8px;z-index:9}}
header{{display:flex;justify-content:space-between;align-items:center;padding:20px 5vw;border-bottom:1px solid rgba(28,26,23,.08);font-size:11px;letter-spacing:.25em;text-transform:uppercase;font-weight:700}}
header a{{text-decoration:none;padding:8px 0}}header a:focus-visible,.nav a:focus-visible{{outline:2px solid var(--accent);outline-offset:4px}}
main{{max-width:1200px;margin:0 auto;padding:4vw 5vw 8vw;display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:5vw;align-items:start}}
.mat{{background:#e5e5e5;padding:clamp(12px,3vw,40px);display:flex;justify-content:center}}
.mat img{{max-width:100%;height:auto;max-height:85vh;object-fit:contain;box-shadow:0 20px 40px rgba(0,0,0,.18)}}
h1{{font-family:'Cormorant Garamond',Georgia,serif;font-style:italic;font-weight:500;font-size:clamp(2rem,5vw,3.6rem);line-height:1.05;margin:0 0 .4em}}
.ar{{font-size:1.3rem;margin:0 0 1.4em;color:rgba(28,26,23,.7)}}
dl{{margin:1.5em 0;border-top:1px solid rgba(28,26,23,.1)}}dl div{{display:flex;justify-content:space-between;gap:1em;padding:.8em 0;border-bottom:1px solid rgba(28,26,23,.06);font-size:12px;letter-spacing:.12em;text-transform:uppercase}}
dt{{opacity:.5;font-weight:700}}dd{{margin:0;font-weight:600}}
.btn{{display:block;text-align:center;padding:16px;margin-top:12px;font-size:11px;letter-spacing:.25em;text-transform:uppercase;font-weight:700;text-decoration:none;border:1px solid rgba(28,26,23,.2)}}
.btn.p{{background:var(--ink);color:#fff;border-color:var(--ink)}}.btn:hover,.btn:focus-visible{{background:var(--accent);color:#fff;border-color:var(--accent);outline:none}}
.nav{{display:flex;justify-content:space-between;margin-top:2em;font-size:11px;letter-spacing:.2em;text-transform:uppercase;font-weight:700}}
.nav a{{text-decoration:none;padding:10px 0}}
@media(max-width:800px){{main{{grid-template-columns:1fr}}}}
</style></head><body>
<a class="skip" href="#work">Skip to artwork</a>
<header><a href="{home}">Osman Rafaat</a><a href="{home}#gallery">&larr; All works</a></header>
<main id="work"><div class="mat"><img src="../../{img}" width="{w}" height="{h}" alt="{alt}" fetchpriority="high"></div>
<div><h1>{title}</h1>{ar}
<dl>{facts}</dl>
<a class="btn p" href="{wa}" rel="noopener">Ask about this work (WhatsApp)</a>
<a class="btn" href="https://www.saatchiart.com/osmanrafaatosman" rel="noopener">View Saatchi Art profile</a>
<div class="nav"><a href="../../{prev}">&larr; Previous</a><a href="../../{next}">Next &rarr;</a></div></div></main>
</body></html>"""

def main():
    rows = read_rows(); seen = []
    for r in rows:
        try:
            src = source_image(r)
            if not src: print("skip (no image)", r["id"]); continue
            r["_img"] = derive(r, src); r["_slug"] = slug(r["title"], r["id"]); seen.append(r)
        except Exception as e:
            print("WARN image failed", r["id"], e, file=sys.stderr)
    n = len(seen)
    for k, r in enumerate(seen):
        t = r["title"] or "Artwork"
        parts = [x for x in (r.get("medium"), r.get("year")) if x]
        desc = f"{t}" + (f", {', '.join(parts)}" if parts else "") + " by Osman Rafaat, visual artist from Minya, Egypt."
        facts = "".join(f"<div><dt>{l}</dt><dd>{escape(v)}</dd></div>" for l, v in (("Year", r.get("year")), ("Medium", r.get("medium")), ("Dimensions", r.get("dimensions"))) if v)
        st = r.get("status", "").lower()
        if st == "available": facts += "<div><dt>Status</dt><dd>Available</dd></div>"
        if st == "collected": facts += "<div><dt>Status</dt><dd>Collected</dd></div>"
        ar = f'<p class="ar" lang="ar" dir="rtl">{escape(r["title_ar"])}</p>' if r.get("title_ar") else ""
        url = f"{SITE}/work/{r['_slug']}/"
        ld = {"@context": "https://schema.org", "@type": "VisualArtwork", "name": t, "creator": {"@type": "Person", "name": "Osman Rafaat", "url": SITE + "/"},
              "image": f"{SITE}/{r['_img']['1600']}", "url": url}
        if r.get("medium"): ld["artMedium"] = r["medium"]
        if r.get("year"): ld["dateCreated"] = r["year"]
        pv, nx = seen[(k - 1) % n], seen[(k + 1) % n]
        msg = urllib.request.quote(f"مرحباً عثمان، أنا مهتم بعملك الفني: {t}")
        html = PAGE.format(title=escape(t), desc=escape(desc, True), url=url, og=f"{SITE}/{r['_img']['og']}",
            ld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"), home="../../", img=r["_img"]["1600"], w=r["_img"]["w"], h=r["_img"]["h"],
            alt=escape(t + " by Osman Rafaat", True), ar=ar, facts=facts, wa=f"https://wa.me/201026933840?text={msg}",
            prev=f"work/{pv['_slug']}/", next=f"work/{nx['_slug']}/")
        d = os.path.join(WORK, r["_slug"]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
    # catalogue for the gallery (thumbnails + page links); index.html may use it later
    cat = [{"id": r["id"], "slug": r["_slug"], "thumb": r["_img"]["600"], "full": r["_img"]["1600"], "w": r["_img"]["w"], "h": r["_img"]["h"]} for r in seen]
    json.dump(cat, open(os.path.join(ROOT, "works.json"), "w"), indent=1)
    urls = [SITE + "/"] + [f"{SITE}/work/{r['_slug']}/" for r in seen]
    open(os.path.join(ROOT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print("built", n, "pages")

if __name__ == "__main__": main()
