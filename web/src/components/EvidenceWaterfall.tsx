// Evidence waterfall: each field's contribution to the log odds, starting from the prior.
// Plain SVG, with a table alternative and a screen reader label.
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type { PairScore } from "../contract/types";
import { usePrefs, useFormat } from "../prefs";

const W = 520;
const ROW = 22;

export function EvidenceWaterfall({ score }: { score: PairScore }) {
  const { t } = useTranslation();
  const { lang } = usePrefs();
  const f = useFormat();
  const [asTable, setAsTable] = useState(false);
  const id = useId();
  const rows = [
    { label: t("evidence.prior"), level: "", weight: score.prior_log_odds, tf: 0 },
    ...score.evidence.map((e) => ({
      label: e.field,
      level: e.level,
      weight: e.weight,
      tf: e.tf_adjustment ?? 0,
    })),
  ];
  let run = 0;
  const steps = rows.map((r) => {
    const start = run;
    run += r.weight;
    return { ...r, start, end: run };
  });
  const lo = Math.min(0, ...steps.map((s) => Math.min(s.start, s.end)));
  const hi = Math.max(0, ...steps.map((s) => Math.max(s.start, s.end)));
  const pad = 140;
  const rtl = lang === "ar";
  const base = (v: number) => pad + ((v - lo) / (hi - lo || 1)) * (W - pad - 10);
  // Right to left mirrors the axis so that evidence for a match grows towards the end side.
  const scale = (v: number) => (rtl ? W - base(v) : base(v));
  const height = (steps.length + 1) * ROW + 10;
  return (
    <figure style={{ margin: 0 }}>
      <figcaption>
        <strong>{t("evidence.title")}</strong>{" "}
        <span className="muted">
          {t("evidence.total")}: <span className="num">{f.num(score.log_odds, 2)}</span>
        </span>
      </figcaption>
      <p className="muted" id={`${id}-desc`}>
        {t("evidence.desc")}
      </p>
      <button type="button" onClick={() => setAsTable((v) => !v)} aria-pressed={asTable}>
        {t("evidence.table")}
      </button>
      {asTable ? (
        <table>
          <thead>
            <tr>
              <th scope="col">{t("evidence.field")}</th>
              <th scope="col">{t("evidence.level")}</th>
              <th scope="col">{t("evidence.weight")}</th>
            </tr>
          </thead>
          <tbody>
            {steps.map((s) => (
              <tr key={s.label}>
                <td>{s.label}</td>
                <td>{s.level}</td>
                <td className="num">
                  {f.num(s.weight, 2)}
                  {s.tf !== 0 ? ` (${t("evidence.freq")} ${f.num(s.tf, 2)})` : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <svg
          role="img"
          aria-labelledby={`${id}-desc`}
          viewBox={`0 0 ${W} ${height}`}
          width="100%"
          style={{ maxWidth: W }}
        >
          <line
            x1={scale(0)}
            x2={scale(0)}
            y1={0}
            y2={height}
            stroke="var(--ink)"
            strokeDasharray="3 3"
          />
          {steps.map((s, i) => {
            const a = scale(s.start);
            const b = scale(s.end);
            const x1 = Math.min(a, b);
            const x2 = Math.max(a, b);
            const y = 6 + i * ROW;
            return (
              <g key={s.label}>
                <text
                  x={rtl ? W - 4 : 4}
                  y={y + 14}
                  fontSize="12"
                  fill="var(--ink)"
                  textAnchor={rtl ? "end" : "start"}
                >
                  {s.label}
                </text>
                <rect
                  x={x1}
                  y={y + 2}
                  width={Math.max(2, x2 - x1)}
                  height={ROW - 6}
                  fill={s.weight >= 0 ? "var(--link)" : "var(--strong)"}
                  stroke="var(--ink)"
                  strokeWidth="1"
                />
              </g>
            );
          })}
        </svg>
      )}
    </figure>
  );
}
