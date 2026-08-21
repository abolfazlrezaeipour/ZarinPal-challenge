
import {useEffect,useState} from "react";
import {getCustomers} from "../api/client";
import {Users,Repeat2,UserRoundCheck,HeartHandshake,Crown,ShoppingCart,Wallet,Star,ReceiptText,CalendarDays,Trophy,Sparkles,History} from "lucide-react";
import KPI from "../components/KPI";

const nf=(n:any)=>new Intl.NumberFormat("fa-IR").format(Math.round(Number(n)||0));
const num=(v:any)=>Number(v)||0;
const money=(n:any)=>nf(n)+" ریال";
const dt=(v:any)=>{
 if(!v)return "—";
 const d=new Date(v);
 return isNaN(d.getTime())?String(v):new Intl.DateTimeFormat("fa-IR",{dateStyle:"medium"}).format(d);
};

function Loading(){return <div className="skeleton"/>}

function TopCard({title,data,icon:Icon,rank,valueLabel,secondaryLabel}:{title:string,data:any,icon:any,rank:number,valueLabel:string,secondaryLabel?:string}){
 if(!data)return null;
 const name=data.customer??data.payer_card_key??"—";
 return <div className="card top-customer-card">
  <div className="top-customer-icon"><Icon size={18}/></div>
  <div className="top-customer-rank">{rank===1?<Crown size={13}/>:<Trophy size={13}/>} رتبه {nf(rank)}</div>
  <span className="muted">{title}</span>
  <strong>{name}</strong>
  <small>{valueLabel}</small>
  {secondaryLabel&&<small>{secondaryLabel}</small>}
  {data.date&&<small><CalendarDays size={11}/> {dt(data.date)}</small>}
 </div>;
}

export default function Customers({merchant}:{merchant:string}){
 const [d,setD]=useState<any>();
 useEffect(()=>{if(merchant){setD(undefined);getCustomers(merchant).then(setD).catch(()=>setD({}))}},[merchant]);
 if(!d)return <Loading/>;

 const total=num(d.customers);
 const segments=[
  ["VIP (۵+ خرید)",d.vip,Crown],
  ["وفادار (۲ تا ۴ خرید)",d.loyal,HeartHandshake],
  ["خرید اول",d.new_customers,UserRoundCheck],
 ];
 const hasTopCards=d.top_customer_by_revenue||d.top_customer_by_orders||d.top_order_by_amount;
 const hasRecency=d.newest_customer||d.longest_tenure_customer;

 return <>
  <div className="page-head">
   <div>
    <span className="eyebrow">CUSTOMER ANALYTICS</span>
    <h1>تحلیل رفتار مشتری</h1>
    <p>تمام شاخص‌های این صفحه مستقیماً از تراکنش‌ها و شناسه شبه‌ناشناس مشتری (payer_card_key) محاسبه شده‌اند؛ بدون نمایش هویت واقعی.</p>
   </div>
  </div>

  <div className="grid kpi-grid">
   <KPI title="تعداد کل مشتریان" value={nf(total)} icon={<Users size={17}/>}/>
   <KPI title="مشتریان بازگشتی" value={nf(d.repeat_customers)} subtitle={`نرخ بازگشت ${num(d.repeat_rate).toFixed(1)}٪`} icon={<Repeat2 size={17}/>}/>
   <KPI title="میانگین تعداد سفارش" value={num(d.avg_orders).toFixed(2)} icon={<ShoppingCart size={17}/>}/>
   <KPI title="میانگین مبلغ خرید" value={money(d.avg_purchase)} icon={<Wallet size={17}/>}/>
  </div>

  {hasTopCards&&<div className="section">
   <div className="card-head"><div><span className="eyebrow">TOP CUSTOMERS</span><h2>مشتریان برتر</h2></div><Trophy size={20}/></div>
   <div className="grid three">
    <TopCard title="بیشترین مجموع خرید" data={d.top_customer_by_revenue} icon={Wallet} rank={1} valueLabel={money(d.top_customer_by_revenue?.amount)}/>
    <TopCard title="بیشترین تعداد سفارش" data={d.top_customer_by_orders} icon={ShoppingCart} rank={2} valueLabel={`${nf(d.top_customer_by_orders?.orders)} سفارش موفق`}/>
    <TopCard title="بزرگ‌ترین سفارش تکی" data={d.top_order_by_amount} icon={ReceiptText} rank={3} valueLabel={money(d.top_order_by_amount?.amount)} secondaryLabel={d.top_order_by_amount?.session_key?`شناسه: ${d.top_order_by_amount.session_key}`:undefined}/>
   </div>
  </div>}

  {hasRecency&&<div className="section">
   <div className="card-head"><div><span className="eyebrow">RECENCY & LOYALTY</span><h2>تازگی و سابقه مشتریان</h2></div><History size={20}/></div>
   <div className="grid two">
    <div className="card">
     <div className="kpi-top"><span>تازه‌ترین مشتری</span><i><Sparkles size={16}/></i></div>
     <strong className="big">{d.newest_customer?.customer??"—"}</strong>
     <span className="muted">اولین خرید: {dt(d.newest_customer?.date)}</span>
    </div>
    <div className="card">
     <div className="kpi-top"><span>باسابقه‌ترین مشتری وفادار</span><i><HeartHandshake size={16}/></i></div>
     <strong className="big">{d.longest_tenure_customer?.customer??"—"}</strong>
     <span className="muted">
      {d.longest_tenure_customer
       ?`${nf(d.longest_tenure_customer.tenure_days)} روز سابقه خرید · ${nf(d.longest_tenure_customer.orders)} سفارش موفق`
       :"داده‌ای برای نمایش موجود نیست"}
     </span>
    </div>
   </div>
  </div>}

  <div className="section">
   <div className="card-head"><div><span className="eyebrow">SEGMENTATION</span><h2>تقسیم‌بندی بر اساس تعداد خرید</h2></div><Star size={20}/></div>
   <div className="grid three">
    {segments.map(([name,count,Icon]:any)=>
     <div className="card segment" key={name}>
      <Icon size={20}/>
      <span>{name}</span>
      <strong>{nf(count)}</strong>
      <div className="progress"><i style={{width:`${total?Math.min(num(count)/total*100,100):0}%`}}/></div>
     </div>
    )}
   </div>
  </div>
 </>;
}
