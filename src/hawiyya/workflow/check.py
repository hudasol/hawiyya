"""Registration time duplicate check: one new registration against the registry.

The registry is indexed once by the same blocking keys as batch matching. A check normalises
the new record, collects candidates that share any key, scores each with the frozen model and
returns them ranked. If anything fails, the check fails open: it returns an empty advisory
result and registration continues.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from hawiyya.contract.models import PairScore, Record
from hawiyya.core.safelog import safe_event
from hawiyya.matching.blocking import record_keys
from hawiyya.matching.compare import RecFeat, features
from hawiyya.normalise.record import RegistryContext, apply_learned, normalise_record
from hawiyya.scoring.scorer import Model, Scorer

MAX_CANDIDATES = 200  # bound on candidates scored per check (largest blocks first dropped)


@dataclass(frozen=True)
class CheckCandidate:
    record: Record
    score: PairScore


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    candidates: tuple[CheckCandidate, ...]
    n_scored: int
    note: str = ""


@dataclass
class RegistryIndex:
    ctx: RegistryContext
    records: dict[str, Record]
    feats: dict[str, RecFeat]
    keys: dict[tuple[str, str], list[str]] = field(default_factory=dict)

    @staticmethod
    def build(ctx: RegistryContext, records: Sequence[Record]) -> RegistryIndex:
        keys: dict[tuple[str, str], list[str]] = defaultdict(list)
        for r in ctx.records:
            for k in set(record_keys(r)):
                keys[k].append(r.record_id)
        return RegistryIndex(
            ctx=ctx,
            records={r.record_id: r for r in records},
            feats={r.record_id: features(r) for r in ctx.records},
            keys=dict(keys),
        )

    def candidates_for(self, rec_feat: RecFeat) -> list[str]:
        hits: dict[str, int] = defaultdict(int)
        blocks = sorted((self.keys.get(k, []) for k in set(record_keys(rec_feat.rec))), key=len)
        for members in blocks:
            for rid in members:
                hits[rid] += 1
        ranked = sorted(hits, key=lambda rid: (-hits[rid], rid))
        return ranked[:MAX_CANDIDATES]


def run_check(index: RegistryIndex, model: Model, new: Record, top: int = 10,
              exclude_self: bool = True) -> CheckResult:
    """Ranked candidates for one registration. Fails open on any internal error."""
    try:
        nrec = apply_learned(normalise_record(new), index.ctx.learned)
        feat = features(nrec)
        scorer = Scorer(model, index.ctx.tf)
        out = []
        cands = index.candidates_for(feat)
        for rid in cands:
            if exclude_self and rid == new.record_id:
                continue
            ps = scorer.pair_score(feat, index.feats[rid])
            out.append(CheckCandidate(index.records[rid], ps))
        out.sort(key=lambda c: (-c.score.log_odds, c.record.record_id))
        safe_event("registration_check", candidates=len(cands), returned=min(top, len(out)))
        return CheckResult(True, tuple(out[:top]), len(cands))
    except Exception as exc:  # fail open: registration must never be blocked
        safe_event("registration_check_failed", error=type(exc).__name__)
        return CheckResult(False, (), 0, "check unavailable; registration continues")


CheckFn = Callable[[Record], CheckResult]
