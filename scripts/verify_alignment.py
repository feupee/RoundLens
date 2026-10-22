"""Read-only diagnostic of imported coordinates against bundled minimaps.

Run: python scripts/verify_alignment.py (requires Pillow for the contact sheet).
No application configuration or environment file is read.
"""
import json
import sqlite3
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads((ROOT / 'frontend/public/maps/catalog.json').read_text(encoding='utf-8'))
    with sqlite3.connect((ROOT / 'backend/eventmap.db').as_uri() + '?mode=ro', uri=True) as db:
        groups = db.execute('SELECT DISTINCT map_id FROM markers ORDER BY map_id').fetchall()
        sheet = Image.new('RGB', (1200, 340 * ((len(groups) + 2) // 3)), '#0b1018')
        report = []
        for index, (map_id,) in enumerate(groups):
            entry = next((m for m in catalog['maps'] if m['mapUrl'].lower() == map_id.lower()), None)
            if not entry:
                report.append({'map': map_id, 'error': 'missing calibration'})
                continue
            a, b, c, d, e, f = entry['matrix']
            points = db.execute('SELECT x,y,kind FROM markers WHERE map_id=? AND x IS NOT NULL AND y IS NOT NULL ORDER BY id', (map_id,)).fetchall()
            projected = [(a*x+b*y+c, d*x+e*y+f, kind) for x, y, kind in points]
            outside = sum(not (0 <= u <= 1 and 0 <= v <= 1) for u, v, _ in projected)
            image = Image.open(ROOT / 'frontend/public' / entry['image'].lstrip('/')).convert('RGB')
            assert image.size == (entry['width'], entry['height'])
            image = image.resize((300, 300))
            draw = ImageDraw.Draw(image)
            for u, v, kind in projected[::max(1, len(projected)//800)]:
                x, y = u * 300, v * 300
                draw.ellipse((x-1, y-1, x+1, y+1), fill='#39d98a' if kind == 'kill' else '#ff5d73')
            x, y = (index % 3)*400, (index // 3)*340
            sheet.paste(image, (x+50, y+30))
            ImageDraw.Draw(sheet).text((x+10, y+8), f"{entry['name']}: {len(points)} points; {outside} outside", fill='white')
            report.append({'map': entry['name'], 'located_markers': len(points), 'outside_image': outside})
    out = ROOT / 'docs/alignment'
    out.mkdir(parents=True, exist_ok=True)
    sheet.save(out / 'contact-sheet.png')
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
