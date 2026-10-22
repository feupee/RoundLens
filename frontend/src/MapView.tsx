import {useEffect,useRef,useState} from 'react';
import {Stage,Layer,Group,Image as CanvasImage,Circle,Line,Text,Rect} from 'react-konva';
import {Expand,Minus,Plus,Settings2} from 'lucide-react';
import {Content,Detail,Marker,Point,time} from './api';
import {projectImage,zoomAt} from './mapGeometry';

type Calibration={image:string;matrix:number[];name?:string};
const validCalibration=(c:Calibration)=>typeof c.image==='string'&&c.matrix?.length===6&&c.matrix.every(Number.isFinite)&&Math.abs(c.matrix[0]*c.matrix[4]-c.matrix[1]*c.matrix[3])>1e-15;
function AgentPortrait({src,point,zoom,color,label,onHover}:{src?:string;point:Point;zoom:number;color:string;label:string;onHover:(s:string)=>void}){
 const [portrait,setPortrait]=useState<HTMLImageElement|null>(null);
 useEffect(()=>{setPortrait(null);if(!src)return;const image=new window.Image();image.onload=()=>setPortrait(image);image.src=src;return()=>{image.onload=null;};},[src]);
 return <Group x={point.x} y={point.y} scaleX={1/zoom} scaleY={1/zoom} onMouseEnter={()=>onHover(label)} onMouseLeave={()=>onHover('')} onClick={()=>onHover(label)} onTap={()=>onHover(label)}><Rect x={-15} y={-15} width={30} height={30} cornerRadius={4} fill="#0b1018" stroke={color} strokeWidth={2}/>{portrait?<CanvasImage image={portrait} x={-12} y={-12} width={24} height={24}/>:<Text x={-7} y={-7} text="?" fill="white" fontSize={16}/>}<Line points={[-3,0,3,0]} stroke="white" strokeWidth={1} listening={false}/><Line points={[0,-3,0,3]} stroke="white" strokeWidth={1} listening={false}/></Group>;
}
export default function MapView({mapId,markers,detail,bounds,content,onSelect}:{mapId:string;markers:Marker[];detail:Detail|null;bounds:(number|null)[];content:Content;onSelect:(id:string)=>void}){
 const box=useRef<HTMLDivElement>(null);const [width,setWidth]=useState(800);const height=560;
 const [catalog,setCatalog]=useState<(Calibration&{mapUrl:string})[]>([]);
 const automatic=catalog.find(m=>m.mapUrl.toLowerCase()===mapId.toLowerCase());
 useEffect(()=>{const controller=new AbortController();fetch('/maps/catalog.json',{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{if(!Array.isArray(data.maps))throw new Error();setCatalog(data.maps.filter((m:Calibration&{mapUrl:string})=>typeof m.mapUrl==='string'&&validCalibration(m)));}).catch(e=>{if(e.name!=='AbortError')setError('Minimapas indisponíveis. Execute scripts/download_maps.py e reconstrua o frontend.');});return()=>controller.abort();},[]);
 const [cal,setCal]=useState<Calibration|null>(null);const [img,setImg]=useState<HTMLImageElement|null>(null);
 const [editing,setEditing]=useState(false);const [draft,setDraft]=useState('0.0001, 0, 0.5, 0, 0.0001, 0.5');const [pendingImage,setPendingImage]=useState('');
 const [error,setError]=useState('');const [viewport,setViewport]=useState({zoom:1,pan:{x:0,y:0}});const {zoom,pan}=viewport;
 const resetView=()=>setViewport({zoom:1,pan:{x:0,y:0}});
 const changeZoom=(factor:number,anchor={x:width/2,y:height/2})=>setViewport(v=>zoomAt(v.zoom,v.pan,v.zoom*factor,anchor));
 const [hits,setHits]=useState<Marker[]>([]);const [hover,setHover]=useState('');
 useEffect(()=>{const ro=new ResizeObserver(e=>setWidth(e[0].contentRect.width));if(box.current)ro.observe(box.current);return ()=>ro.disconnect();},[]);
 useEffect(()=>{setCal(automatic??null);setDraft(automatic?.matrix.join(', ')??'0.0001, 0, 0.5, 0, 0.0001, 0.5');setImg(null);resetView();setHits([]);setPendingImage(automatic?.image??'');setError('');
  try{const raw=localStorage.getItem('roundlens:'+mapId);if(raw){const c=JSON.parse(raw);if(validCalibration(c)){setCal(c);setDraft(c.matrix.join(', '));setPendingImage(c.image);}}}catch{setError('Não foi possível carregar a calibração local.');}
 },[mapId,automatic]);
 useEffect(()=>{setImg(null);if(!cal){setImg(null);return;}const image=new window.Image();image.onload=()=>setImg(image);image.onerror=()=>setError('Imagem inválida');image.src=cal.image;return ()=>{image.onload=null;image.onerror=null;};},[cal]);
 useEffect(()=>setHits([]),[markers]);
 useEffect(()=>setHover(''),[detail?.id]);
 const [xmin,xmax,ymin,ymax]=bounds.map(v=>v??0);const range=Math.max(xmax-xmin,ymax-ymin,1);
 // Imagem preserva proporção; sem asset, plano cartesiano com escala igual nos dois eixos.
 const fit=img?Math.min(Math.max(width-40,1)/img.width,(height-40)/img.height):1;
 const iw=img?img.width*fit:width-60, ih=img?img.height*fit:height-60;
 const ox=(width-iw)/2,oy=(height-ih)/2;
 const project=(p:Point)=>{if(cal&&img){return projectImage(p,cal.matrix,{x:ox,y:oy,width:iw,height:ih});}
 const scale=Math.min(width-80,height-80)/range;return {x:width/2+(p.x-(xmin+xmax)/2)*scale,y:height/2-(p.y-(ymin+ymax)/2)*scale};};
 const located=markers.filter(m=>m.x!==null&&m.y!==null);
 const displayed=detail?located.filter(m=>m.event_id===detail.id):located;
 function choose(m:Marker){const p=project(m as Point);const nearby=located.filter(n=>{const q=project(n as Point);return Math.hypot(q.x-p.x,q.y-p.y)*zoom<10;});setHits(nearby.length>1?nearby:[]);onSelect(m.event_id);}
 function apply(){const matrix=draft.split(',').map(Number);if(matrix.length!==6||matrix.some(x=>!Number.isFinite(x))||Math.abs(matrix[0]*matrix[4]-matrix[1]*matrix[3])<1e-15){setError('Informe seis coeficientes finitos, com transformação não degenerada.');return;}
 if(!pendingImage){setError('Carregue uma imagem antes de aplicar.');return;}const value={image:pendingImage,matrix};try{localStorage.setItem('roundlens:'+mapId,JSON.stringify(value));setCal(value);setEditing(false);setError('');}catch{setError('Não foi possível salvar. Use uma imagem menor (até 2 MB).');}}
 const kp=detail?.killer_location?project(detail.killer_location):null;const vp=detail?project(detail.victim_location):null;
 const spike=detail?.spike_location?project(detail.spike_location):null;
 const referenceTeam=detail?.participants.find(p=>p.id===detail.killer?.id)?.team_id;
 return <div ref={box} className="mapbox">
  <div className="map-toolbar"><span className="badge">{cal?(cal.name?'Minimapa · '+cal.name:'Imagem com calibração manual'):'Plano de coordenadas • sem imagem calibrada'}</span><div><button title="Diminuir zoom" onClick={()=>changeZoom(1/1.25)}><Minus size={15}/></button><button title="Aumentar zoom" onClick={()=>changeZoom(1.25)}><Plus size={15}/></button><button title="Restaurar" onClick={()=>{resetView();}}><Expand size={15}/></button><button title="Configurar mapa" onClick={()=>{if(!editing&&cal){setDraft(cal.matrix.join(', '));setPendingImage(cal.image);}setEditing(!editing);}}><Settings2 size={15}/></button></div></div>
  {editing&&<div className="calibration"><strong>Imagem e calibração deste mapa</strong><p>Use um asset autorizado. u=a·x+b·y+c e v=d·x+e·y+f são coordenadas normalizadas da imagem. Consulte o script de calibração no projeto. Os valores iniciais são exemplos, não uma calibração válida.</p><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>{const f=e.target.files?.[0];if(!f)return;if(f.size>2*1024*1024){setError('Limite: 2 MB');return;}const reader=new FileReader();reader.onload=()=>setPendingImage(String(reader.result));reader.readAsDataURL(f);}}/><label>Coeficientes a, b, c, d, e, f<input value={draft} onChange={e=>setDraft(e.target.value)}/></label><button onClick={apply}>Aplicar calibração</button><button onClick={()=>{localStorage.removeItem('roundlens:'+mapId);setCal(automatic??null);setError('');setEditing(false);}}>Restaurar mapa automático</button><small>Configuração salva apenas neste navegador. Confira pontos de referência antes de analisar.</small></div>}
  {error&&<p className="error">{error}</p>}
  <Stage width={Math.max(width,100)} height={height} draggable scaleX={zoom} scaleY={zoom} x={pan.x} y={pan.y} onDragEnd={e=>{if(e.target===e.target.getStage())setViewport(v=>({...v,pan:{x:e.target.x(),y:e.target.y()}}));}} onWheel={e=>{e.evt.preventDefault();const pointer=e.target.getStage()?.getPointerPosition();if(pointer)changeZoom(e.evt.deltaY>0?1/1.1:1.1,pointer);}}>
   <Layer><Rect width={width} height={height} fill="#0b1018"/>{!img&&Array.from({length:17},(_,i)=><Line key={'v'+i} points={[i*width/16,0,i*width/16,height]} stroke="#1a2330" listening={false}/>)}{!img&&Array.from({length:12},(_,i)=><Line key={'h'+i} points={[0,i*height/11,width,i*height/11]} stroke="#1a2330" listening={false}/>)}
    {img&&<CanvasImage image={img} x={ox} y={oy} width={iw} height={ih} listening={false}/>}
    {!img&&<Text text="POSIÇÕES REGISTRADAS · EIXOS DO JOGO" x={22} y={height-24} fill="#718096" fontSize={10} listening={false}/>}
    {displayed.map(m=>{const p=project(m as Point);const selected=m.event_id===detail?.id;const color=m.kind==='kill'?'#39d98a':'#ff5d73';return <Circle key={m.id} x={p.x} y={p.y} radius={(selected?7:4)/zoom} fill={m.kind==='kill'?color:'#0b1018'} stroke={selected?'white':color} strokeWidth={(selected?2:1.5)/zoom} opacity={selected?1:detail?0.12:0.78} onClick={()=>choose(m)} onTap={()=>choose(m)} onMouseEnter={()=>setHover(`${m.kind==='kill'?'Abate':'Morte'} · ${m.player_name} · ${time(m.time_ms)}`)} onMouseLeave={()=>setHover('')}/>;})}
    {kp&&vp&&<Line points={[kp.x,kp.y,vp.x,vp.y]} stroke="#d7e1f2" dash={[5,5]} strokeWidth={1.5/zoom} listening={false}/>}
    {vp&&<Circle {...vp} radius={23/zoom} stroke="#ff5d73" strokeWidth={2/zoom} listening={false}/>}{kp&&<Circle {...kp} radius={23/zoom} stroke="#39d98a" strokeWidth={2/zoom} listening={false}/>}
    {detail?.participants.filter(p=>p.location).map(p=>{const agent=content.agents[p.agent_id.toLowerCase()];return <AgentPortrait key={detail.id+':'+p.id} src={agent?.image} point={project(p.location!)} zoom={zoom} color={p.team_id===referenceTeam?'#6ab7ff':'#ffb45d'} label={`${p.name} · ${agent?.name||'Agente não identificado'} · ${p.team.replaceAll('_',' ')}${p.id===detail.victim?.id?' · Vítima':p.id===detail.killer?.id?' · Quem abateu':''}`} onHover={setHover}/>;})}
    {spike&&<Group x={spike.x} y={spike.y} scaleX={1/zoom} scaleY={1/zoom} onMouseEnter={()=>setHover(`Spike plantada · ${detail?.plant_site}`)} onMouseLeave={()=>setHover('')}><Circle radius={13} fill="#171b20" stroke="#ffe080" strokeWidth={2}/><Line points={[-5,7,-5,-2,0,-9,5,-2,5,7,0,10]} closed fill="#ffe080" stroke="#ffe080" strokeWidth={1}/><Line points={[0,-3,0,5]} stroke="#171b20" strokeWidth={2}/></Group>}
   </Layer>
  </Stage>
  <div className="map-foot">{hover||(detail?'Posições deste evento · Azul: time de quem abateu · Laranja: adversários · Amarelo: spike. Toque ou passe sobre um retrato para identificar.':'Clique em um marcador para investigar o evento.')}</div>
  {hits.length>1&&<div className="overlaps"><strong>{hits.length} marcadores próximos</strong><button onClick={()=>setHits([])}>Fechar</button><div>{hits.map(m=><button key={m.id} onClick={()=>onSelect(m.event_id)}>{m.kind==='kill'?'●':'○'} {m.player_name} · {time(m.time_ms)}</button>)}</div></div>}
 </div>;
}
