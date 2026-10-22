import {Content,Person} from './api';
import {equipmentSummary} from './equipment';

const credits=(value:number|null)=>value===null?'Não informado':`${value.toLocaleString('pt-BR')} créditos`;
export default function Equipment({killer,victim,content}:{killer:Person|null;victim:Person|null;content:Content}){
 return <section className="equipment-report"><h3>Equipamento do round</h3><p>Dados registrados no round; a arma pode mudar até o instante do abate.</p><div className="equipment-cards">{[killer,victim].map((p,i)=>{const e=equipmentSummary(p,content);return <article key={i}><h4 className={i===0?'green':'red'}>{i===0?'Quem abateu':'Vítima'}</h4><p>{p?.name||'Não identificado'}</p><dl><dt>Arma</dt><dd>{e.weapon}</dd><dt>Colete</dt><dd>{e.armor}</dd><dt>Valor do equipamento</dt><dd>{credits(e.loadout)}</dd><dt>Gasto total no round</dt><dd>{credits(e.spent)}</dd><dt>Gasto com utilitários</dt><dd>{credits(e.utilitySpent)}</dd><dt>Créditos restantes</dt><dd>{credits(e.remaining)}</dd></dl></article>;})}</div><small>A fonte não separa o gasto com utilitários do gasto total.</small></section>;
}
