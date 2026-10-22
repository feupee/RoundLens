"""Importação transacional, idempotente e sem extração de caminhos do ZIP."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from sqlalchemy import delete, select
from .db import Base, engine, Session
from .models import Match, KillEvent, Marker


def team_names(filename, data, overrides):
    mid = data['matchInfo']['matchId']
    if mid in overrides:
        result = overrides[mid]
        if set(result) != {'Red', 'Blue'} or not all(isinstance(v, str) and v for v in result.values()):
            raise ValueError('Override deve conter nomes Red e Blue')
        return result, 'manual'
    # Nomes vêm da fonte, não de nicks de jogadores. Não unificar aliases automaticamente.
    found = re.search(r'\d{2}-\d{2}-\d{2}_(.+)_(\d+)_x_(\d+)_(.+)_([^_]+)\.json$', filename, re.I)
    teams = data['teams']
    if found:
        left, score_left, score_right, right, _ = found.groups()
        if score_left != score_right:
            scores = {t['roundsWon']: t['teamId'] for t in teams}
            if int(score_left) in scores and int(score_right) in scores:
                return {scores[int(score_left)]: left, scores[int(score_right)]: right}, 'filename_score'
    return {t['teamId']: f"Não resolvido: {mid[:8]} / {t['teamId']}" for t in teams}, 'unresolved'


def role(round_data, team):
    winner_role = round_data.get('winningTeamRole')
    if team not in ('Red', 'Blue') or winner_role not in ('Attacker', 'Defender'):
        return 'Unknown'
    if team == round_data['winningTeam']:
        return winner_role
    return 'Defender' if winner_role == 'Attacker' else 'Attacker'


def import_match(filename, raw, overrides=None):
    d = json.loads(raw)
    mi = d['matchInfo']
    mid = mi['matchId']
    digest = hashlib.sha256(raw).hexdigest()
    mapping, mapping_method = team_names(filename, d, overrides or {})
    competition = str(Path(filename).parent).replace('\\', '/')
    map_name = Path(filename).stem.rsplit('_', 1)[-1]
    metadata = {'teams': mapping, 'method': mapping_method}
    players = {p['puuid']: p for p in d['players'] if not p.get('isObserver')}
    event_rows, marker_rows = [], []
    for r in d['roundResults']:
        stats = {p['puuid']: p for p in r['playerStats']}
        for owner in r['playerStats']:
            for index, k in enumerate(owner['kills']):
                eid = hashlib.sha256(f"{mid}:{r['roundNum']}:{owner['puuid']}:{index}".encode()).hexdigest()[:32]
                killer, victim = players.get(k['killer']), players.get(k['victim'])
                category = ('unknown' if not killer or not victim else 'self' if k['killer'] == k['victim'] else
                            'friendly' if killer['teamId'] == victim['teamId'] else 'enemy')
                def person(p):
                    if not p:
                        return None
                    return {'id': p['puuid'], 'name': p['gameName']+'#'+p['tagLine'],
                            'agent_id': p['characterId'], 'team': mapping.get(p['teamId'], p['teamId']),
                            'side': role(r, p['teamId']),
                            'economy': stats.get(p['puuid'], {}).get('economy')}
                positions = {p['puuid']: p['location'] for p in k['playerLocations']}
                post = r.get('bombPlanter') is not None and k['timeSinceRoundStartMillis'] >= r['plantRoundTime']
                detail = {'killer': person(killer), 'victim': person(victim),
                          'assistants': [person(players.get(a)) or {'name': a} for a in k['assistants']],
                          'finishing_damage': k['finishingDamage'], 'victim_location': k['victimLocation'],
                          'killer_location': positions.get(k['killer']), 'positions': k['playerLocations'],
                          'post_plant': post, 'plant_site': r['plantSite'] if post else None,
                          'since_plant_ms': k['timeSinceRoundStartMillis']-r['plantRoundTime'] if post else None,
                          'round_result': r['roundResult'], 'round_winner': mapping.get(r['winningTeam']),
                          'source_owner': owner['puuid'], 'source_index': index}
                event_rows.append({'id': eid, 'match_id': mid, 'round_num': r['roundNum'],
                                   'time_ms': k['timeSinceRoundStartMillis'], 'game_time_ms': k['timeSinceGameStartMillis'],
                                   'category': category, 'detail': detail})
                # Mortes incluem self/friendly; abates são apenas contra adversários.
                for kind, p, pos in [('death', victim, k['victimLocation']), ('kill', killer, positions.get(k['killer']))]:
                    if not p or (kind == 'kill' and category != 'enemy'):
                        continue
                    marker_rows.append({'id': eid+':'+kind, 'event_id': eid, 'map_id': mi['mapId'],
                                        'competition': competition, 'team': mapping.get(p['teamId'], p['teamId']),
                                        'player_id': p['puuid'], 'player_name': p['gameName']+'#'+p['tagLine'],
                                        'side': role(r,p['teamId']), 'kind': kind, 'time_ms': k['timeSinceRoundStartMillis'],
                                        'x': pos.get('x') if pos else None, 'y': pos.get('y') if pos else None})
    with Session.begin() as session:
        old = session.get(Match, mid)
        if old and old.sha256 == digest and old.source == filename and old.team_mapping == metadata:
            return 'skipped', 0, mapping_method
        if old:
            event_ids = select(KillEvent.id).where(KillEvent.match_id == mid)
            session.execute(delete(Marker).where(Marker.event_id.in_(event_ids)))
            session.execute(delete(KillEvent).where(KillEvent.match_id == mid))
            session.delete(old)
            session.flush()
        session.add(Match(id=mid, source=filename, sha256=digest, competition=competition,
                          map_id=mi['mapId'], map_name=map_name, version=mi['gameVersion'],
                          team_mapping=metadata, payload=d))
        session.flush()
        if event_rows:
            session.execute(KillEvent.__table__.insert(), event_rows)
        if marker_rows:
            session.execute(Marker.__table__.insert(), marker_rows)
    return 'imported', len(event_rows), mapping_method


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path, help='ZIP oficial ou pasta com JSONs')
    parser.add_argument('--qualifiers-only', action='store_true', help='Importa apenas Classificatória 1 a 4')
    parser.add_argument('--teams', type=Path, help='Overrides: {matchId: {Red: nome, Blue: nome}}')
    args = parser.parse_args()
    overrides = json.loads(args.teams.read_text(encoding='utf-8')) if args.teams else {}
    Base.metadata.create_all(engine)
    counts = {'imported': 0, 'skipped': 0, 'errors': 0, 'unresolved': 0, 'events': 0}
    def consume(name, raw):
        if args.qualifiers_only and not re.search(r'Classificatória [1-4]/', name):
            return
        try:
            status, n, method = import_match(name, raw, overrides)
            counts[status] += 1
            counts['events'] += n
            counts['unresolved'] += method == 'unresolved'
        except Exception as exc:
            counts['errors'] += 1
            # Não emitir URL/credenciais do banco em mensagens de exceção.
            print(f'Falha em {name}: {type(exc).__name__}')
    if args.source.suffix.lower() == '.zip':
        with ZipFile(args.source) as archive:
            for item in archive.infolist():
                if item.filename.lower().endswith('.json'):
                    if item.file_size > 20_000_000:
                        raise ValueError('JSON excede limite de 20 MB')
                    consume(item.filename, archive.read(item))
    else:
        for path in sorted(args.source.rglob('*.json')):
            consume(path.relative_to(args.source).as_posix(), path.read_bytes())
    print(json.dumps(counts, ensure_ascii=False))
    if counts['errors']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
