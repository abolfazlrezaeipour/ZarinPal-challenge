
import {useEffect,useState} from "react";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Insights from "./pages/Insights";
import Benchmark from "./pages/Benchmark";
import Sessions from "./pages/Sessions";
import Customers from "./pages/Customers";
import Analytics from "./pages/Analytics";
import Assistant from "./pages/Assistant";
import {getMerchants} from "./api/client";

export default function App(){
  const [page,setPage]=useState("dashboard");
  const [merchant,setMerchant]=useState("");
  const [merchants,setMerchants]=useState<any[]>([]);
  const [dark,setDark]=useState(()=>{try{return localStorage.getItem("dashboard-theme")==="dark"}catch{return false}});
  useEffect(()=>{try{localStorage.setItem("dashboard-theme",dark?"dark":"light")}catch{}},[dark]);
  useEffect(()=>{document.documentElement.dataset.theme=dark?"dark":"light"; document.body.dataset.theme=dark?"dark":"light"; return ()=>{delete document.documentElement.dataset.theme; delete document.body.dataset.theme}},[dark]);
  useEffect(()=>{getMerchants().then(x=>{setMerchants(x); if(x[0]) setMerchant(x[0].merchant_key)}).catch(()=>{})},[]);
  return <div className={dark?"theme dark":"theme"}>
    <Layout page={page} setPage={setPage} dark={dark} setDark={setDark}
      merchant={merchant} setMerchant={setMerchant} merchants={merchants}>
      {page==="dashboard" && <Dashboard merchant={merchant}/>}
      {page==="insights" && <Insights merchant={merchant}/>}
      {page==="benchmark" && <Benchmark merchant={merchant}/>}
      {page==="sessions" && <Sessions merchant={merchant}/>}
      {page==="customers" && <Customers merchant={merchant}/>}
      {page==="analytics" && <Analytics merchant={merchant}/>}
      {page==="assistant" && <Assistant merchant={merchant}/>}
    </Layout>
  </div>
}
