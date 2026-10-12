# 하디-크로스 관망해석

폐회로 관망의 유량을 Hardy-Cross 반복법으로 맞추는 Python 프로그램입니다.

## 실행

```powershell
cd C:\Users\user\hardy-cross
python -m pip install -r requirements.txt
python app.py
```

브라우저에서 http://127.0.0.1:5050 을 연 뒤 **예제 불러오기** → **해석** 을 누르면 됩니다. 기본 예제는 수리학 **예제 5.14**(그림 5.5.2, 표 5.5.1)입니다.

단위 테스트:

```powershell
python -m pytest -q
```

이 환경에는 Git이 설치되어 있지 않아 저장소 초기화는 하지 않았습니다. Git을 설치한 뒤 `git init` 하면 됩니다.

## 계산

각 폐회로에서 손실수두의 대수합이 0이 되도록 보정유량 ΔQ를 더합니다.

```
ΔQ = − Σ hf / (n Σ |hf / Q|)
```

- **Hazen-Williams**: `hf = 10.67 L Q^1.852 / (C^1.852 D^4.87)`, `n = 1.852`
- **Darcy-Weisbach**: `hf = 8 f L Q |Q| / (π² g D⁵)`, `n = 2`

유량 부호는 관 **시점 → 종점**이 양입니다. 루프 멤버의 `sign`은 루프 순회가 그 방향과 같으면 `+1`, 반대면 `-1`입니다. 공유관은 속한 루프마다 보정을 받습니다. 초기 유량이 절점 연속방정식을 만족하면 보정 후에도 유지됩니다.

## 구조

| 파일 | 역할 |
|------|------|
| `hardy_cross/engine.py` | Hardy-Cross 반복, 입출력 모델 |
| `hardy_cross/friction.py` | 마찰 공식과 저항계수 r |
| `hardy_cross/examples.py` | 예제 5.14 관망 (표 5.5.1 k·가정유량) |
| `app.py` | Flask API |
| `static/index.html` | 입력·도식·결과 UI |
| `tests/test_engine.py` | 병렬관 평형, 예제 연속조건 |

## 처음 바꿔보기 좋은 곳

1. `hardy_cross/examples.py`의 `EXAMPLE_5_14` — 교재 제원·k·가정유량. UI **예제 불러오기**에 바로 반영됩니다.
2. `hardy_cross/engine.py`의 `solve()` — 순차 보정 대신 동시 보정(한 스텝의 모든 ΔQ를 한꺼번에 적용)으로 바꿔 수렴을 비교할 수 있습니다.
3. `static/index.html` — 표 컬럼이나 도식 색을 바꿔 UI를 익히기 좋습니다.
