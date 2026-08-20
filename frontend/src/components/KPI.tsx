
import {ArrowUpLeft,ArrowDownLeft} from "lucide-react";
export default function KPI({title,value,subtitle,trend,icon}:{title:string,value:string,subtitle?:string,trend?:number,icon?:React.ReactNode}){
 return <div className="card kpi"><div className="kpi-top"><span>{title}</span><i>{icon}</i></div><strong>{value}</strong>{subtitle&&<small>{subtitle}</small>}{trend!==undefined&&<em className={trend>=0?"positive":"negative"}>{trend>=0?<ArrowUpLeft size={13}/>:<ArrowDownLeft size={13}/>} {Math.abs(trend).toFixed(1)}٪ نسبت به مبنای مقایسه</em>}</div>
}
