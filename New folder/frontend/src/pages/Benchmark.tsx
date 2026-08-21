
import {useEffect,useState} from "react";
import {getMerchant,getPeers} from "../api/client";
import {GitCompareArrows,Medal} from "lucide-react";
const nf=(n:number)=>new Intl.NumberFormat("fa-IR").format(Math.round(n||0));
const pct=(n:number)=>`${(Number(n||0)*100).toFixed(1)}٪`;
const money=(n:number)=>nf(n)+" ریال";
export default function Benchmark({merchant}:{merchant:string}){
 const [m,setM]=useState<any>(),[peers,setPeers]=useState<any[]>([]);
 useEffect(()=>{if(merchant){getMerchant(merchant).then(setM);getPeers(merchant).then(setPeers)}},[merchant]);
 if(!m)return <div className="skeleton"/>;
 const own=m.merchant,peer=m.peer||{};
 return <><div className="page-head"><div><span className="eyebrow">BENCHMARK</span><h1>مقایسه با هم‌صنف‌ها</h1><p>رتبه‌بندی بر اساس category و معیارهای عملکرد پرداخت</p></div></div>
 <div className="grid three"><div className="card benchmark-score"><Medal size={22}/><strong>{Math.round((peer.success_rate_percentile||0)*100)}</strong><span>صدک نرخ موفقیت</span></div><div className="card"><small>نرخ موفقیت پذیرنده</small><strong className="big">{pct(own.final_success_rate)}</strong><span className="muted">میانه هم‌صنف قابل مشاهده در جدول</span></div><div className="card"><small>AOV پذیرنده</small><strong className="big">{money(own.aov)}</strong><span className="muted">صدک AOV: {Math.round((peer.aov_percentile||0)*100)}٪</span></div></div>
 <div className="card section"><div className="card-head"><h2>پذیرندگان هم‌صنف</h2><GitCompareArrows size={18}/></div><div className="table-scroll"><table><thead><tr><th>پذیرنده</th><th>Session</th><th>فروش موفق</th><th>AOV</th><th>Success</th><th>صدک</th></tr></thead><tbody>{peers.map((p:any)=><tr className={p.merchant_key===merchant?"selected":""} key={p.merchant_key}><td>{p.merchant_key}</td><td>{nf(p.sessions)}</td><td>{money(p.successful_volume)}</td><td>{money(p.aov)}</td><td>{pct(p.final_success_rate)}</td><td>{Math.round((p.success_rate_percentile||0)*100)}٪</td></tr>)}</tbody></table></div></div>
 </>;
}
