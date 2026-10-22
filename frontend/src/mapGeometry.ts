export type XY = {x:number;y:number};

// Image coordinates are normalized; keep the image and every overlay in the
// same coordinate space before applying the viewport transform.
export function projectImage(p:XY, matrix:number[], frame:{x:number;y:number;width:number;height:number}):XY {
 const [a,b,c,d,e,f]=matrix;
 return {x:frame.x+(a*p.x+b*p.y+c)*frame.width,y:frame.y+(d*p.x+e*p.y+f)*frame.height};
}

export function zoomAt(zoom:number, pan:XY, requested:number, anchor:XY) {
 const next=Math.max(.5,Math.min(8,requested));
 const ratio=next/zoom;
 return {zoom:next,pan:{x:anchor.x-(anchor.x-pan.x)*ratio,y:anchor.y-(anchor.y-pan.y)*ratio}};
}
