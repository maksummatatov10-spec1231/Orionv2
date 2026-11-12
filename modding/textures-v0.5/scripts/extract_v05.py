#!/usr/bin/env python3
"""Extract the v0.4 target set plus every ore block/icon/drop/particle from Orion.swf."""
import argparse, hashlib, json, re, struct, zlib
import xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
OUT = ROOT / 'input'
OUT.mkdir(exist_ok=True)
(DEFAULT_SWF := Path('/tmp/orion-work/Orion Sandbox Enhanced/Orion.swf'))

ORES = [
    # name, block id, placeable item id, dropped item id, hit effect
    ('coal', 5, 260, 1024, 'coal'),
    ('bronze', 167, 420, 1194, 'bronze'),
    ('iron', 6, 261, 1025, 'iron'),
    ('gold', 7, 262, 1026, 'gold'),
    ('diamond', 8, 263, 1027, 'diamond'),
    ('fire_iron', 9, 264, 1028, 'fire_iron'),
]

def sha(b): return hashlib.sha256(b).hexdigest()

def parse_tags(body):
    n = (body[0] >> 3) & 31
    p = (5 + 4*n + 7)//8 + 4
    out = []
    while p + 2 <= len(body):
        v = struct.unpack_from('<H', body, p)[0]
        code, ln, h = v >> 6, v & 63, 2
        if ln == 63:
            ln = struct.unpack_from('<I', body, p+2)[0]; h = 6
        e = p + h + ln
        if e > len(body): raise ValueError('truncated SWF tag')
        out.append((code, body[p+h:e])); p = e
        if code == 0: break
    return out

def lossless(data):
    fmt = data[2]
    w, h = struct.unpack_from('<HH', data, 3)
    if fmt != 5: raise ValueError(f'unsupported image format {fmt}')
    raw = zlib.decompress(data[7:])
    stride = ((w*4 + 3)//4)*4
    if len(raw) != stride*h: raise ValueError('bad lossless payload')
    im = Image.new('RGBA', (w, h)); px = im.load()
    for y in range(h):
        base = y*stride
        for x in range(w):
            a, r, g, b = raw[base+x*4:base+x*4+4]
            px[x, y] = (0, 0, 0, 0) if a == 0 else (
                min(255, round(r*255/a)), min(255, round(g*255/a)),
                min(255, round(b*255/a)), a)
    return im

def ui_char(item_id):
    p = REPO / 'analysis/as3/assets' / f'Images_ITEM_{item_id}_CLASS.as'
    if not p.exists(): return None
    m = re.search(r'Embed\(source="/_assets/(\d+)_', p.read_text())
    return int(m.group(1)) if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', type=Path, default=DEFAULT_SWF)
    args = ap.parse_args()
    swf = args.input.read_bytes()
    if swf[:3] != b'CWS': raise ValueError('expected CWS SWF')
    tags = parse_tags(zlib.decompress(swf[8:]))
    byid = {}
    for code, data in tags:
        if code in (20, 36) and len(data) >= 7:
            byid[struct.unpack_from('<H', data, 0)[0]] = (code, data)
    decoded = {}
    def image(cid):
        if cid not in decoded: decoded[cid] = lossless(byid[cid][1])
        return decoded[cid]

    manifest = {'source_swf_sha256': sha(swf), 'version': 'textures-v0.5', 'targets': []}
    xml_cache = {}
    def atlas(cid, xml, region, label):
        if xml not in xml_cache:
            xml_cache[xml] = E.parse(REPO / 'analysis/binary' / f'binary-{xml}.xml').getroot()
        e = next(e for e in xml_cache[xml] if e.get('name') == region)
        x, y, w, h = map(int, (e.get('x'), e.get('y'), e.get('width'), e.get('height')))
        im = image(cid).crop((x, y, x+w, y+h))
        p = OUT / f'{label}.png'; im.save(p)
        manifest['targets'].append({
            'kind': 'atlas_rect', 'label': label, 'atlas_char': cid, 'xml_char': xml,
            'region': region, 'x': x, 'y': y, 'w': w, 'h': h, 'path': str(p),
            'sha256': sha(p.read_bytes()), 'alpha_extrema': im.getchannel('A').getextrema()})
        return im
    def standalone(cid, label):
        im = image(cid)
        p = OUT / f'{label}.png'; im.save(p)
        manifest['targets'].append({
            'kind': 'image', 'label': label, 'char': cid, 'tag_code': byid[cid][0],
            'w': im.width, 'h': im.height, 'path': str(p), 'sha256': sha(p.read_bytes()),
            'alpha_extrema': im.getchannel('A').getextrema()})
        return im

    # Re-extract all accepted v0.4 targets from the original SWF (no processed pixels reused as input).
    old = json.loads((ROOT.parent / 'textures-v0.4/verification/targets.json').read_text())['targets']
    for t in old:
        if t['kind'] == 'atlas_rect':
            atlas(t['atlas_char'], t['xml_char'], t['region'], t['label'])
        elif t['kind'] == 'image':
            standalone(t['char'], t['label'])
        else:
            raise ValueError(t['kind'])

    def has_region(xml, region):
        if xml not in xml_cache:
            xml_cache[xml] = E.parse(REPO / 'analysis/binary' / f'binary-{xml}.xml').getroot()
        return any(e.get('name') == region for e in xml_cache[xml])

    coverage = []
    for name, block_id, place_id, drop_id, hit in ORES:
        atlas(1646, 1987, f'block_{block_id}', f'{name}_ore_block_{block_id}')
        # Most ore block items reuse the dropped-mineral icon; only bronze has a dedicated placeable atlas rect.
        if has_region(2045, f'item_{place_id}'):
            atlas(1476, 2045, f'item_{place_id}', f'{name}_ore_block_icon_atlas_{place_id}')
        atlas(1476, 2045, f'item_{drop_id}', f'{name}_ore_drop_icon_atlas_{drop_id}')
        cid = ui_char(drop_id)
        if cid is not None:
            standalone(cid, f'{name}_ore_drop_icon_ui_{drop_id}')
        place_ui = ui_char(place_id)
        if place_ui is not None:
            standalone(place_ui, f'{name}_ore_block_icon_ui_{place_id}')
        atlas(1501, 1582, f'hit_{hit}', f'hit_{hit}')
        coverage.append({'name': name, 'block_id': block_id, 'placeable_item_id': place_id,
                         'dropped_item_id': drop_id, 'hit_texture': f'hit_{hit}',
                         'drop_ui_char': cid, 'placeable_ui_char': place_ui})
    # item_light_1027 aliases the same atlas rectangle as item_1027; one replacement covers both.
    manifest['ore_coverage'] = coverage
    labels = [t['label'] for t in manifest['targets']]
    if len(labels) != len(set(labels)): raise ValueError('duplicate target labels')
    (ROOT / 'verification/targets.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps({'targets': len(labels), 'ores': len(ORES), 'source_sha256': manifest['source_swf_sha256']}))

if __name__ == '__main__':
    main()
