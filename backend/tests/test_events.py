import os
import tempfile
import json
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'test.db')
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from app.db import Base,engine,Session
from app.models import Match,KillEvent,Marker
from app.ingest import import_match,role
from app.main import app


def fixture():
    # Caso sintético de borda, não apresentado como partida real no aplicativo.
    players=[{'puuid':u,'gameName':u,'tagLine':'BR','teamId':t,'characterId':'agent','isObserver':False} for u,t in [('a','Red'),('b','Blue')]]
    kill={'killer':'a','victim':'b','assistants':[],'timeSinceRoundStartMillis':30000,'timeSinceGameStartMillis':60000,
          'victimLocation':{'x':100,'y':200},'playerLocations':[{'puuid':'a','location':{'x':10,'y':20},'viewRadians':1}],
          'finishingDamage':{'damageType':'Ability','damageItem':'Ultimate','isSecondaryFireMode':False}}
    r={'roundNum':0,'winningTeam':'Blue','winningTeamRole':'Attacker','roundResult':'Eliminated',
       'bombPlanter':'b','plantRoundTime':25000,'plantSite':'A',
       'playerStats':[{'puuid':'a','kills':[kill],'economy':{'loadoutValue':3000}},{'puuid':'b','kills':[],'economy':{}}]}
    return {'matchInfo':{'matchId':'test','mapId':'map','gameVersion':'test'},'players':players,
            'teams':[{'teamId':'Red','roundsWon':1},{'teamId':'Blue','roundsWon':13}],'roundResults':[r]}


def test_complete_flow():
    Base.metadata.create_all(engine)
    d=fixture();name='Univavá/Classificatória 1/X_01-01-26_alpha_1_x_13_beta_haven.json'
    assert import_match(name,json.dumps(d).encode())[0]=='imported'
    assert import_match(name,json.dumps(d).encode())[0]=='skipped'
    with Session() as s:
        assert s.scalar(select(func.count()).select_from(KillEvent))==1
        assert s.scalar(select(func.count()).select_from(Marker))==2
    with TestClient(app) as c:
        page=c.get('/api/v1/events',params={'map_id':'map','kind':'kill','player':'a','team':'alpha','side':'Defender','start_ms':30000}).json()
        assert page['summary']['kills']==1
        assert page['items'][0]['x']==10
        assert c.get('/api/v1/events',params={'map_id':'map','end_ms':30000}).json()['summary']['events']==0
        assert c.get('/api/v1/events',params={'map_id':'map','kind':'death','side':'Attacker'}).json()['items'][0]['x']==100
        report=c.get('/api/v1/events/'+page['items'][0]['event_id']).json()
        assert report['since_plant_ms']==5000
        assert report['finishing_damage']['damageItem']=='Ultimate'
        assert report['round']==1
        assert c.get('/api/v1/events',params={'map_id':'map','start_ms':30,'end_ms':10}).status_code==422
        assert c.get('/api/v1/events',params={'map_id':'map','kind':'invalid'}).status_code==422
        assert c.get('/api/v1/events/missing').status_code==404
        first=c.get('/api/v1/events',params={'map_id':'map','limit':1}).json()
        second=c.get('/api/v1/events',params={'map_id':'map','limit':1,'after':first['next_cursor']}).json()
        assert first['items'][0]['id']!=second['items'][0]['id']
        assert second['next_cursor'] is None
    # Reimportação alterada substitui registros e mantém posição ausente como null.
    d['roundResults'][0]['playerStats'][0]['kills'][0]['playerLocations']=[]
    assert import_match(name,json.dumps(d).encode())[0]=='imported'
    with TestClient(app) as c:
        result=c.get('/api/v1/events',params={'map_id':'map','kind':'kill'}).json()
        assert result['summary']['missing_positions']==1
        assert result['items'][0]['x'] is None
    # Autodestruição não cria um abate.
    d['roundResults'][0]['playerStats'][0]['kills'][0]['victim']='a'
    import_match(name,json.dumps(d).encode())
    with TestClient(app) as c:
        result=c.get('/api/v1/events',params={'map_id':'map'}).json()
        assert result['summary']['kills']==0
        assert result['summary']['deaths']==1
    # Mapeamento manual também atualiza fonte sem alteração do hash do JSON.
    assert import_match(name,json.dumps(d).encode(),{'test':{'Red':'Alpha corrigido','Blue':'Beta'}})[0]=='imported'


def test_roles():
    assert role({'winningTeam':'Red','winningTeamRole':'Defender'},'Blue')=='Attacker'
    assert role({'winningTeam':'Blue','winningTeamRole':'Attacker'},'Red')=='Defender'
    assert role({'winningTeam':'Red','winningTeamRole':''},'Blue')=='Unknown'


def test_progressive_catalog_match_round_and_event_context():
    from copy import deepcopy
    Base.metadata.create_all(engine)
    d=fixture(); d['matchInfo']['matchId']='guided-one'; d['matchInfo']['mapId']='guided-map'
    r=d['roundResults'][0]
    r['plantLocation']={'x':44,'y':55}
    r['playerStats'][0]['damage']=[{'receiver':'b','damage':160,'headshots':1,'bodyshots':1,'legshots':0}]
    r2=deepcopy(r);r2['roundNum']=1
    d['roundResults'].append(r2)
    d['players'].append({'puuid':'absent','gameName':'Absent','tagLine':'BR','teamId':'Red','characterId':'agent','isObserver':False})
    import_match('League/A/X_01-01-26_alpha_1_x_13_beta_haven.json',json.dumps(d).encode())
    other=deepcopy(d);other['matchInfo']['matchId']='guided-two'
    import_match('League/B/X_02-01-26_gamma_1_x_13_delta_haven.json',json.dumps(other).encode())
    with TestClient(app) as c:
        scope={'map_id':'guided-map','competition':'League/A'}
        cat=c.get('/api/v1/catalog',params=scope).json()
        assert set(cat['teams'])=={'alpha','beta'}
        assert [m['id'] for m in cat['matches']]==['guided-one']
        cat=c.get('/api/v1/catalog',params={**scope,'team':'alpha','match_id':'guided-one'}).json()
        assert [p['id'] for p in cat['players']]==['a']
        assert cat['rounds']==[1,2]
        assert cat['round_timeline']==[
            {'round':1,'winner':'beta','outcome':'loss'},
            {'round':2,'winner':'beta','outcome':'loss'},
        ]
        beta=c.get('/api/v1/catalog',params={**scope,'team':'beta','match_id':'guided-one'}).json()
        assert [r['outcome'] for r in beta['round_timeline']]==['win','win']
        neutral=c.get('/api/v1/catalog',params={**scope,'match_id':'guided-one'}).json()
        assert [r['outcome'] for r in neutral['round_timeline']]==['unknown','unknown']
        assert c.get('/api/v1/catalog',params={**scope,'match_id':'guided-two'}).json()['rounds']==[]
        assert c.get('/api/v1/catalog',params={**scope,'match_id':'guided-two'}).json()['round_timeline']==[]
        page=c.get('/api/v1/events',params={**scope,'match_id':'guided-one','round_num':2,'side':'Defender','team':'alpha'}).json()
        assert page['summary']['events']==1
        report=c.get('/api/v1/events/'+page['items'][0]['event_id']).json()
        assert report['round']==2
        assert report['score']==[{'team':'alpha','rounds':0},{'team':'beta','rounds':1}]
        assert report['spike_location']=={'x':44,'y':55}
        assert report['damage_report'][0]['headshots']==1
        assert report['final_hit_headshot'] is None
        roster={p['id']:p for p in report['participants']}
        assert roster['b']['location']=={'x':100,'y':200}
        assert roster['a']['location']=={'x':10,'y':20}
        assert roster['absent']['location'] is None
        assert c.get('/api/v1/events',params={**scope,'match_id':'guided-two'}).json()['summary']['events']==0
        assert c.get('/api/v1/events',params={**scope,'round_num':2}).status_code==422
        assert c.get('/api/v1/events',params={**scope,'match_id':'guided-one','round_num':99}).json()['items']==[]
        # Multiple championships combine with OR, and allow seeing events before team/player selection.
        both=c.get('/api/v1/events',params=[('map_id','guided-map'),('competition','League/A'),('competition','League/B')]).json()
        assert both['summary']['events']==4
    # Source payload drives spike visibility, including events before plant and after defuse.
    from types import SimpleNamespace
    from app.main import event_report
    match=SimpleNamespace(payload=d,team_mapping={'teams':{'Red':'alpha','Blue':'beta'}},competition='League/A',map_name='haven',source='test')
    ev=SimpleNamespace(id='e',match_id='guided-one',round_num=1,time_ms=20000,game_time_ms=20000,category='enemy',detail=report)
    assert event_report(ev,match)['spike_location'] is None
    ev.time_ms=30000;r2['bombDefuser']='a';r2['defuseRoundTime']=29000
    assert event_report(ev,match)['spike_location'] is None
