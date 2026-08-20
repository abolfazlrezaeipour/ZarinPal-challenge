
const API=import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
async function req(path:string, options:RequestInit={}){
 const r=await fetch(API+path,{headers:{"Content-Type":"application/json",...(options.headers||{})},...options});
 if(!r.ok){
   let message=await r.text();
   try{message=JSON.parse(message).detail||message}catch{}
   throw new Error(message);
 }
 return r.json();
}
export const getMerchants=()=>req("/merchants?limit=200");
export const getMerchant=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/overview`);
export const getInsights=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/insights`);
export const getDaily=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/daily?limit=180`);
export const getHourly=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/hourly`);
export const getPSPs=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/psps`);
export const getAmounts=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/amounts`);
export const getPeers=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/peers`);
export const getCustomers=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/customers`);
export const getCalendar=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/calendar`);
export const getSeasonality=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/seasonality`);
export const getHealth=(id:string)=>req(`/merchants/${encodeURIComponent(id)}/health-score`);
export const getSessions=(id:string,search="",status="all",offset=0)=>req(`/merchants/${encodeURIComponent(id)}/sessions?search=${encodeURIComponent(search)}&status=${status}&limit=25&offset=${offset}`);
export const getSession=(id:string)=>req(`/sessions/${encodeURIComponent(id)}`);
export const getInsightDetail=(id:string,type:string)=>req(`/insights/${encodeURIComponent(id)}/${encodeURIComponent(type)}`);
export const getEvidence=(id:string,type:string)=>req(`/insights/${encodeURIComponent(id)}/${encodeURIComponent(type)}/sessions?limit=100`);
export const askMerchant=(id:string,q:string)=>req(`/merchants/${encodeURIComponent(id)}/ask`,{method:"POST",body:JSON.stringify({question:q})});
export async function safeReq<T>(fn:()=>Promise<T>,fallback:T):Promise<T>{
    try{
        return await fn();
    }
    catch(e){
        console.error(e);
        return fallback;
    }
}