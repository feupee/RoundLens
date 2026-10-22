import test from 'node:test';
import assert from 'node:assert/strict';
import {blankFilters,changeFilter,eventParams} from './filters.ts';

const active=()=>({...blankFilters(),map:'haven',competition:['A','B'],team:'Alpha',player:['p1'],side:['Defender'],match:'m1',round:'2'});
test('changing upstream choices clears dependent filters',()=>{
 const map=changeFilter(active(),'map','lotus');
 assert.deepEqual([map.competition,map.team,map.player,map.side,map.match,map.round],[[],'',[],[],'','']);
 const competition=changeFilter(active(),'competition',['B']);
 assert.equal(competition.map,'haven');assert.equal(competition.team,'');assert.equal(competition.match,'');
 const team=changeFilter(active(),'team','Beta');
 assert.deepEqual([team.player,team.side,team.match,team.round],[[],[],'','']);
 assert.equal(changeFilter(active(),'match','m2').round,'');
});
test('championship-only selection and side without player produce correct queries',()=>{
 const f={...blankFilters(),map:'haven',competition:['A','B']};
 const p=eventParams(f);
 assert.deepEqual(p.getAll('competition'),['A','B']);assert.equal(p.has('team'),false);
 const side=eventParams({...f,team:'Alpha',side:['Attacker']});
 assert.equal(side.get('side'),'Attacker');assert.equal(side.has('player'),false);
});
test('match and human round number are sent together',()=>{
 const p=eventParams(active());
 assert.equal(p.get('match_id'),'m1');assert.equal(p.get('round_num'),'2');
 assert.equal(eventParams({...active(),match:''}).has('round_num'),false);
});
