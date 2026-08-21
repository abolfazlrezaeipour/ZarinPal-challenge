
import {LayoutDashboard,BrainCircuit,GitCompareArrows,ReceiptText,Users,ChartNoAxesCombined,Bot,X} from "lucide-react";
const items=[
 ["dashboard","نمای کلی",LayoutDashboard],
 ["analytics","تحلیل فروش و زمان",ChartNoAxesCombined],
 ["insights","Insightهای هوشمند",BrainCircuit],
 ["benchmark","Benchmark صنفی",GitCompareArrows],
 ["sessions","Session Explorer",ReceiptText],
 ["customers","تحلیل مشتری",Users],
 ["assistant","دستیار تحلیلی",Bot],
] as const;
export default function Sidebar({page,setPage,open,setOpen}:{page:string,setPage:(x:string)=>void,open:boolean,setOpen:(x:boolean)=>void}){
 return <aside className={"sidebar "+(open?"open":"")}>
   <div className="brand"><div className="brand-mark">Z</div><div><strong>ZarinPal</strong><small>Insight Platform</small></div><button className="icon-btn close mobile" onClick={()=>setOpen(false)}><X size={16}/></button></div>
   <div className="nav-label">داشبورد تحلیلی</div>
   <nav>{items.map(([id,label,Icon])=><button key={id} className={page===id?"active":""} onClick={()=>{setPage(id);setOpen(false)}}><Icon size={17}/><span>{label}</span></button>)}</nav>
   <div className="side-note"><b>Evidence First</b><span>هر Insight قابل ردیابی تا Session و Attempt است.</span></div>
 </aside>
}
