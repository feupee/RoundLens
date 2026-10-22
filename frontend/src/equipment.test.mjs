import test from 'node:test';
import assert from 'node:assert/strict';
import {equipmentSummary} from './equipment.ts';

const content={agents:{},weapons:{weapon:{name:'Operator'}},gear:{armor:{name:'Escudos pesados'}}};
test('round equipment resolves IDs without inventing utility spend',()=>{
 const e=equipmentSummary({economy:{weapon:'WEAPON',armor:'ARMOR',loadoutValue:5500,spent:1000,remaining:0}},content);
 assert.equal(e.weapon,'Operator');assert.equal(e.armor,'Escudos pesados');
 assert.equal(e.spent,1000);assert.equal(e.remaining,0);assert.equal(e.utilitySpent,null);
});
test('missing equipment is distinguished from no armor and zero spend',()=>{
 const absent=equipmentSummary(null,content);
 assert.equal(absent.armor,'Não informado');assert.equal(absent.spent,null);
 const noArmor=equipmentSummary({economy:{armor:'',spent:0}},content);
 assert.equal(noArmor.armor,'Sem colete');assert.equal(noArmor.spent,0);
 assert.equal(equipmentSummary({economy:{armor:'unknown'}},content).armor,'Colete não identificado');
});
