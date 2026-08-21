import { useEffect, useState } from "react";
import { getSessions, getSession, getPSPs, SessionFilters } from "../api/client";
import { Search, SlidersHorizontal, X, RotateCcw } from "lucide-react";

const nf = (n: number) =>
  new Intl.NumberFormat("fa-IR").format(Math.round(n || 0));

const money = (n: number) => nf(n) + " ریال";

const dt = (v: any) => {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d.getTime())) return String(v);
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" }).format(d);
};

const STATUS_OPTIONS = [
  ["all", "همه وضعیت‌ها"],
  ["success", "موفق"],
  ["failed", "ناموفق"],
  ["recovered", "بازیابی‌شده"],
  ["retry", "Retry"],
  ["no_attempt", "بدون Attempt"],
] as const;

const emptyFilters: SessionFilters = {
  search: "",
  status: "all",
  psp: "",
  dateFrom: "",
  dateTo: "",
  minAmount: "",
  maxAmount: "",
  minAttempts: "",
};

function countActive(f: SessionFilters) {
  let n = 0;
  if (f.psp) n++;
  if (f.dateFrom) n++;
  if (f.dateTo) n++;
  if (f.minAmount) n++;
  if (f.maxAmount) n++;
  if (f.minAttempts) n++;
  return n;
}

export default function Sessions({ merchant }: { merchant: string }) {
  const [data, setData] = useState<any>({
    items: [],
    total: 0,
  });

  const [filters, setFilters] = useState<SessionFilters>(emptyFilters);
  const [draft, setDraft] = useState<SessionFilters>(emptyFilters);
  const [showFilters, setShowFilters] = useState(false);
  const [psps, setPsps] = useState<any[]>([]);
  const [offset, setOffset] = useState(0);
  const [detail, setDetail] = useState<any>();

  useEffect(() => {
    if (merchant) getPSPs(merchant).then(setPsps).catch(() => setPsps([]));
  }, [merchant]);

  useEffect(() => {
    if (merchant) {
      getSessions(merchant, filters, offset).then(setData);
    }
  }, [merchant, filters, offset]);

  const open = (id: string) => {
    getSession(id).then(setDetail);
  };

  const openFilters = () => {
    setDraft(filters);
    setShowFilters(true);
  };

  const applyFilters = () => {
    setOffset(0);
    setFilters(draft);
    setShowFilters(false);
  };

  const clearAll = () => {
    setDraft(emptyFilters);
  };

  const activeCount = countActive(filters);

  return (
    <>
      <div className="page-head">
        <div>
          <span className="eyebrow">SESSION EXPLORER</span>
          <h1>کاوش تراکنش‌ها</h1>
          <p>
            مدل تحلیل: هر Session یک intent و هر Attempt یک تلاش پرداخت است.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="filters">
          <div className="search">
            <Search size={16} />
            <input
              value={filters.search}
              onChange={(e) => {
                setOffset(0);
                setFilters((f) => ({ ...f, search: e.target.value }));
              }}
              placeholder="جستجوی Session Key"
            />
          </div>

          <div className="select-wrap status-select">
            <select
              value={filters.status}
              onChange={(e) => {
                setOffset(0);
                setFilters((f) => ({ ...f, status: e.target.value }));
              }}
            >
              {STATUS_OPTIONS.map(([v, label]) => (
                <option key={v} value={v}>{label}</option>
              ))}
            </select>
          </div>

          <button className="filter-toggle-btn" onClick={openFilters}>
            <SlidersHorizontal size={15} />
            فیلترهای پیشرفته
            {activeCount > 0 && <span className="filter-count-badge">{activeCount}</span>}
          </button>
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Session</th>
                <th>تاریخ و زمان</th>
                <th>مبلغ</th>
                <th>Attempt</th>
                <th>اولین تلاش</th>
                <th>آخرین وضعیت</th>
                <th>PSP</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {data.items.map((s: any) => (
                <tr
                  key={s.session_key}
                  onClick={() => open(s.session_key)}
                  className="click-row"
                >
                  <td>{s.session_key}</td>
                  <td>{dt(s.created_at)}</td>
                  <td>{money(s.amount)}</td>
                  <td>{nf(s.attempt_count)}</td>
                  <td>{s.first_try_status || "—"}</td>
                  <td>
                    <span
                      className={
                        "status " + (s.final_success ? "success" : "failed")
                      }
                    >
                      {s.final_success
                        ? "موفق"
                        : s.unrecovered
                          ? "از دست رفته"
                          : "در جریان"}
                    </span>
                  </td>
                  <td>{s.last_psp_code || "—"}</td>
                  <td>›</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="pagination">
          <span>{nf(data.total)} Session</span>

          <div>
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 25))}
            >
              قبلی
            </button>

            <button
              disabled={offset + 25 >= data.total}
              onClick={() => setOffset(offset + 25)}
            >
              بعدی
            </button>
          </div>
        </div>
      </div>

      {showFilters && (
        <div className="modal-backdrop" onClick={() => setShowFilters(false)}>
          <div className="modal filter-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <div>
                <span className="eyebrow">ADVANCED FILTERS</span>
                <h2>فیلترهای پیشرفته</h2>
              </div>

              <button className="icon-btn" onClick={() => setShowFilters(false)}>
                <X size={16} />
              </button>
            </div>

            <div className="filter-grid">
              <div className="field">
                <label>جستجوی Session Key</label>
                <div className="search">
                  <Search size={16} />
                  <input
                    value={draft.search}
                    onChange={(e) => setDraft((f) => ({ ...f, search: e.target.value }))}
                    placeholder="مثلاً 1739273"
                  />
                </div>
              </div>

              <div className="field">
                <label>وضعیت تراکنش</label>
                <div className="select-wrap">
                  <select className="w100 search"
                    value={draft.status}
                    onChange={(e) => setDraft((f) => ({ ...f, status: e.target.value }))}
                  >
                    {STATUS_OPTIONS.map(([v, label]) => (
                      <option key={v} value={v}>{label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="field">
                <label>PSP</label>
                <div className="select-wrap">
                  <select className="search"
                    value={draft.psp}
                    onChange={(e) => setDraft((f) => ({ ...f, psp: e.target.value }))}
                  >
                    <option value="">همه PSPها</option>
                    {psps.map((p: any) => (
                      <option key={p.psp_code} value={p.psp_code}>{p.psp_code}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="field">
                <label>حداقل تعداد Attempt</label>
                <input
                  type="number"
                  min={0}
                  className="field-input"
                  value={draft.minAttempts}
                  onChange={(e) => setDraft((f) => ({ ...f, minAttempts: e.target.value }))}
                  placeholder="مثلاً 2"
                />
              </div>

              <div className="field">
                <label>از تاریخ و ساعت</label>
                <input
                  type="datetime-local"
                  className="field-input"
                  value={draft.dateFrom}
                  onChange={(e) => setDraft((f) => ({ ...f, dateFrom: e.target.value }))}
                />
              </div>

              <div className="field">
                <label>تا تاریخ و ساعت</label>
                <input
                  type="datetime-local"
                  className="field-input"
                  value={draft.dateTo}
                  onChange={(e) => setDraft((f) => ({ ...f, dateTo: e.target.value }))}
                />
              </div>

              <div className="field">
                <label>حداقل مبلغ (ریال)</label>
                <input
                  type="number"
                  min={0}
                  className="field-input"
                  value={draft.minAmount}
                  onChange={(e) => setDraft((f) => ({ ...f, minAmount: e.target.value }))}
                  placeholder="مثلاً 100000"
                />
              </div>

              <div className="field">
                <label>حداکثر مبلغ (ریال)</label>
                <input
                  type="number"
                  min={0}
                  className="field-input"
                  value={draft.maxAmount}
                  onChange={(e) => setDraft((f) => ({ ...f, maxAmount: e.target.value }))}
                  placeholder="مثلاً 5000000"
                />
              </div>
            </div>

            <div className="filter-actions">
              <button className="filter-clear-btn" onClick={clearAll}>
                <RotateCcw size={14} />
                پاک کردن همه فیلترها
              </button>
              <button className="filter-apply-btn" onClick={applyFilters}>
                اعمال فیلترها
              </button>
            </div>
          </div>
        </div>
      )}

      {detail && (
        <div
          className="modal-backdrop"
          onClick={() => setDetail(null)}
        >
          <div
            className="modal wide"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-head">
              <div>
                <span className="eyebrow">SESSION TIMELINE</span>
                <h2>#{detail.session.session_key}</h2>
              </div>

              <button
                className="icon-btn"
                onClick={() => setDetail(null)}
              >
                ×
              </button>
            </div>

            <div className="grid three">
              <div className="card">
                <small>مبلغ</small>
                <strong>{money(detail.session.amount)}</strong>
              </div>

              <div className="card">
                <small>Attempt</small>
                <strong>{nf(detail.session.attempt_count)}</strong>
              </div>

              <div className="card">
                <small>وضعیت</small>
                <strong>{detail.session.session_status}</strong>
              </div>
            </div>

            <div className="timeline">
              {detail.attempts.map((a: any) => (
                <div className="timeline-item" key={a.try_seq}>
                  <div className="dot" />

                  <div>
                    <b>
                      Attempt {nf(a.try_seq)} · {a.psp_code || "No PSP"}
                    </b>

                    <p>
                      {a.try_status || "NoAttempt"} ·{" "}
                      {a.switch_response_code || "بدون کد پاسخ"} ·{" "}
                      {a.try_created_at || a.created_at}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}