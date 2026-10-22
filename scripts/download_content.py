"""Download bundled agent portraits and weapon names without application secrets.

Run from the project root: python scripts/download_content.py
Source: https://valorant-api.com (community game-content catalog).
"""
import json
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1] / 'frontend/public/content'


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'RoundLens/1.0'}), timeout=45) as r:
        return r.read()


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    agents = json.loads(fetch('https://valorant-api.com/v1/agents?isPlayableCharacter=true&language=pt-BR'))['data']
    weapons = json.loads(fetch('https://valorant-api.com/v1/weapons?language=pt-BR'))['data']
    gear = json.loads(fetch('https://valorant-api.com/v1/gear?language=pt-BR'))['data']

    def agent(a):
        name = a['uuid'].lower() + '.png'
        if not (ROOT / name).exists():
            raw = fetch(a['displayIconSmall'] or a['displayIcon'])
            if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Invalid agent portrait')
            (ROOT / name).write_bytes(raw)
        return a['uuid'].lower(), {'name': a['displayName'], 'image': '/content/' + name,
                                  'abilities': {s['slot']: s['displayName'] for s in a['abilities']}}

    with ThreadPoolExecutor(max_workers=4) as pool:
        portraits = dict(pool.map(agent, agents))
    catalog = {'source': 'https://valorant-api.com', 'agents': portraits,
               'weapons': {w['uuid'].lower(): {'name': w['displayName']} for w in weapons},
               'gear': {g['uuid'].lower(): {'name': g['displayName']} for g in gear}}
    temp = ROOT / 'catalog.tmp'
    temp.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(ROOT / 'catalog.json')
    print(f"Downloaded {len(portraits)} agents and {len(weapons)} weapon names")


if __name__ == '__main__':
    main()
