import {useState} from "react";
import type {ReactNode} from "react";
import {Bot,Sparkles,Database,AlertCircle} from "lucide-react";
import {askMerchant} from "../api/client";

// Renders the LLM's Markdown-ish reply (**bold**, ### headings, - lists)
// as real elements instead of showing the raw *** and # characters.
function inline(text:string,key:string|number){
 const parts=text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
 return <>{parts.map((p,i)=>p.startsWith("**")&&p.endsWith("**")
   ?<strong key={`${key}-${i}`}>{p.slice(2,-2)}</strong>
   :<span key={`${key}-${i}`}>{p}</span>)}</>;
}
function AnswerText({text}:{text:string}){
 const lines=text.replace(/\r\n/g,"\n").split("\n");
 const blocks:ReactNode[]=[];
 let list:string[]=[];
 const flushList=()=>{
  if(list.length){blocks.push(<ul className="answer-list" key={`ul-${blocks.length}`}>{list.map((li,i)=><li key={i}>{inline(li,i)}</li>)}</ul>);list=[]}
 };
 lines.forEach((raw,idx)=>{
  const line=raw.trim();
  if(!line){flushList();return}
  const heading=line.match(/^#{2,4}\s+(.*)/);
  const bullet=line.match(/^[-*]\s+(.*)/);
  if(heading){flushList();blocks.push(<h4 className="answer-heading" key={`h-${idx}`}>{inline(heading[1],idx)}</h4>)}
  else if(bullet){list.push(bullet[1])}
  else{flushList();blocks.push(<p className="answer-p" key={`p-${idx}`}>{inline(line,idx)}</p>)}
 });
 flushList();
 return <div className="answer-body">{blocks}</div>;
}

export default function Assistant({merchant}:{merchant:string}){
 const [q,setQ]=useState(""),[a,setA]=useState<any>(),[loading,setLoading]=useState(false),[error,setError]=useState("");
 const ask=async()=>{
  if(!q.trim()||!merchant)return;
  setLoading(true);setError("");
  try{setA(await askMerchant(merchant,q.trim()))}catch(e:any){setError(e.message||"خطا در اتصال به مدل")}
  finally{setLoading(false)}
 };
 const prompts=["چرا نرخ موفقیت پایین است؟","فروش موفق من چقدر است؟","چقدر پرداخت از دست رفته دارم؟","کدام PSP عملکرد بهتری دارد؟"];
 return <>
  <div className="page-head"><div><span className="eyebrow">LLM ANALYST</span><h1>دستیار تحلیلی هوشمند</h1><p>پاسخ‌ها مستقیماً با داده‌های DuckDB همین پذیرنده تغذیه می‌شوند؛ مدل اجازه ساختن آمار ندارد.</p></div></div>
  <div className="grid two">
   <div className="card assistant">
    <div className="assistant-head"><div className="bot"><Bot size={21}/></div><div><b>Merchant Analyst</b><small>LLM + DuckDB Evidence</small></div></div>
    <div className="chat">
      <div className="bubble bot-bubble">سلام. درباره فروش، موفقیت پرداخت، Retry، PSP یا مشتری‌ها سؤال بپرسید. پاسخ فقط بر اساس دیتای واقعی پذیرنده ساخته می‌شود.</div>
      {a&&<div className="bubble user-bubble"><AnswerText text={a.answer}/><small><Database size={13}/> مدل: {a.model} · پاسخ مبتنی بر داده‌های DuckDB</small></div>}
      {error&&<div className="error-box"><AlertCircle size={16}/>{error}</div>}
    </div>
    <div className="askbar"><input value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&ask()} placeholder="مثلاً: در کدام ساعت‌ها نرخ موفقیت افت می‌کند؟"/><button onClick={ask} disabled={loading}>{loading?"در حال تحلیل…":"بپرس"}</button></div>
   </div>
   <div className="card"><h2>سؤالات پیشنهادی</h2>{prompts.map(p=><button className="prompt" key={p} onClick={()=>setQ(p)}><Sparkles size={15}/>{p}</button>)}<div className="callout"><b>Grounded LLM</b><p>قبل از فراخوانی مدل، خلاصه KPI، روند ۳۰ روزه، ساعت‌ها، PSPها، مشتری‌ها و Insightهای همین پذیرنده از DuckDB خوانده می‌شود.</p></div></div>
  </div>
 </>
}
