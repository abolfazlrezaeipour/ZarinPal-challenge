
import {useEffect,useState} from "react";
import {getInsights,getInsightDetail,getEvidence} from "../api/client";
import {BrainCircuit,ExternalLink} from "lucide-react";
const money=(n:number)=>new Intl.NumberFormat("fa-IR").format(Math.round(n||0))+" ریال";
export default function Insights({merchant}:{merchant:string}){
 const [rows,setRows]=useState<any[]>([]),[detail,setDetail]=useState<any>();
 useEffect(()=>{if(merchant)getInsights(merchant).then(setRows)},[merchant]);
 const open=async(i:any)=>{const d=await getInsightDetail(merchant,i.insight_type);const e=await getEvidence(merchant,i.insight_type);setDetail({...d,evidence:e})};
 return <><div className="page-head"><div><span className="eyebrow">INTELLIGENCE</span><h1>Insightهای هوشمند</h1><p>هر توصیه از یک Metric مشخص و شواهد قابل ردیابی ساخته شده است.</p></div></div>
 <div className="insight-grid">{rows.map(i=><button className="insight-card" key={i.insight_type} onClick={()=>open(i)}><div className="insight-icon"><BrainCircuit size={18}/></div><span className={"severity "+i.severity}>{i.severity}</span><h3>{i.title}</h3><p>{i.summary}</p><div className="recommend">{i.recommendation}</div><small>Metric: {i.metric_name} · {i.metric_name.includes("volume")?money(i.metric_value):(Number(i.metric_value)*100).toFixed(1)+"%"}</small><ExternalLink size={15}/></button>)}</div>
 {detail&&<div className="modal-backdrop" onClick={()=>setDetail(null)}><div className="modal" onClick={e=>e.stopPropagation()}><div className="modal-head"><div><span className="eyebrow">EVIDENCE</span><h2>{detail.insight.title}</h2></div><button className="icon-btn" onClick={()=>setDetail(null)}>×</button></div><div className="formula"><b>فرمول</b><code>{detail.methodology?.formula}</code><p>{detail.methodology?.definition}</p><small>{detail.methodology?.filters}</small></div><div className="table-scroll"><table><thead><tr><th>Session</th><th>مبلغ</th><th>Attempt</th><th>وضعیت</th></tr></thead><tbody>{detail.evidence?.map((s:any)=><tr key={s.session_key}><td>{s.session_key}</td><td>{money(s.amount)}</td><td>{s.attempt_count}</td><td>{s.session_status}</td></tr>)}</tbody></table></div></div></div>}
 </>;
}
