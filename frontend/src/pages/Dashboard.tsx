import { useEffect, useState } from "react";
import { Banknote, Activity, Percent, Repeat2, AlertTriangle, Target, Clock3 } from "lucide-react";
import KPI from "../components/KPI";
import { getMerchant, getDaily, getHourly, getPSPs, getHealth, getInsights } from "../api/client";
import { SalesAreaChart, VolumeBarChart, SuccessBarChart } from "../components/ChartKit";

const nf = (n: number) => new Intl.NumberFormat("fa-IR").format(Math.round(n || 0));
const money = (n: number) => nf(n) + " ریال";
function Loading() { return <div className="skeleton" />; }

export default function Dashboard({ merchant }: { merchant: string }) {
  const [m, setM] = useState<any>();
  const [daily, setDaily] = useState<any[]>([]);
  const [hourly, setHourly] = useState<any[]>([]);
  const [psp, setPsp] = useState<any[]>([]);
  const [h, setH] = useState<any>();
  const [ins, setIns] = useState<any[]>([]);

  useEffect(() => {
    if (!merchant) return;
    Promise.all([getMerchant(merchant), getDaily(merchant), getHourly(merchant), getPSPs(merchant), getHealth(merchant), getInsights(merchant)]).then(([a, b, c, d, e, f]) => {
      setM(a); setDaily(b); setHourly(c); setPsp(d); setH(e); setIns(f);
    });
  }, [merchant]);

  if (!m) return <Loading />;
  const x = m.merchant;

  return <>
    <div className="page-head"><div><span className="eyebrow">OVERVIEW</span><h1>{x.category_title || "داشبورد پذیرنده"}</h1><p>تصویر ۳۶۰ درجه از سلامت پرداخت، فروش و فرصت‌های رشد</p></div><div className="date-chip">{x.first_seen_at?.slice(0, 10)} تا {x.last_seen_at?.slice(0, 10)}</div></div>
    <div className="grid kpi-grid">
      <KPI title="فروش موفق" value={money(x.successful_volume)} subtitle={`${nf(x.successful_sessions)} Session موفق`} icon={<Banknote size={17} />} />
      <KPI title="نرخ موفقیت نهایی" value={`${(x.final_success_rate * 100).toFixed(1)}٪`} subtitle={`تلاش اول ${(x.first_attempt_success_rate * 100).toFixed(1)}٪`} trend={(x.final_success_rate - x.first_attempt_success_rate) * 100} icon={<Percent size={17} />} />
      <KPI title="AOV" value={money(x.aov)} subtitle={`${nf(x.sessions)} کل Session`} icon={<Activity size={17} />} />
      <KPI title="فرصت بازیابی" value={money(x.unrecovered_volume)} subtitle={`${nf(x.unrecovered_sessions)} Session بازیابی‌نشده`} icon={<Repeat2 size={17} />} />
    </div>

    <div className="grid two section">
      <div className="card chart-card"><div className="card-head"><div><h2>روند فروش</h2><small>فروش موفق روزانه</small></div><span className="chart-badge">IRR</span></div><SalesAreaChart data={daily} /></div>
      <div className="card health"><div className="card-head"><div><h2>Payment Health Score</h2><small>ترکیبی از موفقیت، Retry و Recovery</small></div><Target size={20} /></div><div className="health-ring" style={{ "--p": `${h?.score || 0}%` } as any}><span>{nf(h?.score || 0)}</span></div><b>{h?.status}</b><p>صدک موفقیت نسبت به هم‌صنف: {nf(h?.percentile || 0)}٪</p><div className="mini-metrics"><span>Success <b>{(h?.success_rate * 100).toFixed(1)}٪</b></span><span>Retry <b>{(h?.retry_rate * 100).toFixed(1)}٪</b></span></div></div>
    </div>

    <div className="grid three section">
      <div className="card chart-card"><div className="card-head"><h2>ساعات پرترافیک</h2><Clock3 size={18} /></div><VolumeBarChart data={hourly} dataKey="successful_volume" xKey="hour_of_day" name="فروش موفق" kind="money" className="small" /></div>
      <div className="card chart-card"><div className="card-head"><h2>عملکرد PSP</h2><Banknote size={18} /></div><SuccessBarChart data={psp.slice(0, 6)} /></div>
      <div className="card"><div className="card-head"><h2>مهم‌ترین فرصت‌ها</h2><AlertTriangle size={18} /></div>{ins.slice(0, 4).map((i) => <div className="mini-insight" key={i.insight_type}><span className={`severity ${i.severity}`}>{i.severity}</span><b>{i.title}</b><p>{i.summary}</p></div>)}</div>
    </div>
  </>;
}
