import { useTranslation } from "react-i18next";

/** The synthetic data banner. Always rendered, never dismissable. */
export function SyntheticBanner() {
  const { t } = useTranslation();
  return (
    <div className="banner" role="note" data-testid="synthetic-banner">
      {t("app.banner")}
    </div>
  );
}

/** Every person name and identifier goes through this bidi isolating element, so Arabic and
 * Latin text never reorders the digits or punctuation around it. */
export function Name({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="muted">-</span>;
  return (
    <bdi className="name" dir="auto" data-testid="name">
      {value}
    </bdi>
  );
}

/** The name renderings a record holds, each isolated, on separate lines. */
export function Names({ ar, latin }: { ar?: string | null; latin?: string | null }) {
  const present = [ar, latin].filter((v): v is string => Boolean(v));
  if (!present.length) return <span className="muted">-</span>;
  return (
    <div>
      {present.map((v) => (
        <div key={v}>
          <Name value={v} />
        </div>
      ))}
    </div>
  );
}

export function Ident({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="muted">-</span>;
  return (
    <bdi className="name mono" dir="ltr" data-testid="name">
      {value}
    </bdi>
  );
}

export type DecisionKind = "LINK" | "REVIEW" | "KEEP_APART";

/** Decision encoded by shape and label as well as colour. */
export function DecisionBadge({ kind }: { kind: DecisionKind }) {
  const { t } = useTranslation();
  const shape =
    kind === "LINK" ? (
      <circle cx="8" cy="8" r="6" fill="currentColor" />
    ) : kind === "REVIEW" ? (
      <polygon points="8,1 15,15 1,15" fill="currentColor" />
    ) : (
      <rect x="2" y="2" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="3" />
    );
  return (
    <span className={`decision ${kind}`} data-decision={kind}>
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        {shape}
      </svg>
      {t(`decision.${kind}`)}
    </span>
  );
}

export function Loading() {
  const { t } = useTranslation();
  return (
    <p role="status" aria-live="polite">
      {t("app.loading")}
    </p>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  const { t } = useTranslation();
  return (
    <div className="card" role="alert">
      <strong>{t("app.error")}</strong>
      <div className="muted mono">{error instanceof Error ? error.message : String(error)}</div>
    </div>
  );
}

export function Empty() {
  const { t } = useTranslation();
  return <p className="muted">{t("app.empty")}</p>;
}
