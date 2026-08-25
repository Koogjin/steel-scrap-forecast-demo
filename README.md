# 미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo

### Target: **BLS WPU1012** — Iron and steel scrap
*U.S. Iron & Steel Scrap Producer Price Index Forecasting*

> **각 과거 시점에 실제로 공개되어 있던 정보만 사용해서 예측했습니다.**
> 무료 공개 데이터 · CPU only · 사전등록된 실험.

🎯 **예측 대상은 실제 $/ton 거래가격이 아니라 BLS 공식 생산자물가지수(PPI)입니다.**

---

## 예측 대상이 무엇인가

| | |
|---|---|
| **이 지수는 무엇인가?** | 미국 노동통계국(BLS)이 발표하는 **철·강 스크랩 제품군의 생산자물가지수**. BLS 상품코드 `10-12`, 월간, 비계절조정. 기준시점을 100으로 두고 그 이후의 **상대적인 가격 변화**를 측정합니다. |
| **오르면?** | 철·강 스크랩 제품군에 대해 **생산자들이 받는 가격 수준이 기준시점 대비 상승**하는 방향 |
| **내리면?** | 해당 제품군의 **생산자 가격 수준이 기준시점 대비 하락**하는 방향 |
| **무엇이 아닌가?** | 특정 기업 구매가격 ✗ · 특정 grade 거래가격 ✗ · **$/ton 현물가격 ✗** |

지수 값과 달러 금액은 다릅니다 — 지수 600은 톤당 600달러라는 뜻이 **아닙니다**.
월별 변화는 지수 포인트 차이보다 **percent change** 로 읽는 것이 자연스럽습니다.

---

## 한눈에 보기

| | |
|---|---|
| 예측 대상 | **BLS WPU1012** (Iron and steel scrap, PPI) |
| 설명변수 | Clean-PIT 6개 계열 → 12개 파생 지표 |
| 예측 시점 | **50개** (2021-11-30 ~ 2025-12-31) |
| 학습 행 | 72 ~ 118 — **M0/M1/M2 전부 동일** |
| 공식 사건·상태 | **17건** (2013-01~, 월 커버리지 73%) |
| 자동 테스트 | **729개** |
| FRED/ALFRED 의존 | **0** |
| 실행 커밋 | `6c34fcec308a` |

---

## 3단계 모델 구조

![모델 3단계](assets/model_stages.png)

| 단계 | 입력 |
|---|---|
| **M0** | 과거 PPI 이력 10개 |
| **M1** | M0 + 시장/산업 데이터 12개 |
| **M2** | M1 + 공식 사건 압력 (PEP / NEP) 2개 |

**M0/M1은 기존 사전등록 실험 결과이며, M2는 공식 사건 정보를 추가한 탐색적 확장
Demo입니다.** Demo V2에서는 셋을 **동일한 Train/Test 조건**에서 추가 비교합니다.

---

## Demo V2 결과 — 동일 Train/Test

두 가지 비교 방식을 함께 제시합니다.

- **A. 통제 비교** — 알고리즘을 Ridge로 고정하고 **정보만** 추가
- **B. Best-CV 벤치마크** — 각 예측시점의 **학습 데이터 안에서만** 모델 선택
  (Ridge / ElasticNet / RandomForest / HistGradientBoosting)

| 단계 | A. Ridge 고정 MAE | B. Best-CV MAE |
|---|---|---|
| M0 | 49.19 | 47.73 |
| M1 | 50.75 | 49.28 |
| M2 | 50.72 | 49.52 |

> **최종 Test 성능을 보고 모델을 고른 것이 아니라, 각 예측시점의 과거 학습데이터
> 내부에서만 모델을 선택했습니다.**

선택된 모델 분포: M0:elasticnet 25 · M0:ridge 25 · M1:elasticnet 21 · M1:ridge 29 · M2:elasticnet 20 · M2:ridge 30

![성능 비교](assets/forecast_comparison.png)

![실제 vs 예측](assets/forecast_actual_vs_pred.png)

---

## 기존 사전등록 결과 (원본 보존)

결과를 보기 **전에** 규칙을 고정한 실험의 원본 결과입니다. Demo V2는 이를 대체하지
않습니다.

| 모델 | MAE | RMSE |
|---|---|---|
| N0 | 50.32 | 69.40 |
| M0 | 49.19 | 76.20 |
| M1 | 50.75 | 80.77 |

사전등록된 주요 가설(M0 vs M1): 상대 개선 **-3.2%**, DM 검정 p = **0.727** —
개선 증거 없음. 결과가 기대와 달랐지만 사전에 고정한 모델·기간·지표를 바꾸지
않았습니다.

---

## 공식 사건 압력 (PEP / NEP)

뉴스 기사 원문을 수집하지 않습니다. **공식적으로 확인된 사건과 상태**를 구조화해
두 개의 압력 변수로 변환합니다.

- **PEP** — 가격 **상승** 압력 증거 (0~1)
- **NEP** — 가격 **하락** 압력 증거 (0~1)

감성분석이 아니며 두 지표는 **독립**입니다. 관세처럼 상승·하락 채널을 동시에 갖는
사건은 두 값이 함께 올라갑니다.

**POINT 사건**(단발성 발표)과 **ONGOING 상태**(관세·제재·분쟁처럼 지속되는 상태)를
구분해, 월을 채우려고 사건을 만들지 않고도 긴 이력에서 신호가 유지됩니다.

![사건 압력 타임라인](assets/event_pressure_timeline.png)

출처: U.S. Federal Register · U.S. Department of the Treasury ·
U.S. Department of Defense · U.S. Department of Commerce · U.S. CDC.
전체 목록과 링크는 [`data/event_registry_v2.csv`](data/event_registry_v2.csv),
방법론은 [`docs/event_method.md`](docs/event_method.md).

---

## 왜 Clean-PIT 인가

**2023년 시점을 예측할 때 2026년에 수정된 최종 WPU1012 값을 사용하는 것이 아니라,
당시 실제로 공개되어 있던 값만 사용합니다.**

경제지표는 최초 발표 후 여러 차례 개정됩니다. 개정된 값으로 과거를 학습하면 실제
운영에서는 재현되지 않는 성능이 나옵니다.

```
forecast origin O 에서 사용 가능한 값
  = release_date <= O 인 발표분 중 가장 최근 값
```

---

## Claude Code Agent Team

![Agent Team workflow](assets/claude_code_workflow.png)

> 역할별 Agent Team 을 구성해 복잡한 프로젝트를 End-to-End 로 수행했습니다.
> 연구자가 연구 원칙과 판단 기준을 정의하고, Agent Team 이 조사·구현·검증·문서화를
> 수행했습니다.

---

## 대시보드 실행

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

앱은 `data/` 의 사전 계산된 결과만 읽습니다. 외부 API 호출·데이터 수집·모델 학습을
하지 않으므로 연구용 노트북이 꺼져 있어도 동작합니다.

## 문서

- [경영진 요약](docs/executive_summary.md)
- [방법론 요약](docs/methodology_summary.md)
- [사건 압력 방법론](docs/event_method.md)
- [배포 보안 감사](docs/DEPLOYMENT_AUDIT.md)

---

## 한계 (경영진 보고 시 함께 전달)

- 예측 시점 50개로 검정력이 제한적입니다. **"유의하지 않음"과 "효과 없음"은 다릅니다.**
- Clean-PIT 대상 패널의 관측월이 137개뿐이라 학습 구간이 짧습니다.
- 설명변수가 미국 공급·산업활동 축에 치우쳐 있고, 원자재 가격·전방 수요·환율 축이 비어 있습니다.
- 사건 압력(M2)은 **탐색적 확장**이며 정식 연구 검증 대상이 아닙니다.
- 이 Demo는 **공개 지수** 예측이며 특정 기업의 구매가격 예측이 아닙니다.
