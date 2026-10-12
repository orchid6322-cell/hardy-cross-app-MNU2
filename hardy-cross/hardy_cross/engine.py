"""하디-크로스 반복법.

각 폐회로에서 Σhf → 0 이 되도록 회로 유량 보정 ΔQ를 적용한다.
고전적 순차 보정: 한 루프의 ΔQ를 바로 반영한 뒤 다음 루프를 계산한다.
연속방정식은 초기 유량이 만족하면 루프 보정만으로 유지된다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hardy_cross.friction import Formula, pipe_resistance, signed_head_loss, velocity

EPS_Q = 1e-12


@dataclass
class Pipe:
    id: str
    start: str
    end: str
    length_m: float
    diameter_m: float
    q_m3s: float
    c: float = 100.0
    f: float = 0.02
    k: float | None = None
    label: str = ""


@dataclass
class Loop:
    id: str
    """(pipe_id, sign). sign=+1 이면 루프 순회 방향이 관 시점→종점."""
    members: list[tuple[str, int]]
    label: str = ""


@dataclass
class Node:
    id: str
    x: float
    y: float
    label: str = ""


@dataclass
class Network:
    pipes: list[Pipe]
    loops: list[Loop]
    nodes: list[Node] = field(default_factory=list)
    formula: Formula = Formula.HAZEN_WILLIAMS

    def pipe_map(self) -> dict[str, Pipe]:
        return {p.id: p for p in self.pipes}


@dataclass
class PipeResult:
    id: str
    start: str
    end: str
    q_m3s: float
    velocity_ms: float
    head_loss_m: float
    r: float
    length_m: float
    diameter_m: float


@dataclass
class LoopSnapshot:
    loop_id: str
    sum_hf: float
    delta_q: float


@dataclass
class IterationRecord:
    iteration: int
    max_abs_dq: float
    max_abs_sum_hf: float
    loops: list[LoopSnapshot]
    flows: dict[str, float]


@dataclass
class SolveResult:
    converged: bool
    iterations: int
    formula: str
    exponent: float
    pipes: list[PipeResult]
    history: list[IterationRecord]
    message: str

    def to_dict(self) -> dict:
        return {
            "converged": self.converged,
            "iterations": self.iterations,
            "formula": self.formula,
            "exponent": self.exponent,
            "message": self.message,
            "pipes": [p.__dict__ for p in self.pipes],
            "history": [
                {
                    "iteration": h.iteration,
                    "max_abs_dq": h.max_abs_dq,
                    "max_abs_sum_hf": h.max_abs_sum_hf,
                    "loops": [s.__dict__ for s in h.loops],
                    "flows": h.flows,
                }
                for h in self.history
            ],
        }


def _optional_k(value) -> float | None:
    if value in (None, "", False):
        return None
    k = float(value)
    return k if k > 0 else None


def _tiny_q(q: float) -> float:
    if abs(q) < EPS_Q:
        return EPS_Q if q >= 0 else -EPS_Q
    return q


def solve(
    network: Network,
    *,
    tolerance: float = 1e-6,
    max_iter: int = 80,
    hf_tolerance: float | None = None,
) -> SolveResult:
    """관망을 제자리(in-place)로 갱신하고 결과를 반환한다."""
    if not network.pipes:
        raise ValueError("관이 없습니다.")
    if not network.loops:
        raise ValueError("폐회로가 없습니다.")

    pipes = network.pipe_map()
    formula = network.formula
    n = formula.exponent
    hf_tol = hf_tolerance if hf_tolerance is not None else max(tolerance * 10.0, 1e-5)

    for loop in network.loops:
        if not loop.members:
            raise ValueError(f"루프 {loop.id}에 관이 없습니다.")
        for pid, sign in loop.members:
            if pid not in pipes:
                raise ValueError(f"루프 {loop.id}의 관 {pid}를 찾을 수 없습니다.")
            if sign not in (1, -1):
                raise ValueError(f"루프 {loop.id}의 부호는 +1 또는 -1 이어야 합니다.")

    history: list[IterationRecord] = []
    converged = False
    used = 0

    for k in range(1, max_iter + 1):
        used = k
        snapshots: list[LoopSnapshot] = []
        max_dq = 0.0
        max_hf = 0.0

        for loop in network.loops:
            sum_hf = 0.0
            sum_dh_dq = 0.0
            for pid, sign in loop.members:
                pipe = pipes[pid]
                r = pipe_resistance(pipe, formula)
                q = _tiny_q(pipe.q_m3s)
                hf = signed_head_loss(r, q, n)
                sum_hf += sign * hf
                sum_dh_dq += n * r * abs(q) ** (n - 1.0)

            if sum_dh_dq == 0:
                raise ValueError(f"루프 {loop.id}의 Σ|∂hf/∂Q| 가 0입니다.")

            dq = -sum_hf / sum_dh_dq
            for pid, sign in loop.members:
                pipes[pid].q_m3s += sign * dq

            snapshots.append(LoopSnapshot(loop.id, sum_hf, dq))
            max_dq = max(max_dq, abs(dq))
            max_hf = max(max_hf, abs(sum_hf))

        history.append(
            IterationRecord(
                iteration=k,
                max_abs_dq=max_dq,
                max_abs_sum_hf=max_hf,
                loops=snapshots,
                flows={p.id: p.q_m3s for p in network.pipes},
            )
        )
        if max_dq < tolerance and max_hf < hf_tol:
            converged = True
            break

    results: list[PipeResult] = []
    for pipe in network.pipes:
        r = pipe_resistance(pipe, formula)
        q = pipe.q_m3s
        results.append(
            PipeResult(
                id=pipe.id,
                start=pipe.start,
                end=pipe.end,
                q_m3s=q,
                velocity_ms=velocity(q, pipe.diameter_m),
                head_loss_m=signed_head_loss(r, _tiny_q(q), n),
                r=r,
                length_m=pipe.length_m,
                diameter_m=pipe.diameter_m,
            )
        )

    if converged:
        msg = f"{used}회 반복 후 수렴했습니다. (max|ΔQ| < {tolerance:g})"
    else:
        msg = f"{max_iter}회 안에 수렴하지 않았습니다. 초기유량·허용오차·관 계수를 확인하세요."

    return SolveResult(
        converged=converged,
        iterations=used,
        formula=formula.value,
        exponent=n,
        pipes=results,
        history=history,
        message=msg,
    )


def network_from_dict(data: dict) -> Network:
    formula = Formula(data.get("formula", Formula.HAZEN_WILLIAMS.value))
    nodes = [
        Node(id=str(n["id"]), x=float(n["x"]), y=float(n["y"]), label=str(n.get("label", n["id"])))
        for n in data.get("nodes", [])
    ]
    pipes = [
        Pipe(
            id=str(p["id"]),
            start=str(p["start"]),
            end=str(p["end"]),
            length_m=float(p["length_m"]),
            diameter_m=float(p["diameter_m"]),
            q_m3s=float(p["q_m3s"]),
            c=float(p.get("c", 100)),
            f=float(p.get("f", 0.02)),
            k=_optional_k(p.get("k")),
            label=str(p.get("label", p["id"])),
        )
        for p in data["pipes"]
    ]
    loops = [
        Loop(
            id=str(lp["id"]),
            members=[(str(m["pipe"]), int(m["sign"])) for m in lp["members"]],
            label=str(lp.get("label", lp["id"])),
        )
        for lp in data["loops"]
    ]
    return Network(pipes=pipes, loops=loops, nodes=nodes, formula=formula)
