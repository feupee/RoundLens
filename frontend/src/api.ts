export type Point = {x:number;y:number};
export type Marker = {id:string;event_id:string;player_id:string;player_name:string;team:string;side:string;kind:'kill'|'death';time_ms:number;x:number|null;y:number|null};
export type RoundResult = {round:number;winner:string|null;outcome:'win'|'loss'|'unknown'};
export type Catalog = {maps:{id:string;name:string}[];competitions:string[];teams:string[];players:{id:string;name:string}[];matches:{id:string;name:string;source:string}[];rounds:number[];round_timeline:RoundResult[]};
export type Content = {agents:Record<string,{name:string;image:string;abilities:Record<string,string>}>;weapons:Record<string,{name:string}>;gear?:Record<string,{name:string}>};
export type Participant = {id:string;name:string;agent_id:string;team_id:string;team:string;location:Point|null};
export type Damage = {attacker_id:string;attacker_name:string;damage:number;headshots:number;bodyshots:number;legshots:number};
export type SpikeState = 'defused'|'planted'|'not_planted';
export type Person = {id:string;name:string;agent_id:string;team:string;side:string;economy:Record<string,number|string>|null};
export type Detail = {id:string;match_id:string;round:number;time_ms:number;game_time_ms:number;category:string;competition:string;map:string;source:string;killer:Person|null;victim:Person|null;assistants:{name:string}[];killer_location:Point|null;victim_location:Point;positions:{puuid:string;location:Point;viewRadians:number}[];finishing_damage:{damageType:string;damageItem:string;isSecondaryFireMode:boolean};post_plant:boolean;plant_site:string|null;since_plant_ms:number|null;round_result:string;round_winner:string;participants:Participant[];score:{team:string;rounds:number}[];spike_location:Point|null;spike_state:SpikeState;damage_report:Damage[];final_hit_headshot:boolean|null};
export type Summary = {markers:number;events:number;kills:number;deaths:number;missing_positions:number};
export type Page = {items:Marker[];next_cursor:string|null;summary:Summary};
export async function get<T>(path:string, signal?:AbortSignal):Promise<T>{
 const base=(import.meta as unknown as {env:Record<string,string>}).env.VITE_API_URL||'';
 const r=await fetch(base+path,{signal});if(!r.ok){const d=await r.json().catch(()=>null);throw new Error(typeof d?.detail==='string'?d.detail:`Falha na API (${r.status}). Verifique o backend.`);}return r.json();
}
export function time(ms:number){return `${Math.floor(ms/60000).toString().padStart(2,'0')}:${((ms%60000)/1000).toFixed(3).padStart(6,'0')}`;}
export function sideLabel(s:string){return s==='Attacker'?'Atacante':s==='Defender'?'Defensor':'Não identificado';}
