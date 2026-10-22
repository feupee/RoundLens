"""Baixa minimapas e calibrações juntos. Execute na raiz: python scripts/download_maps.py."""
import json
import math
import os
import struct
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'frontend' / 'public' / 'maps'
URL = 'https://valorant-api.com/v1/maps'

def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'RoundLens/1.0'}), timeout=60) as response:
        return response.read()

def download(m):
    keys = ('xMultiplier', 'yMultiplier', 'xScalarToAdd', 'yScalarToAdd')
    if not m.get('displayIcon') or any(not isinstance(m.get(k), (int, float)) or not math.isfinite(m[k]) for k in keys):
        return None
    xm, ym, xs, ys = (m[k] for k in keys)
    if xm == 0 or ym == 0:
        return None
    raw = fetch(m['displayIcon'])
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Imagem PNG inválida: ' + m['displayName'])
    w, h = struct.unpack('>II', raw[16:24])
    # Content-addressed images keep the previous manifest usable on partial failure.
    import hashlib
    name = m['uuid'] + '-' + hashlib.sha256(raw).hexdigest()[:12] + '.png'
    (OUT / name).write_bytes(raw)
    print(m['displayName'], w, h)
    return {'mapUrl': m['mapUrl'], 'name': m['displayName'], 'image': '/maps/' + name,
            'matrix': [0, xm, xs, ym, 0, ys], 'width': w, 'height': h}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    maps = json.loads(fetch(URL))['data']
    with ThreadPoolExecutor(max_workers=4) as pool:
        entries = [m for m in pool.map(download, maps) if m]
    if not entries:
        raise RuntimeError('Nenhum minimapa válido recebido; catálogo anterior preservado.')
    manifest = {'source': URL, 'downloadedAt': datetime.now(timezone.utc).isoformat(), 'maps': entries}
    temp = OUT / 'catalog.tmp'
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, OUT / 'catalog.json')
    print(f'{len(entries)} mapas salvos em {OUT}')

if __name__ == '__main__':
    main()
