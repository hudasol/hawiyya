import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import {
  getCheckExamples,
  MODE,
  postCheck,
  type CheckResponse,
  type RegistrationInput,
} from "../api";
import { DecisionBadge, Empty, ErrorBox, Ident, Loading, Names } from "../components/Basics";
import { EvidenceWaterfall } from "../components/EvidenceWaterfall";
import { useFormat } from "../prefs";

function Results({ data }: { data: CheckResponse }) {
  const { t } = useTranslation();
  const f = useFormat();
  if (!data.ok) return <p role="status">{t("check.failed_open")}</p>;
  return (
    <section aria-labelledby="cands" style={{ marginBlockStart: "1rem" }}>
      <h3 id="cands">
        {t("check.candidates")}{" "}
        <span className="muted">
          ({t("check.scored")}: <span className="num">{f.num(data.n_scored)}</span>)
        </span>
      </h3>
      {data.candidates.length === 0 ? <p>{t("check.none")}</p> : null}
      <ol style={{ paddingInlineStart: "1.25rem" }}>
        {data.candidates.map((c) => (
          <li key={c.record.record_id ?? ""} className="card" data-testid="candidate">
            <div className="toolbar" style={{ justifyContent: "space-between" }}>
              <div>
                <Names ar={c.record.name_ar} latin={c.record.name_latin} />
                <div className="muted">
                  {t("check.record")} <span className="mono">{c.record.record_id}</span> ·{" "}
                  <Ident value={c.record.dob} /> · <Ident value={c.record.id_value} />
                </div>
              </div>
              <div>
                <div>
                  {t("check.probability")}:{" "}
                  <strong className="num">{f.pct(c.score.probability, 1)}</strong>
                </div>
                <div className="muted">
                  {t("check.interval")}:{" "}
                  <span className="num">
                    {f.pct(c.score.probability_low, 1)} - {f.pct(c.score.probability_high, 1)}
                  </span>
                </div>
                {c.decision ? (
                  <DecisionBadge kind={c.decision.decision} />
                ) : (
                  <span className="muted">{t("decision.pending")}</span>
                )}
              </div>
            </div>
            <details>
              <summary>{t("check.evidence")}</summary>
              <EvidenceWaterfall score={c.score} />
            </details>
          </li>
        ))}
      </ol>
    </section>
  );
}

function LiveForm() {
  const { t } = useTranslation();
  const [form, setForm] = useState<RegistrationInput>({});
  const m = useMutation({ mutationFn: postCheck });
  const set = (k: keyof RegistrationInput) => (e: { target: { value: string } }) =>
    setForm((s) => ({ ...s, [k]: e.target.value || null }));
  const submit = (e: FormEvent) => {
    e.preventDefault();
    m.mutate(form);
  };
  return (
    <>
      <form onSubmit={submit} className="card" aria-label={t("check.title")}>
        <div className="form-grid">
          <label>
            {t("check.name_ar")}
            <input dir="rtl" lang="ar" onChange={set("name_ar")} />
          </label>
          <label>
            {t("check.name_latin")}
            <input dir="ltr" onChange={set("name_latin")} />
          </label>
          <label>
            {t("check.dob")}
            <input type="date" onChange={set("dob")} />
          </label>
          <label>
            {t("check.sex")}
            <select onChange={set("sex")} defaultValue="">
              <option value="">{t("check.sex_any")}</option>
              <option value="M">{t("check.sex_m")}</option>
              <option value="F">{t("check.sex_f")}</option>
            </select>
          </label>
          <label>
            {t("check.id")}
            <input dir="ltr" inputMode="numeric" onChange={set("id_value")} />
          </label>
          <label>
            {t("check.phone")}
            <input dir="ltr" inputMode="tel" onChange={set("phone")} />
          </label>
        </div>
        <div style={{ marginBlockStart: "1rem" }}>
          <button className="primary" type="submit">
            {t("check.submit")}
          </button>
        </div>
      </form>
      {m.isPending ? <Loading /> : null}
      {m.isError ? <ErrorBox error={m.error} /> : null}
      {m.data ? <Results data={m.data} /> : null}
    </>
  );
}

function StaticExamples() {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["check-examples"], queryFn: getCheckExamples });
  const [key, setKey] = useState<string>("");
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorBox error={q.error} />;
  if (!q.data.length) return <Empty />;
  const chosen = q.data.find((e) => e.key === key) ?? q.data[0];
  return (
    <>
      <p className="card">{t("check.static_note")}</p>
      <label>
        {t("check.example")}
        <select value={chosen.key} onChange={(e) => setKey(e.target.value)}>
          {q.data.map((e) => (
            <option key={e.key} value={e.key}>
              {e.label}
            </option>
          ))}
        </select>
      </label>
      <div className="card" style={{ marginBlockStart: "1rem" }}>
        <Names ar={chosen.input.name_ar} latin={chosen.input.name_latin} />
        <div className="muted">
          <Ident value={chosen.input.dob} /> · <Ident value={chosen.input.id_value} />
        </div>
      </div>
      <Results data={chosen.response} />
    </>
  );
}

export function Check() {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="check-title">
      <h2 id="check-title">{t("check.title")}</h2>
      <p>{t("check.intro")}</p>
      {MODE === "static" ? <StaticExamples /> : <LiveForm />}
    </section>
  );
}
