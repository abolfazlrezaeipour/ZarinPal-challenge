
import React,{useState} from "react";
import Sidebar from "./Sidebar";
import {Menu,RefreshCw,Sun,Moon} from "lucide-react";

export default function Layout({children,page,setPage,dark,setDark,merchant,setMerchant,merchants}:{children:React.ReactNode,page:string,setPage:(x:string)=>void,dark:boolean,setDark:(x:boolean)=>void,merchant:string,setMerchant:(x:string)=>void,merchants:any[]}){
 const [open,setOpen]=useState(false);
 return <div className="shell">
  <Sidebar page={page} setPage={setPage} open={open} setOpen={setOpen}/>
  <main className="main">
   <header className="topbar">
    <button className="icon-btn mobile" onClick={()=>setOpen(true)}><Menu size={18}/></button>
    <div className="top-title"><b>هوش کسب‌وکار زرین‌پال</b><span>Merchant Intelligence · تحلیل داده‌های پرداخت</span></div>
    <div className="top-actions">
      <div className="select-wrap merchant-select"><select value={merchant} onChange={e=>setMerchant(e.target.value)}>{merchants.map(m=><option key={m.merchant_key} value={m.merchant_key}>{m.merchant_key} · {m.category_title||"پذیرنده"}</option>)}</select></div>
      <button className="icon-btn" onClick={()=>setDark(!dark)}>{dark?<Sun size={17}/>:<Moon size={17}/>}</button>
      <button className="icon-btn" onClick={()=>location.reload()}><RefreshCw size={17}/></button>
    </div>
   </header>
   <div className="content">{children}</div>
  </main>
 </div>
}
