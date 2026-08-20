
import {useEffect,useState} from "react";
import {getCustomers} from "../api/client";
import {Users,Repeat2,UserRoundCheck,HeartHandshake} from "lucide-react";
const nf=(n:number)=>new Intl.NumberFormat("fa-IR").format(Math.round(n||0));
export default function Customers({merchant}:{merchant:string}){
 const [d,setD]=useState<any>();useEffect(()=>{if(merchant)getCustomers(merchant).then(setD)},[merchant]);if(!d)return <div className="skeleton"/>;
 const segments=[["VIP",d.vip,Users],["Loyal",d.loyal,HeartHandshake],["New",d.new_customers,UserRoundCheck]];
 return <><div className="page-head"><div><span className="eyebrow">CUSTOMER ANALYTICS</span><h1>تحلیل رفتار مشتری</h1><p>تحلیل بر پایه payer_card_key شبه‌ناشناس؛ بدون نمایش هویت واقعی مشتری.</p></div></div><div className="grid three"><div className="card"><div className="kpi-top"><span>مشتریان</span><Users size={18}/></div><strong className="big">{nf(d.customers)}</strong></div><div className="card"><div className="kpi-top"><span>نرخ بازگشت</span><Repeat2 size={18}/></div><strong className="big">{Number(d.repeat_rate||0).toFixed(1)}٪</strong></div><div className="card"><div className="kpi-top"><span>میانگین سفارش</span><Repeat2 size={18}/></div><strong className="big">{Number(d.avg_orders||0).toFixed(2)}</strong></div></div><div className="grid three section">{segments.map(([name,count,Icon])=><div className="card segment" key={name}><Icon size={20}/><span>{name}</span><strong>{nf(Number(count))}</strong><div className="progress"><i style={{width:`${d.customers?Number(count)/d.customers*100:0}%`}}/></div></div>)}</div><div className="card section"><h2>RFM-ready</h2><p className="muted">Recency / Frequency / Monetary از داده‌های پرداخت قابل استخراج است. در این نسخه، segmentation پایه نمایش داده شده و ساختار API برای توسعه RFM کامل آماده است.</p></div></>
}
