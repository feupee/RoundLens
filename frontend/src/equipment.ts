import type {Content,Person} from './api.ts';

export function equipmentSummary(person:Person|null,content:Content){
 const e=person?.economy;
 const weapon=typeof e?.weapon==='string'?e.weapon.toLowerCase():null;
 const armor=typeof e?.armor==='string'?e.armor.toLowerCase():null;
 const amount=(key:string)=>typeof e?.[key]==='number'&&Number.isFinite(e[key])?Number(e[key]):null;
 return {
  weapon:weapon?content.weapons[weapon]?.name||'Arma não identificada':'Não informado',
  armor:armor===''?'Sem colete':armor?content.gear?.[armor]?.name||'Colete não identificado':'Não informado',
  loadout:amount('loadoutValue'),spent:amount('spent'),remaining:amount('remaining'),
  // Total spend includes other purchases. Carried/dropped weapons and armor
  // repairs prevent inferring utility purchases by subtracting catalog prices.
  utilitySpent:null,
 };
}
