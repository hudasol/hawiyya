import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { getSummary } from "../api";
import { ErrorBox, Loading } from "../components/Basics";
import { useFormat } from "../prefs";

export function Overview() {
  const { t } = useTranslation();
  const f = useFormat();
  const q = useQuery({ queryKey: ["summary"], queryFn: getSummary });
  return (
    <section aria-labelledby="ov-title">
      <h2 id="ov-title">{t("overview.title")}</h2>
      {q.isPending ? <Loading /> : null}
      {q.isError ? <ErrorBox error={q.error} /> : null}
      {q.data ? (
        <>
          <div className="grid">
            <div className="stat">
              <div>{t("overview.records")}</div>
              <div className="value">{f.num(q.data.records)}</div>
            </div>
            <div className="stat">
              <div>{t("overview.persons")}</div>
              <div className="value">{f.num(q.data.synthetic_ground_truth.persons)}</div>
              <div className="muted">{t("overview.truth_label")}</div>
            </div>
            <div className="stat">
              <div>{t("overview.duplicate_share")}</div>
              <div className="value">
                {f.pct(q.data.synthetic_ground_truth.duplicate_record_share)}
              </div>
              <div className="muted">{t("overview.truth_label")}</div>
            </div>
            <div className="stat">
              <div>{t("overview.placeholder_share")}</div>
              <div className="value">{f.pct(q.data.placeholder_identifier_share)}</div>
              <div className="muted">{t("overview.detected_label")}</div>
            </div>
            <div className="stat">
              <div>{t("overview.dob_default_share")}</div>
              <div className="value">{f.pct(q.data.suspected_default_dob_share)}</div>
              <div className="muted">{t("overview.detected_label")}</div>
            </div>
          </div>
          <div className="card" style={{ marginBlockStart: "1.25rem" }}>
            <h3>{t("overview.facilities")}</h3>
            <table>
              <tbody>
                {q.data.facilities.map((fac) => (
                  <tr key={fac.facility_id}>
                    <th scope="row" className="mono">
                      {fac.facility_id}
                    </th>
                    <td>{fac.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted">
              {t("overview.source")}: {q.data.data_source}. {t("overview.model")}:{" "}
              <span className="mono">{q.data.model_version}</span>
            </p>
          </div>
        </>
      ) : null}
    </section>
  );
}
