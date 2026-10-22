import test from 'node:test';
import assert from 'node:assert/strict';
import {projectImage,zoomAt} from './mapGeometry.ts';

const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-8, `${a} != ${b}`);
test('world axes, normalized image and aspect-preserving frame agree',()=>{
 const matrix=[0,.00007,.813895,-.00007,0,.573242];
 const frame={x:140,y:20,width:520,height:520};
 const p=projectImage({x:1000,y:-2000},matrix,frame);
 near(p.x,140+.673895*520);
 near(p.y,20+.503242*520);
 const origin=projectImage({x:0,y:0},matrix,frame);
 assert.ok(p.x<origin.x && p.y<origin.y);
});
test('zoom retains the anchor after panning and returns to original viewport',()=>{
 const pan={x:-120,y:55}, anchor={x:321,y:207}, zoom=1.5;
 const next=zoomAt(zoom,pan,zoom*1.1,anchor);
 const world={x:(anchor.x-pan.x)/zoom,y:(anchor.y-pan.y)/zoom};
 near(world.x*next.zoom+next.pan.x,anchor.x);
 near(world.y*next.zoom+next.pan.y,anchor.y);
 const back=zoomAt(next.zoom,next.pan,zoom,anchor);
 near(back.pan.x,pan.x);near(back.pan.y,pan.y);
});
test('zoom limits preserve anchor and do not drift when already limited',()=>{
 for(const limit of [.5,8]){
  const pan={x:70,y:-30},anchor={x:400,y:280};
  const next=zoomAt(limit,pan,limit===8?100:.01,anchor);
  assert.deepEqual(next,{zoom:limit,pan});
 }
});
