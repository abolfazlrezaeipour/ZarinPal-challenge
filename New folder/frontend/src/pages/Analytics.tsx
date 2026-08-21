import { useEffect, useState } from "react";
import { getDaily, getHourly, getAmounts, getSeasonality } from "../api/client";
import { MetricChart, AmountDistributionPieChart } from "../components/ChartKit";

const monthNames = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
const weekNames = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"];

export default function Analytics({ merchant }: { merchant: string }) {
  const [d, setD] = useState<any[]>([]);
  const [h, setH] = useState<any[]>([]);
  const [a, setA] = useState<any[]>([]);
  const [s, setS] = useState<any>({ monthly: [], weekday: [] });

  useEffect(() => {
    if (!merchant) return;
    Promise.allSettled([getDaily(merchant), getHourly(merchant), getAmounts(merchant), getSeasonality(merchant)]).then((results) => {
      setD(results[0].status === "fulfilled" ? results[0].value : []);
      setH(results[1].status === "fulfilled" ? results[1].value : []);
      setA(results[2].status === "fulfilled" ? results[2].value : []);
      setS(results[3].status === "fulfilled" ? results[3].value : { monthly: [], weekday: [] });
    });
  }, [merchant]);

  const monthly = (s.monthly || []).map((x: any) => ({ ...x, label: monthNames[x.month] || String(x.month) }));
  const weekday = (s.weekday || []).map((x: any) => ({ ...x, label: weekNames[x.weekday] || String(x.weekday) }));

  return (
    <>
      <div className="page-head"><div><span className="eyebrow">TIME & AMOUNT</span><h1>تحلیل زمانی و مبلغی</h1><p>تحلیل Session ها، رفتار زمانی و مبلغی پذیرنده</p></div></div>
      <div className="grid two">
        <MetricChart title="فروش روزانه" data={d} x="metric_date" y="successful_volume" type="area" kind="money" />
        <MetricChart title="نرخ موفقیت ساعتی" data={h} x="hour_of_day" y="success_rate" type="line" percent />
        <MetricChart title="توزیع مبلغ تراکنش" data={a} x="amount_bucket" y="sessions" type="bar" count />
        <div className="card chart-card"><div className="card-head"><div><h2>سهم Sessionها بر اساس مبلغ</h2><small>ترکیب بازه‌های مبلغی</small></div><span className="chart-badge">SHARE</span></div><AmountDistributionPieChart data={a} /></div>
        <MetricChart title="فروش ماهانه" data={monthly} x="label" y="successful_volume" type="bar" kind="money" />
        <MetricChart title="نرخ موفقیت روزهای هفته" data={weekday} x="label" y="success_rate" type="line" percent />
      </div>
    </>
  );
}
