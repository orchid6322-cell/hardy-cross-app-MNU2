from copy import deepcopy

from hardy_cross.engine import Loop, Network, Pipe, solve
from hardy_cross.examples import EXAMPLE_5_14, TWO_LOOP
from hardy_cross.friction import Formula, resistance, signed_head_loss


def test_parallel_two_pipe_loop_darcy():
    """병렬 2관: Q1+Q2 보존, 평형에서 r1 Q1² = r2 Q2²."""
    net = Network(
        formula=Formula.DARCY_WEISBACH,
        pipes=[
            Pipe("A", "J1", "J2", length_m=100, diameter_m=0.2, q_m3s=0.30, f=0.02),
            Pipe("B", "J1", "J2", length_m=200, diameter_m=0.2, q_m3s=0.30, f=0.02),
        ],
        loops=[Loop("L", [("A", 1), ("B", -1)])],
    )
    r1 = resistance(100, 0.2, Formula.DARCY_WEISBACH, f=0.02)
    r2 = resistance(200, 0.2, Formula.DARCY_WEISBACH, f=0.02)
    total = 0.60
    result = solve(net, tolerance=1e-10, max_iter=50)
    assert result.converged
    q1 = next(p.q_m3s for p in result.pipes if p.id == "A")
    q2 = next(p.q_m3s for p in result.pipes if p.id == "B")
    assert abs(q1 + q2 - total) < 1e-9
    hf1 = signed_head_loss(r1, q1, 2.0)
    hf2 = signed_head_loss(r2, q2, 2.0)
    assert abs(hf1 - hf2) < 1e-6


def test_two_loop_example_balances():
    net = deepcopy(TWO_LOOP)
    result = solve(net, tolerance=1e-8, max_iter=80)
    assert result.converged
    pipes = {p.id: p for p in result.pipes}
    # 연속: A 유입 0.12 = P1+P2, D 유출 = P4+P5
    assert abs(pipes["P1"].q_m3s + pipes["P2"].q_m3s - 0.12) < 1e-9
    assert abs(pipes["P4"].q_m3s + pipes["P5"].q_m3s - 0.12) < 1e-9
    assert abs(pipes["P1"].q_m3s - pipes["P3"].q_m3s - pipes["P4"].q_m3s) < 1e-9
    last = result.history[-1]
    assert last.max_abs_sum_hf < 1e-4


def test_example_5_14_matches_textbook_table():
    """표 5.5.1의 1·2차 수정유량과 같은 순서로 맞는다."""
    net = deepcopy(EXAMPLE_5_14)
    result = solve(net, tolerance=1e-4, max_iter=20)
    q1 = result.history[0].flows
    assert abs(q1["1"] - 2.791) < 0.01
    assert abs(q1["2"] - 2.209) < 0.01
    assert abs(q1["3"] - 0.414) < 0.015
    assert abs(q1["4"] - 3.205) < 0.01
    assert abs(q1["5"] - 3.205) < 0.01
    assert abs(q1["6"] - 1.795) < 0.01
    dq = {s.loop_id: s.delta_q for s in result.history[0].loops}
    assert abs(dq["I"] - 0.291) < 0.01
    assert abs(dq["II"] - (-0.296)) < 0.01

    q2 = result.history[1].flows
    assert abs(q2["1"] - 2.780) < 0.01
    assert abs(q2["2"] - 2.220) < 0.01
    assert abs(q2["3"] - 0.441) < 0.015
    assert abs(q2["4"] - 3.221) < 0.015
    assert abs(q2["5"] - 3.221) < 0.015
    assert abs(q2["6"] - 1.779) < 0.015

    pipes = {p.id: p for p in result.pipes}
    assert abs(pipes["1"].q_m3s + pipes["2"].q_m3s - 5.0) < 1e-6
    assert abs(pipes["5"].q_m3s + pipes["6"].q_m3s - 5.0) < 1e-6
