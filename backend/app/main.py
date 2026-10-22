import os
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.orm import Session as DBSession
from .db import Base, engine, get_session
from .models import Match, KillEvent, Marker

@asynccontextmanager
async def lifespan(app):
    # Inicialização para o MVP local; em produção, usar Alembic antes de iniciar.
    if os.getenv('AUTO_CREATE_TABLES', 'true').lower() == 'true':
        Base.metadata.create_all(engine)
    yield

app = FastAPI(title='VALORANT Event Map', version='0.1.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(','), allow_methods=['GET'], allow_headers=['*'])
DB = Annotated[DBSession, Depends(get_session)]

@app.get('/health')
def health(db: DB):
    db.execute(select(1))
    return {'status': 'ok'}

@app.get('/api/v1/catalog')
def catalog(db: DB, map_id: str | None = None,
            competition: Annotated[list[str] | None, Query()] = None,
            team: Annotated[list[str] | None, Query()] = None,
            match_id: str | None = None):
    scope = [Marker.map_id == map_id] if map_id else []
    if competition:
        scope.append(Marker.competition.in_(competition))
    if team:
        scope.append(Marker.team.in_(team))
    pq = select(Marker.player_id, Marker.player_name).distinct().order_by(Marker.player_name)
    pq = pq.where(*scope)
    names = {}
    for pid, name in db.execute(pq):
        names.setdefault(pid, []).append(name)
    # Matches are restricted by exactly the same map/championship/team scope.
    matches = db.execute(select(Match.id, Match.source, Match.team_mapping).where(
        Match.id.in_(select(KillEvent.match_id).join(Marker, Marker.event_id == KillEvent.id).where(*scope))
    ).order_by(Match.source)).all()
    chosen = db.get(Match, match_id) if match_id and match_id in {m.id for m in matches} else None
    rounds = sorted({r['roundNum'] for r in chosen.payload.get('roundResults', [])}) if chosen else []
    timeline = []
    if chosen:
        teams = chosen.team_mapping.get('teams', {})
        for r in sorted(chosen.payload.get('roundResults', []), key=lambda r: r['roundNum']):
            winner = teams.get(r.get('winningTeam'))
            outcome = ('win' if winner == team[0] else 'loss') if team and len(team) == 1 and winner else 'unknown'
            timeline.append({'round': r['roundNum']+1, 'winner': winner, 'outcome': outcome})
    competitions = select(Marker.competition).distinct().order_by(Marker.competition)
    if map_id:
        competitions = competitions.where(Marker.map_id == map_id)
    team_scope = [Marker.map_id == map_id] if map_id else []
    if competition:
        team_scope.append(Marker.competition.in_(competition))
    available_teams = list(db.scalars(select(Marker.team).where(*team_scope).distinct().order_by(Marker.team)))
    return {'maps': [{'id': a, 'name': b} for a,b in db.execute(select(Match.map_id, Match.map_name).distinct().order_by(Match.map_name))],
            'competitions': list(db.scalars(competitions)), 'teams': available_teams,
            'players': [{'id': pid, 'name': ' / '.join(ns)} for pid, ns in names.items()],
            'matches': [{'id': m.id, 'name': ' × '.join(m.team_mapping.get('teams', {}).values()), 'source': m.source.rsplit('/', 1)[-1]} for m in matches],
            'rounds': [r+1 for r in rounds], 'round_timeline': timeline}

@app.get('/api/v1/map-bounds')
def bounds(db: DB, map_id: str):
    row = db.execute(select(func.min(Marker.x),func.max(Marker.x),func.min(Marker.y),func.max(Marker.y)).where(Marker.map_id == map_id)).one()
    return {'bounds': list(row), 'note': 'Limites dos dados apenas para plano de coordenadas; não calibram uma imagem.'}

@app.get('/api/v1/events')
def events(db: DB, map_id: str,
           competition: Annotated[list[str] | None, Query()] = None,
           team: Annotated[list[str] | None, Query()] = None,
           player: Annotated[list[str] | None, Query()] = None,
           side: Annotated[list[str] | None, Query()] = None,
           kind: Annotated[list[str] | None, Query()] = None,
           match_id: str | None = None, round_num: int | None = Query(None, ge=1),
           start_ms: int = Query(0, ge=0), end_ms: int | None = Query(None, ge=0),
           after: str | None = None, limit: int = Query(2000, ge=1, le=5000)):
    if end_ms is not None and end_ms <= start_ms:
        raise HTTPException(422, 'Fim deve ser maior que início')
    if side and any(s not in ['Attacker','Defender','Unknown'] for s in side):
        raise HTTPException(422, 'Lado inválido')
    if kind and any(k not in ['kill','death'] for k in kind):
        raise HTTPException(422, 'Tipo inválido')
    filters = [Marker.map_id == map_id, Marker.time_ms >= start_ms]
    if round_num is not None and not match_id:
        raise HTTPException(422, 'Escolha uma partida antes do round')
    if match_id:
        event_scope = select(KillEvent.id).where(KillEvent.match_id == match_id)
        if round_num is not None:
            event_scope = event_scope.where(KillEvent.round_num == round_num-1)
        filters.append(Marker.event_id.in_(event_scope))
    for column, options in [(Marker.competition,competition),(Marker.team,team),(Marker.player_id,player),(Marker.side,side),(Marker.kind,kind)]:
        if options:
            filters.append(column.in_(options))
    if end_ms is not None:
        filters.append(Marker.time_ms < end_ms)
    total, unique = db.execute(select(func.count(Marker.id),func.count(func.distinct(Marker.event_id))).where(*filters)).one()
    stats = dict(db.execute(select(Marker.kind,func.count()).where(*filters).group_by(Marker.kind)).all())
    missing = db.scalar(select(func.count()).select_from(Marker).where(*filters, Marker.x.is_(None)))
    q = select(Marker).where(*filters).order_by(Marker.id).limit(limit+1)
    if after:
        q = q.where(Marker.id > after)
    rows = list(db.scalars(q)); more = len(rows)>limit; rows=rows[:limit]
    fields = ['id','event_id','player_id','player_name','team','side','kind','time_ms','x','y']
    return {'items': [{f:getattr(m,f) for f in fields} for m in rows],
            'next_cursor': rows[-1].id if more else None,
            'summary': {'markers':total,'events':unique,'kills':stats.get('kill',0),'deaths':stats.get('death',0),'missing_positions':missing}}

@app.get('/api/v1/events/{event_id}')
def detail(event_id: str, db: DB):
    event = db.get(KillEvent,event_id)
    if not event:
        raise HTTPException(404,'Evento não encontrado')
    match = db.get(Match,event.match_id)
    return event_report(event, match)


def event_report(event, match):
    """Enrich existing imports from their preserved source; no reimport required."""
    payload = match.payload
    rounds = payload.get('roundResults', [])
    current = next((r for r in rounds if r['roundNum'] == event.round_num), {})
    teams = match.team_mapping.get('teams', {})
    players = {p['puuid']: p for p in payload.get('players', []) if not p.get('isObserver')}
    locations = {p['puuid']: p['location'] for p in event.detail.get('positions', [])}
    victim = event.detail.get('victim') or {}
    if event.detail.get('victim_location') and victim.get('id'):
        locations[victim['id']] = event.detail['victim_location']
    participants = [{'id': pid, 'name': p['gameName']+'#'+p['tagLine'],
                     'agent_id': p['characterId'], 'team_id': p['teamId'],
                     'team': teams.get(p['teamId'], p['teamId']), 'location': locations.get(pid)}
                    for pid, p in players.items()]
    score = {tid: 0 for tid in teams}
    for r in rounds:
        if r['roundNum'] < event.round_num and r.get('winningTeam') in score:
            score[r['winningTeam']] += 1
    damage = []
    for stats in current.get('playerStats', []):
        for hit in stats.get('damage', []):
            if hit.get('receiver') == victim.get('id'):
                damage.append({'attacker_id': stats['puuid'],
                               'attacker_name': next((p['name'] for p in participants if p['id'] == stats['puuid']), 'Não identificado'),
                               **{k: hit.get(k, 0) for k in ('damage', 'headshots', 'bodyshots', 'legshots')}})
    planted = bool(current.get('bombPlanter')) and event.time_ms >= current.get('plantRoundTime', 0)
    defused = bool(current.get('bombDefuser')) and event.time_ms >= current.get('defuseRoundTime', 0)
    spike = current.get('plantLocation') if planted and not defused else None
    return {'id':event.id,'match_id':event.match_id,'round':event.round_num+1,'time_ms':event.time_ms,
            'game_time_ms':event.game_time_ms,'category':event.category,'competition':match.competition,
            'map':match.map_name,'source':match.source,'team_mapping':match.team_mapping,**event.detail,
            'participants': participants, 'score': [{'team': teams[t], 'rounds': n} for t,n in score.items()],
            'spike_location': spike, 'spike_state': 'defused' if defused else 'planted' if planted else 'not_planted', 'damage_report': damage,
            'damage_scope': 'round_total', 'final_hit_headshot': None}
