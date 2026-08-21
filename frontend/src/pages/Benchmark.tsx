
import {useEffect,useState} from "react";
import {getMerchant,getPeers} from "../api/client";
import {GitCompareArrows,Medal,Layers,Banknote,Percent,Wallet} from "lucide-react";
import KPI from "../components/KPI";
const nf=(n:number)=>new Intl.NumberFormat("fa-IR").format(Math.round(n||0));
const pct=(n:number)=>`${(Number(n||0)*100).toFixed(1)}٪`;
const money=(n:number)=>nf(n)+" ریال";
export default function Benchmark({merchant}:{merchant:string}){
 const [m,setM]=useState<any>(),[peers,setPeers]=useState<any[]>([]);
 useEffect(()=>{if(merchant){getMerchant(merchant).then(setM);getPeers(merchant).then(setPeers)}},[merchant]);
 if(!m)return <div className="skeleton"/>;
 const own=m.merchant,peer=m.peer||{};
 const ranked=[...peers].sort((a:any,b:any)=>Number(b.final_success_rate||0)-Number(a.final_success_rate||0));
 const ownRank=Math.max(1,ranked.findIndex((p:any)=>p.merchant_key===merchant)+1);
 const totalPeers=ranked.length;
 const rankText=totalPeers?`${nf(ownRank)} از ${nf(totalPeers)}`:"—";
 return <>
  <div className="page-head">
   <div><span className="eyebrow">BENCHMARK</span><h1>مقایسه با هم‌صنف‌ها</h1><p>رتبه‌بندی بر اساس category و معیارهای عملکرد پرداخت</p></div>
  </div>

  <div className="grid two">
   <div className="card benchmark-score"><Medal size={22}/><strong>{rankText}</strong><span>رتبه پذیرنده بین هم‌صنف‌ها</span></div>
   <div className="card benchmark-score"><Medal size={22}/><strong>{Math.round((peer.success_rate_percentile||0)*100)}</strong><span>صدک نرخ موفقیت</span></div>
  </div>

  <div className="grid kpi-grid section">
   <KPI title="Session پذیرنده" value={nf(own.sessions)} subtitle="تعداد کل Sessionهای ثبت‌شده" icon={<Layers size={17}/>}/>
   <KPI title="فروش موفق پذیرنده" value={money(own.successful_volume)} subtitle="مجموع تراکنش‌های موفق" icon={<Banknote size={17}/>}/>
   <KPI title="نرخ موفقیت پذیرنده" value={pct(own.final_success_rate)} subtitle="میانه هم‌صنف در جدول زیر" icon={<Percent size={17}/>}/>
   <KPI title="AOV پذیرنده" value={money(own.aov)} subtitle={`صدک AOV: ${Math.round((peer.aov_percentile||0)*100)}٪`} icon={<Wallet size={17}/>}/>
  </div>

  <div className="card section">
   <div className="card-head"><h2>پذیرندگان هم‌صنف</h2><GitCompareArrows size={18}/></div>
   <div className="table-scroll">
    <table>
     <thead><tr><th>رتبه</th><th>پذیرنده</th><th>Session</th><th>فروش موفق</th><th>AOV</th><th>Success</th><th>صدک</th></tr></thead>
     <tbody>
      {ranked.map((p:any,i:number)=>
       <tr className={p.merchant_key===merchant?"selected":""} key={p.merchant_key}>
        <td><strong>{nf(i+1)}</strong>{p.merchant_key===merchant&&<span className="muted"> (شما)</span>}</td>
        <td>{p.merchant_key}</td>
        <td>{nf(p.sessions)}</td>
        <td>{money(p.successful_volume)}</td>
        <td>{money(p.aov)}</td>
        <td>{pct(p.final_success_rate)}</td>
        <td>{Math.round((p.success_rate_percentile||0)*100)}٪</td>
       </tr>
      )}
     </tbody>
    </table>
   </div>
   <p className="muted" style={{marginTop:12}}>رتبه‌بندی بر اساس نرخ موفقیت نهایی انجام شده است. پذیرنده فعلی با برچسب «شما» مشخص شده است.</p>
  </div>
 </>;
}
