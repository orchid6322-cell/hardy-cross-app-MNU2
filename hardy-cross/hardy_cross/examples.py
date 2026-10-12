"""내장 예제 관망."""

from hardy_cross.engine import Loop, Network, Node, Pipe
from hardy_cross.friction import Formula

# 수리학 예제 5.14 / 그림 5.5.2 / 표 5.5.1
# ① 유입 5 m³/s, ③ 유출 5 m³/s, Hazen-Williams k는 교재 값
#
#        5 m³/s
#          ①
#         /  \
#       2/    \1
#       /      \
#      ⑤--3----②--4--④
#       \              \
#       6\              \5
#         \______③______/
#                5 m³/s
EXAMPLE_5_14 = Network(
    formula=Formula.HAZEN_WILLIAMS,
    nodes=[
        Node("1", 160, 36, "① 유입 5"),
        Node("2", 300, 70, "②"),
        Node("4", 410, 95, "④"),
        Node("5", 70, 210, "⑤"),
        Node("3", 390, 250, "③ 유출 5"),
    ],
    pipes=[
        Pipe("1", "1", "2", length_m=2000, diameter_m=2.0, q_m3s=2.5, c=100, k=0.146),
        Pipe("2", "1", "5", length_m=3000, diameter_m=2.0, q_m3s=2.5, c=100, k=0.218),
        Pipe("3", "5", "2", length_m=1000, diameter_m=2.0, q_m3s=1.0, c=100, k=0.073),
        Pipe("4", "2", "4", length_m=1000, diameter_m=2.0, q_m3s=3.5, c=100, k=0.073),
        Pipe("5", "4", "3", length_m=1000, diameter_m=1.8, q_m3s=3.5, c=100, k=0.122),
        Pipe("6", "5", "3", length_m=2000, diameter_m=1.5, q_m3s=1.5, c=100, k=0.590),
    ],
    loops=[
        Loop("I", [("1", 1), ("2", -1), ("3", -1)], "회로 I"),
        Loop("II", [("3", 1), ("4", 1), ("5", 1), ("6", -1)], "회로 II"),
    ],
)

# 작은 두 폐회로 (단위 테스트용)
TWO_LOOP = Network(
    formula=Formula.HAZEN_WILLIAMS,
    nodes=[
        Node("A", 200, 40, "A 유입"),
        Node("B", 80, 180, "B"),
        Node("C", 320, 180, "C"),
        Node("D", 200, 320, "D 유출"),
    ],
    pipes=[
        Pipe("P1", "A", "B", length_m=400, diameter_m=0.30, q_m3s=0.07, c=100),
        Pipe("P2", "A", "C", length_m=400, diameter_m=0.25, q_m3s=0.05, c=100),
        Pipe("P3", "B", "C", length_m=300, diameter_m=0.20, q_m3s=0.02, c=100),
        Pipe("P4", "B", "D", length_m=350, diameter_m=0.25, q_m3s=0.05, c=100),
        Pipe("P5", "C", "D", length_m=350, diameter_m=0.30, q_m3s=0.07, c=100),
    ],
    loops=[
        Loop("L1", [("P1", 1), ("P3", 1), ("P2", -1)], "A-B-C"),
        Loop("L2", [("P3", 1), ("P5", 1), ("P4", -1)], "B-C-D"),
    ],
)


def network_to_dict(n: Network, *, tolerance: float = 1e-4, max_iter: int = 80) -> dict:
    return {
        "formula": n.formula.value,
        "tolerance": tolerance,
        "max_iter": max_iter,
        "nodes": [{"id": nd.id, "x": nd.x, "y": nd.y, "label": nd.label} for nd in n.nodes],
        "pipes": [
            {
                "id": p.id,
                "start": p.start,
                "end": p.end,
                "length_m": p.length_m,
                "diameter_m": p.diameter_m,
                "q_m3s": p.q_m3s,
                "c": p.c,
                "f": p.f,
                "k": p.k,
            }
            for p in n.pipes
        ],
        "loops": [
            {
                "id": lp.id,
                "label": lp.label,
                "members": [{"pipe": pid, "sign": s} for pid, s in lp.members],
            }
            for lp in n.loops
        ],
    }


def example_dict() -> dict:
    return network_to_dict(EXAMPLE_5_14)


def two_loop_dict() -> dict:
    return network_to_dict(TWO_LOOP)
