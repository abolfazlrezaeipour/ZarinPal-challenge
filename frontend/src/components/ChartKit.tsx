import React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Pie,
  PieChart,
  Cell,
  Legend,
} from "recharts";

export type ChartValueKind = "number" | "percent" | "money" | "count";

type ChartTooltipProps = {
  active?: boolean;
  payload?: any[];
  label?: React.ReactNode;
  kind?: ChartValueKind;
  labelFormatter?: (value: any) => string;
};

export const compactNumber = (value: number, kind: ChartValueKind = "number") => {
  if (!Number.isFinite(value)) return "—";
  if (kind === "percent") return `${(value * 100).toFixed(value * 100 < 10 ? 1 : 0)}%`;

  const abs = Math.abs(value);
  const sign = value < 0 ? "−" : "";
  const decimals = (n: number) => {
    if (n >= 100) return n.toFixed(0);
    if (n >= 10) return n.toFixed(1);
    return n.toFixed(2);
  };

  if (abs >= 1e15) return `${sign}${value.toExponential(2).replace("e+", "e")}`;
  if (abs >= 1e12) return `${sign}${decimals(abs / 1e12)}T`;
  if (abs >= 1e9) return `${sign}${decimals(abs / 1e9)}B`;
  if (abs >= 1e6) return `${sign}${decimals(abs / 1e6)}M`;
  if (abs >= 1e3) return `${sign}${decimals(abs / 1e3)}K`;
  return `${sign}${Math.round(abs).toLocaleString("en-US")}`;
};

export const axisNumber = (value: number, kind: ChartValueKind = "number") => compactNumber(Number(value), kind);

export function ChartTooltip({ active, payload, label, kind = "number", labelFormatter }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  const numeric = Number(item?.value);
  const formatted = Number.isFinite(numeric) ? compactNumber(numeric, kind) : String(item?.value ?? "—");
  const title = labelFormatter ? labelFormatter(label) : String(label ?? "");

  return (
    <div className="chart-tooltip" dir="rtl">
      <div className="chart-tooltip-label">{title}</div>
      <div className="chart-tooltip-row">
        <span className="chart-tooltip-dot" style={{ background: item?.color || "var(--primary)" }} />
        <span>{item?.name || "مقدار"}</span>
        <strong dir="ltr">{formatted}</strong>
      </div>
    </div>
  );
}

export function chartTick(value: any) {
  const text = String(value ?? "");
  return text.length > 12 ? `${text.slice(0, 10)}…` : text;
}

export function ChartFrame({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`chart ${className}`}><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div>;
}

export function SalesAreaChart({ data }: { data: any[] }) {
  return (
    <ChartFrame>
      <AreaChart data={data} margin={{ top: 12, right: 8, left: 2, bottom: 2 }}>
        <defs>
          <linearGradient id="sales-area-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--chart-primary)" stopOpacity={0.32} />
            <stop offset="100%" stopColor="var(--chart-primary)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
        <XAxis dataKey="metric_date" tickFormatter={chartTick} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} minTickGap={18} />
        <YAxis tickFormatter={(v) => axisNumber(Number(v), "money")} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} width={52} />
        <Tooltip content={<ChartTooltip kind="money" />} cursor={{ stroke: "var(--chart-hover)", strokeWidth: 1 }} />
        <Area type="monotone" dataKey="successful_volume" name="فروش موفق" stroke="var(--chart-primary)" fill="url(#sales-area-fill)" strokeWidth={2.5} activeDot={{ r: 5, strokeWidth: 2, stroke: "var(--surface)" }} />
      </AreaChart>
    </ChartFrame>
  );
}

export function VolumeBarChart({ data, dataKey = "successful_volume", xKey = "hour_of_day", name = "فروش موفق", kind = "money", className = "" }: { data: any[]; dataKey?: string; xKey?: string; name?: string; kind?: ChartValueKind; className?: string }) {
  const showLabels = data.length <= 8;
  return (
    <ChartFrame className={className}>
      <BarChart data={data} margin={{ top: showLabels ? 20 : 8, right: 8, left: 2, bottom: 2 }}>
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
        <XAxis dataKey={xKey} tickFormatter={chartTick} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} minTickGap={12} />
        <YAxis tickFormatter={(v) => axisNumber(Number(v), kind)} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} width={52} />
        <Tooltip content={<ChartTooltip kind={kind} />} cursor={{ fill: "var(--chart-hover-fill)" }} />
        <Bar dataKey={dataKey} name={name} fill="var(--chart-primary)" radius={[7, 7, 2, 2]} maxBarSize={34}>
          {showLabels && <LabelList dataKey={dataKey} position="top" formatter={(v: any) => compactNumber(Number(v), kind)} fill="var(--chart-label)" fontSize={8} />}
        </Bar>
      </BarChart>
    </ChartFrame>
  );
}

export function SuccessBarChart({ data }: { data: any[] }) {
  const showLabels = data.length <= 8;
  return (
    <ChartFrame className="small">
      <BarChart data={data} layout="vertical" margin={{ top: 6, right: 10, left: 2, bottom: 4 }}>
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => axisNumber(Number(v), "percent")} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} />
        <YAxis dataKey="psp_code" type="category" width={58} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} />
        <Tooltip content={<ChartTooltip kind="percent" />} cursor={{ fill: "var(--chart-hover-fill)" }} />
        <Bar dataKey="success_rate" name="نرخ موفقیت" fill="var(--chart-secondary)" radius={[0, 7, 7, 0]} maxBarSize={22}>
          {showLabels && <LabelList dataKey="success_rate" position="right" formatter={(v: any) => compactNumber(Number(v), "percent")} fill="var(--chart-label)" fontSize={8} />}
        </Bar>
      </BarChart>
    </ChartFrame>
  );
}

export function AmountDistributionPieChart({ data }: { data: any[] }) {
  const rows = data
    .map((item: any) => ({ name: String(item.amount_bucket ?? "—"), value: Number(item.sessions ?? 0) }))
    .filter((item: any) => Number.isFinite(item.value) && item.value > 0);
  const palette = [
    "var(--chart-primary)",
    "var(--chart-secondary)",
    "var(--chart-accent)",
    "var(--chart-info)",
    "var(--chart-warning)",
    "var(--chart-danger)",
  ];
  const total = rows.reduce((sum, item) => sum + item.value, 0);

  return (
    <ChartFrame className="small pie-chart-frame">
      {!rows.length ? <div className="empty-chart">داده‌ای موجود نیست</div> : (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={rows} dataKey="value" nameKey="name" cx="42%" cy="50%" innerRadius="54%" outerRadius="76%" paddingAngle={2} stroke="var(--surface)" strokeWidth={3}>
              {rows.map((_, index) => <Cell key={`cell-${index}`} fill={palette[index % palette.length]} />)}
            </Pie>
            <Tooltip content={<ChartTooltip kind="count" />} />
            <Legend verticalAlign="middle" align="right" layout="vertical" iconType="circle" formatter={(value: any) => {
              const row = rows.find((item) => item.name === value);
              const pct = row && total ? `${((row.value / total) * 100).toFixed(0)}٪` : "";
              return <span className="pie-legend-label">{value} <b>{pct}</b></span>;
            }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </ChartFrame>
  );
}

export function MetricChart({ title, data, x, y, type, kind = "number", percent = false, count = false }: { title: string; data: any[]; x: string; y: string; type: "area" | "line" | "bar"; kind?: ChartValueKind; percent?: boolean; count?: boolean }) {
  const valueKind: ChartValueKind = percent ? "percent" : count ? "count" : kind;
  const showLabels = type === "bar" && data.length <= 8;
  const tooltip = <ChartTooltip kind={valueKind} />;
  return (
    <div className="card chart-card">
      <div className="card-head">
        <div><h2>{title}</h2><small>{data.length} نقطه داده</small></div>
        <span className="chart-badge">{percent ? "%" : valueKind === "money" ? "IRR" : "مقدار"}</span>
      </div>
      <div className="chart">
        {!data.length ? <div className="empty-chart">داده‌ای موجود نیست</div> : (
          <ResponsiveContainer width="100%" height="100%">
            {type === "bar" ? (
              <BarChart data={data} margin={{ top: showLabels ? 20 : 8, right: 8, left: 2, bottom: 2 }}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
                <XAxis dataKey={x} interval={0} tickFormatter={chartTick} tick={{ fill: "var(--chart-text)", fontSize: 8 }} tickLine={false} axisLine={false} minTickGap={4} />
                <YAxis tickFormatter={(v) => axisNumber(Number(v), valueKind)} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} width={52} domain={percent ? [0, 1] : undefined} />
                <Tooltip content={tooltip} cursor={{ fill: "var(--chart-hover-fill)" }} />
                <Bar dataKey={y} name={title} fill="var(--chart-primary)" radius={[7, 7, 2, 2]} maxBarSize={34}>
                  {showLabels && <LabelList dataKey={y} position="top" formatter={(v: any) => compactNumber(Number(v), valueKind)} fill="var(--chart-label)" fontSize={8} />}
                </Bar>
              </BarChart>
            ) : type === "line" ? (
              <LineChart data={data} margin={{ top: 12, right: 8, left: 2, bottom: 2 }}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
                <XAxis dataKey={x} tickFormatter={chartTick} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} minTickGap={12} />
                <YAxis tickFormatter={(v) => axisNumber(Number(v), valueKind)} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} width={48} domain={percent ? [0, 1] : undefined} />
                <Tooltip content={tooltip} cursor={{ stroke: "var(--chart-hover)", strokeWidth: 1 }} />
                <Line type="monotone" dataKey={y} name={title} stroke="var(--chart-secondary)" strokeWidth={2.5} dot={{ r: 2.5, fill: "var(--chart-secondary)", strokeWidth: 0 }} activeDot={{ r: 5, fill: "var(--chart-secondary)", stroke: "var(--surface)", strokeWidth: 2 }} />
              </LineChart>
            ) : (
              <AreaChart data={data} margin={{ top: 12, right: 8, left: 2, bottom: 2 }}>
                <defs><linearGradient id={`metric-area-${y}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--chart-primary)" stopOpacity={0.28} /><stop offset="100%" stopColor="var(--chart-primary)" stopOpacity={0.02} /></linearGradient></defs>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
                <XAxis dataKey={x} tickFormatter={chartTick} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} minTickGap={16} />
                <YAxis tickFormatter={(v) => axisNumber(Number(v), valueKind)} tick={{ fill: "var(--chart-text)", fontSize: 9 }} tickLine={false} axisLine={false} width={52} />
                <Tooltip content={tooltip} cursor={{ stroke: "var(--chart-hover)", strokeWidth: 1 }} />
                <Area type="monotone" dataKey={y} name={title} stroke="var(--chart-primary)" fill={`url(#metric-area-${y})`} strokeWidth={2.5} activeDot={{ r: 5, fill: "var(--chart-primary)", stroke: "var(--surface)", strokeWidth: 2 }} />
              </AreaChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
