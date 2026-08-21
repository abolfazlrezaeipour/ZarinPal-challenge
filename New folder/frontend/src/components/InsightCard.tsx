export default function InsightCard({data}:any){
return <div className="card insight">
<h3>{data?.title}</h3>
<p>{data?.summary}</p>
<span>{data?.severity}</span>
</div>
}
