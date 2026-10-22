export type Filters={map:string;competition:string[];team:string;player:string[];side:string[];kind:string[];start:string;end:string;match:string;round:string};
export const blankFilters=():Filters=>({map:'',competition:[],team:'',player:[],side:[],kind:['kill','death'],start:'0',end:'',match:'',round:''});
export function changeFilter<K extends keyof Filters>(f:Filters,key:K,value:Filters[K]):Filters {
 const next={...f,[key]:value};
 if(key==='map')Object.assign(next,{competition:[],team:'',player:[],side:[],match:'',round:''});
 if(key==='competition')Object.assign(next,{team:'',player:[],side:[],match:'',round:''});
 if(key==='team')Object.assign(next,{player:[],side:[],match:'',round:''});
 if(key==='match')next.round='';
 return next;
}
export function catalogParams(f:Filters) {
 const p=new URLSearchParams();
 if(f.map)p.set('map_id',f.map);
 f.competition.forEach(v=>p.append('competition',v));
 if(f.team)p.set('team',f.team);
 if(f.match)p.set('match_id',f.match);
 return p;
}
export function eventParams(f:Filters) {
 const p=catalogParams(f);
 f.player.forEach(v=>p.append('player',v));
 f.side.forEach(v=>p.append('side',v));
 f.kind.forEach(v=>p.append('kind',v));
 p.set('start_ms',String(Math.round(Number(f.start)*1000)));
 if(f.end!=='')p.set('end_ms',String(Math.round(Number(f.end)*1000)));
 if(f.match&&f.round)p.set('round_num',f.round);
 return p;
}
