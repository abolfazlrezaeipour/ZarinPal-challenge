import { useEffect, useState } from "react";
import { getSessions, getSession } from "../api/client";
import { Search } from "lucide-react";

const nf = (n: number) =>
  new Intl.NumberFormat("fa-IR").format(Math.round(n || 0));

const money = (n: number) => nf(n) + " ریال";

export default function Sessions({ merchant }: { merchant: string }) {
  const [data, setData] = useState<any>({
    items: [],
    total: 0,
  });

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [offset, setOffset] = useState(0);
  const [detail, setDetail] = useState<any>();

  useEffect(() => {
    if (merchant) {
      getSessions(merchant, q, status, offset).then(setData);
    }
  }, [merchant, q, status, offset]);

  const open = (id: string) => {
    getSession(id).then(setDetail);
  };

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
              value={q}
              onChange={(e) => {
                setOffset(0);
                setQ(e.target.value);
              }}
              placeholder="جستجوی Session Key"
            />
          </div>

          <div className="select-wrap status-select">
            <select
              value={status}
              onChange={(e) => {
                setOffset(0);
                setStatus(e.target.value);
              }}
            >
              <option value="all">همه وضعیت‌ها</option>
              <option value="success">موفق</option>
              <option value="failed">ناموفق</option>
              <option value="recovered">بازیابی‌شده</option>
              <option value="retry">Retry</option>
              <option value="no_attempt">بدون Attempt</option>
            </select>
          </div>
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Session</th>
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