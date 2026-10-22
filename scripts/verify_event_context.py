"""Smoke-test the new experience against local imports, strictly read-only.

Run with the backend development requirements installed, from the project root.
This does not read .env or use the running application's database configuration.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ['AUTO_CREATE_TABLES'] = 'false'
os.environ['DATABASE_URL'] = 'sqlite://'
sys.path.insert(0, str(ROOT / 'backend'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.db import get_session


def main():
    path = (ROOT / 'backend/eventmap.db').as_uri() + '?mode=ro'
    engine = create_engine('sqlite://', creator=lambda: sqlite3.connect(path, uri=True, check_same_thread=False))

    def readonly_session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = readonly_session
    content = json.loads((ROOT / 'frontend/public/content/catalog.json').read_text(encoding='utf-8'))
    assert content['weapons']['a03b24d3-4319-996d-0f8c-94bbfba1dfc7']['name'] == 'Operator'
    reports = []
    try:
        with TestClient(app) as client:
            maps = client.get('/api/v1/catalog').json()['maps']
            for m in maps:
                catalog = client.get('/api/v1/catalog', params={'map_id': m['id']}).json()
                competition = catalog['competitions'][0]
                scope = {'map_id': m['id'], 'competition': competition}
                catalog = client.get('/api/v1/catalog', params=scope).json()
                team = catalog['teams'][0]
                scope['team'] = team
                catalog = client.get('/api/v1/catalog', params=scope).json()
                mid = catalog['matches'][0]['id']
                scope['match_id'] = mid
                catalog = client.get('/api/v1/catalog', params=scope).json()
                assert catalog['rounds']
                timeline = catalog['round_timeline']
                assert [r['round'] for r in timeline] == catalog['rounds']
                for r in timeline:
                    assert r['outcome'] == ('win' if r['winner'] == team else 'loss') if r['winner'] else r['outcome'] == 'unknown'
                page = client.get('/api/v1/events', params=scope).json()
                assert page['items']
                event = client.get('/api/v1/events/'+page['items'][0]['event_id']).json()
                assert event['match_id'] == mid
                assert sum(s['rounds'] for s in event['score']) == event['round']-1
                assert len(event['participants']) == 10
                for p in event['participants']:
                    agent = content['agents'][p['agent_id'].lower()]
                    assert (ROOT / 'frontend/public' / agent['image'].lstrip('/')).exists()
                for p in [event['killer'], event['victim']]:
                    if p and p.get('economy'):
                        armor = p['economy'].get('armor', '').lower()
                        assert not armor or armor in content['gear']
                one_round = client.get('/api/v1/events', params={**scope, 'round_num': event['round']}).json()
                assert any(p['event_id'] == event['id'] for p in one_round['items'])
                reports.append({'map': m['name'], 'players': len(event['participants']),
                                'positioned': sum(p['location'] is not None for p in event['participants']),
                                'score_verified': True, 'round_filter_verified': True,
                                'timeline_verified': True, 'armor_catalog_verified': True})
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
    out = ROOT / 'docs/event-context'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'smoke-test.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(f'Validated {len(reports)} maps, match/round filters, rosters, scores, portraits and Operator UUID.')


if __name__ == '__main__':
    main()
