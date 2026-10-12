"""관 마찰 손실수두. SI 단위 (m, m³/s)."""

from __future__ import annotations

import math
from enum import Enum

G = 9.80665
HW_K = 10.67  # hf = 10.67 L Q^1.852 / (C^1.852 D^4.87)


class Formula(str, Enum):
    HAZEN_WILLIAMS = "hazen_williams"
    DARCY_WEISBACH = "darcy_weisbach"

    @property
    def exponent(self) -> float:
        return 1.852 if self is Formula.HAZEN_WILLIAMS else 2.0


def resistance(length_m: float, diameter_m: float, formula: Formula, *, c: float = 100.0, f: float = 0.02) -> float:
    """hf = r · Q · |Q|^{n-1} 에서의 r."""
    if length_m <= 0 or diameter_m <= 0:
        raise ValueError("관 길이와 관경은 양수여야 합니다.")
    if formula is Formula.HAZEN_WILLIAMS:
        if c <= 0:
            raise ValueError("Hazen-Williams C는 양수여야 합니다.")
        return HW_K * length_m / (c**1.852 * diameter_m**4.87)
    if f <= 0:
        raise ValueError("Darcy 마찰계수 f는 양수여야 합니다.")
    return 8.0 * f * length_m / (math.pi**2 * G * diameter_m**5)


def pipe_resistance(pipe, formula: Formula) -> float:
    """교재 k가 있으면 그 값을 쓰고, 없으면 L·D·C(또는 f)로 산정한다."""
    if getattr(pipe, "k", None) not in (None, ""):
        k = float(pipe.k)
        if k <= 0:
            raise ValueError("관 저항계수 k는 양수여야 합니다.")
        return k
    return resistance(pipe.length_m, pipe.diameter_m, formula, c=pipe.c, f=pipe.f)


def signed_head_loss(r: float, q_m3s: float, n: float) -> float:
    """시점→종점 방향 손실수두 (유량이 음이면 부호가 반대)."""
    if q_m3s == 0:
        return 0.0
    return r * q_m3s * abs(q_m3s) ** (n - 1.0)


def velocity(q_m3s: float, diameter_m: float) -> float:
    area = math.pi * diameter_m**2 / 4.0
    return q_m3s / area
