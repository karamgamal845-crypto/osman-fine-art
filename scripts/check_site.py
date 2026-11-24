#!/usr/bin/env python3
"""Read-only deployment regression checks. Run: python3 scripts/check_site.py"""
import csv,io,json,re,urllib.request,concurrent.futures
SITE='https://osmanrafaat.github.io/osman-fine-art/'
SHEET='https://docs.google.com/spreadsheets/d/e/2PACX-1vSiChHx_Y9xUhLWb42AXOVrqUMVSUa-G01laFnTo3IZgE2HLPnUSmpHiZhBy79rluBUyYvshSuCDreI/pub?output=csv'
def get(url):
    with urllib.request.urlopen(url,timeout=30) as r:
        assert r.status==200,(url,r.status)
        return r.read()
def main():
    html=get(SITE).decode()
    rows=list(csv.DictReader(io.StringIO(get(SHEET).decode())))
    works=json.loads(get(SITE+'works.json'))
    assert len({r['id'] for r in rows})==len(rows),'Duplicate sheet IDs'
    expected={r['id'] for r in rows if r.get('type','').strip().lower() not in ('about','archive') and r.get('image','').strip()}
    actual={w['id'] for w in works}
    assert actual==expected,('Catalog differs from current sheet; build may be pending',sorted(expected-actual),sorted(actual-expected))
    assert 'tel:01026933840' in html,'Contact regression'
    assert '<main' in html,'Main landmark missing'
    assert 'cdn.tailwindcss.com' not in html,'Runtime CSS compiler returned'
    for f in ('catalog.js','portfolio.js','portfolio.css'):get(SITE+'assets/'+f)
    def check(w):
        path='work/'+w['slug']+'/'
        page=get(SITE+path).decode()
        assert '<link rel="canonical"' in page or 'rel="canonical"' in page, path
        assert 'VisualArtwork' in page,path
        for key in ('thumb','full','og'):
            if key in w:get(SITE+w[key])
        return w['id']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        checked=list(pool.map(check,works))
    get(SITE+'sitemap.xml');get(SITE+'robots.txt')
    print(json.dumps({'sheet_rows':len(rows),'catalog_works':len(works),'checked_ids':sorted(checked,key=int),'status':'passed'},ensure_ascii=False))
if __name__=='__main__':main()
