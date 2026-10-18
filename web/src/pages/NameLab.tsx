import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { analyseName, getNameExamples, MODE, type NameAnalysis } from "../api";
import { ErrorBox, Loading, Name } from "../components/Basics";
import { usePrefs } from "../prefs";

function Analysis({ data }: { data: NameAnalysis }) {
  const { t } = useTranslation();
  const { lang } = usePrefs();
  const s = data.structure;
  return (
    <div className="card" data-testid="name-analysis">
      <p>
        {t("names.normalised")}: <Name value={data.normalised} /> · {t("names.script")}:{" "}
        <span className="mono">{data.input_script}</span>
      </p>
      <h3>{t("names.structure")}</h3>
      <table>
        <tbody>
          {(["given", "father", "grandfather", "family"] as const).map((k) => (
            <tr key={k}>
              <th scope="row">{t(`names.${k}`)}</th>
              <td>
                <Name value={(s[k] as string | null) ?? null} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>{t("names.tokens")}</h3>
      <table>
        <thead>
          <tr>
            <th scope="col">{t("names.token")}</th>
            <th scope="col">{t("names.skeleton")}</th>
            <th scope="col">{t("names.coarse")}</th>
          </tr>
        </thead>
        <tbody>
          {data.tokens.map((tok, i) => (
            <tr key={`${tok.token}-${i}`}>
              <td>
                <Name value={tok.token} />
              </td>
              <td className="mono">{tok.skeleton}</td>
              <td className="mono">{tok.coarse}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>{t("names.variants")}</h3>
      {Object.entries(data.generator_variants).map(([style, vs]) => (
        <p key={style}>
          <span className="mono">{style}</span>:{" "}
          {vs.map((v, i) => (
            <span key={`${v}-${i}`}>
              <Name value={v} />
              {i < vs.length - 1 ? ", " : ""}
            </span>
          ))}
        </p>
      ))}
      <h3>{t("names.collisions")}</h3>
      <p className="muted">{t("names.collision_note")}</p>
      <ul>
        {data.collisions.map((g) => (
          <li key={g.join("|")}>
            {g.map((n, i) => (
              <span key={n}>
                <Name value={n} />
                {i < g.length - 1 ? ", " : ""}
              </span>
            ))}
          </li>
        ))}
      </ul>
      {data.comparison ? (
        <>
          <h3>{t("names.comparison")}</h3>
          <table>
            <tbody>
              {Object.entries(data.comparison).map(([field, v]) => (
                <tr key={field}>
                  <th scope="row">{field}</th>
                  <td>{lang === "ar" ? v.label_ar : v.label_en}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : null}
    </div>
  );
}

function LiveLab() {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [other, setOther] = useState("");
  const m = useMutation({ mutationFn: () => analyseName(name, other) });
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (name.trim()) m.mutate();
  };
  return (
    <>
      <form className="card" onSubmit={submit}>
        <div className="form-grid">
          <label>
            {t("names.name")}
            <input dir="auto" value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label>
            {t("names.other")}
            <input dir="auto" value={other} onChange={(e) => setOther(e.target.value)} />
          </label>
        </div>
        <div style={{ marginBlockStart: "1rem" }}>
          <button className="primary" type="submit">
            {t("names.analyse")}
          </button>
        </div>
      </form>
      {m.isPending ? <Loading /> : null}
      {m.isError ? <ErrorBox error={m.error} /> : null}
      {m.data ? <Analysis data={m.data} /> : null}
    </>
  );
}

function StaticLab() {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["name-examples"], queryFn: getNameExamples });
  const [idx, setIdx] = useState(0);
  if (q.isPending) return <Loading />;
  if (q.isError) return <ErrorBox error={q.error} />;
  const ex = q.data[idx] ?? q.data[0];
  return (
    <>
      <p className="card">{t("names.static_note")}</p>
      <label>
        {t("names.name")}
        <select value={idx} onChange={(e) => setIdx(Number(e.target.value))}>
          {q.data.map((e, i) => (
            <option key={e.name} value={i}>
              {e.name}
            </option>
          ))}
        </select>
      </label>
      {ex ? <Analysis data={ex.response} /> : null}
    </>
  );
}

export function NameLab() {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="names-title">
      <h2 id="names-title">{t("names.title")}</h2>
      <p>{t("names.intro")}</p>
      {MODE === "static" ? <StaticLab /> : <LiveLab />}
    </section>
  );
}
