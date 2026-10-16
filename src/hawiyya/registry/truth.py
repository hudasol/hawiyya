"""Truth view: ground truth labels and pair categories. Never imported by L2 to L5."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

from hawiyya.contract.enums import IdKind
from hawiyya.contract.models import Record, TruthLabels
from hawiyya.registry.people import People

HARD_NEGATIVES = (
    "twin",
    "sibling",
    "father_son_same_name",
    "parent_child",
    "newborn_mother_shared_id",
    "cousin",
    "spouse",
    "shared_placeholder",
    "same_dob_sex",
)
PAIR_CATEGORIES = ("match", *HARD_NEGATIVES, "other_nonmatch")


@dataclass(frozen=True)
class TruthView:
    labels: dict[str, TruthLabels]
    people: People

    def is_placeholder(self, record_id: str) -> bool:
        """True when the generator injected a placeholder identifier into this record."""
        return "id:placeholder" in self.labels[record_id].corruption_log

    def person_of(self, record_id: str) -> str:
        return self.labels[record_id].person_id

    def is_match(self, a: str, b: str) -> bool:
        return self.labels[a].person_id == self.labels[b].person_id

    def true_pairs(self) -> set[tuple[str, str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for rid, lab in self.labels.items():
            groups[lab.person_id].append(rid)
        out: set[tuple[str, str]] = set()
        for ids in groups.values():
            for a, b in combinations(sorted(ids), 2):
                out.add((a, b))
        return out

    def category(self, ra: Record, rb: Record) -> str:
        """Category of a record pair: match, one of the hard negatives, or other."""
        la, lb = self.labels[ra.record_id], self.labels[rb.record_id]
        if la.person_id == lb.person_id:
            return "match"
        pa, pb = self.people.get(la.person_id), self.people.get(lb.person_id)
        if pa.twin_group and pa.twin_group == pb.twin_group:
            return "twin"
        if pa.family_id == pb.family_id:
            if pa.role == "child" and pb.role == "child":
                return "sibling"
            parent_child = pa.person_id in (pb.father_id, pb.mother_id) or pb.person_id in (
                pa.father_id, pa.mother_id)  # fmt: skip
            if parent_child:
                same_name = ("same_name_as_father" in pa.flags and pa.father_id == pb.person_id) or (
                    "same_name_as_father" in pb.flags and pb.father_id == pa.person_id)  # fmt: skip
                if same_name:
                    return "father_son_same_name"
                if (ra.id_kind == IdKind.MOTHER_EID or rb.id_kind == IdKind.MOTHER_EID) and (
                    ra.id_value == rb.id_value
                ):
                    return "newborn_mother_shared_id"
                return "parent_child"
            return "spouse"
        if pa.clan_id and pa.clan_id == pb.clan_id:
            return "cousin"
        if (self.is_placeholder(ra.record_id) and self.is_placeholder(rb.record_id)
                and ra.id_value == rb.id_value):  # fmt: skip
            return "shared_placeholder"
        if pa.birth_date == pb.birth_date and pa.sex == pb.sex:
            return "same_dob_sex"
        return "other_nonmatch"
