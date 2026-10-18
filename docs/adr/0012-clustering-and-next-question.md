# ADR 0012: Clustering rule and the next best question

Status: accepted

## Clustering

LINK edges form a graph. A plain connected component is not accepted, because a chain of
plausible links can join two records that clearly belong to different people. Union find
(written in `hawiyya.decision.cluster`, no graph library) adds LINK edges from the strongest
down and refuses any edge that would put a contradicted pair in one cluster. A contradicted
pair is a scored pair with log odds below -4 (ASSUMPTION). Refused edges go to REVIEW with
CLUSTER_CONFLICT.

## Next best question

For a REVIEW, each question the registration form can ask (scan the card, date of birth,
father's name, phone, passport number) has an agreeing and a disagreeing answer. The answer
probabilities and the posterior follow Bayes' rule with the model's m and u for those levels.
The value of a question is the current minimum expected cost minus the expected minimum cost
after the answer. Because the posterior is a martingale and the minimum cost is concave, the
value is never negative. The list feeds a reception dialogue in simulation only.
