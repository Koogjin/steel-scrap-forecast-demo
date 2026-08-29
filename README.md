# Commodity Intelligence

**Release-Aware Commodity Nowcasting with True Point-in-Time Data**

*공식 데이터 공개 시점 기반 Commodity Rolling Nowcast*

> 월간 Commodity 지표를 **실제 공식 데이터 공개 시점**에 맞춰 갱신하며, 
> History · Market · Event 정보의 incremental predictive value 를 검증한 연구 프로젝트입니다.

`Python 3.13` · `CPU only` · `true point-in-time` · `reproducible` · `paper candidate`

---

## 1. 프로젝트 개요

이 연구는 **미국 철·강 스크랩 생산자물가지수(PPI)** 예측에서 시작해 **철광석·원유**로 확장했습니다. 상품을 늘리는 과정에서 중심 질문이 바뀌었습니다.

> 월간 지표 예측은 흔히 **그 시점에 실제로는 알 수 없었던 데이터**로 평가됩니다. 
> 예측 품질은 *어떤 변수를 쓰는가*뿐 아니라 **공식 정보가 언제 공개되는가**에 달려 있습니다.

그래서 이 프로젝트는 각 과거 시점의 **정보 집합을 실제로 재구성**하고(true Point-in-Time), 대상월 안에서 **W0 → W4** 다섯 시점으로 예측을 갱신하며 History / Market / Event 층의 기여를 분리합니다.

## 2. 연구 질문

> 공식 정보가 시간에 따라 도착할 때 commodity 예측을 어떻게 갱신해야 하고, 어떤 정보가 실제로 예측을 개선하며, 경제적으로 material 한 **희소 Event 층**이 History·Market 정보 위에 무언가를 더하는가?

| | |
|---|---|
| **RQ1** | true-PIT release-aware 갱신이 월간 commodity nowcast 를 개선하는가? |
| **RQ2** | 개선을 설명하는 정보 도착은 무엇인가 — Target History · Market/X · Event? |
| **RQ3** | 그 효과가 matched historical support 아래에서 상품 전반에 재현되는가? |
| **RQ4** | 경제적으로 걸러낸 Material Event 가 정례 공식 발표를 넘어 증분 가치를 갖는가? |

## 3. 핵심 결과

| 발견 | 결과 |
|---|---|
| **Release-aware nowcast** | W0→W4 오차가 세 Primary 상품 모두에서 감소 (**+45.4%** · +36.1% · +20.2%) |
| **가장 큰 기여** | 월 중순 전월 공식 지수 도착 — 50개월 중 **36개월**이 W2 까지 새 target 발표를 받음 |
| **Target-Specific X** | 상대적으로 제한적 (W4 기준 +1.5% · +1.3% · -0.1%) |
| **Material Event** | 안정적 증분 예측 가치 **없음** (W4 기준 -1.2% · -1.3% · +0.0%) |
| **더 긴 true-PIT 이력** | 과거이력 기준선을 유의하게 개선 (V9: 49.19 → 45.57, p=0.045) |
| **검증** | 50개월 historical OOS + prospective 사전 잠금 수집 시작 |

연구 이력 전체에서 가장 강한 긍정·부정 발견은 다음 한 문장으로 요약됩니다.

> **정보 갱신 주기가 모델보다 컸고, 공식 사건 정보는 이 문제에서 예측 가치를 갖지 않았다.**

## 4. Release-Aware Nowcast 프레임워크

대상월 `T` 하나를 다섯 시점에서 예측합니다. **예측 대상은 고정이고 정보만 늘어납니다.**

```text
  W0            W1            W2            W3            W4
  전월 말일      7일           14일          21일          말일
    │             │             │             │             │
    └─ release_date ≤ cutoff 인 관측 + known_at ≤ cutoff 인 Event 만 사용

  M0 = History only
  M1 = + Target-Specific Market / Industry
  M2 = + Material Event      (활성 Event 없으면 M2 ≡ M1)
```

W0 기준선을 고정하지 않습니다 — **정보 집합 전체가 매 시점 갱신**됩니다.

## 5. 예측 대상과 데이터

| 대상 | 공식 계열 | Target-Specific X | 최대 PIT 이력 시작 |
|---|---|---|---|
| 철·강 스크랩 (Iron & Steel Scrap) | `WPU1012` | `WPU1017` + `WPU0542` | 2009-12 |
| 철광석 (Iron Ore) | `WPU1011` | `WPU1017` + `WPU0542` | 2011-05 |
| 원유 (Crude Petroleum) | `WPU0561` | `WPU0571` + `WPU0542` | 2009-11 |

모든 계열은 **U.S. Bureau of Labor Statistics** PPI Detailed Report 의 동일 간행물에서 추출합니다 — 같은 발표 일정·같은 `known_at` 규칙이므로 상품 간 비교에서 데이터 불공정이 구조적으로 발생하지 않습니다.

- 유료 데이터: **0건**
- 사용 기관: U.S. Bureau of Labor Statistics · Office of the Federal Register (NARA)
- Copper Base Scrap 은 V11 Primary 에서 제외 — 사유는 성능이 아니라 **공통 이력 병목**입니다(빼면 공통 학습 시작이 2014-09 → 2011-05, **+40개월**). V10 아카이브로 보존됩니다.

## 6. Historical Evaluation

- **50개월 multi-year out-of-sample evaluation window** (2021-11-30 ~ 2025-12-31)
- matched historical support: 공통 학습 시작 **2011-05**
- maximum-history 조건에서도 동일한 방향으로 재현 (43.6261% · 35.9501% · 15.7593%)
- 통계 단위는 **대상월**입니다. 다섯 시점을 독립 표본으로 취급하지 않습니다.

### 시점별 오차 (matched · M1)

| 상품 | W0 | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|
| 스크랩 | 47.25 | 47.25 | 29.06 | 25.72 | 25.79 |
| 철광석 | 5.46 | 5.46 | 4.00 | 3.60 | 3.49 |
| 원유 | 22.33 | 22.33 | 19.54 | 17.85 | 17.81 |

W0 과 W1 의 오차가 **정확히 같습니다** — 그 사이에 새 공식 발표가 없기 때문이며, 구현이 실제 정보 도착을 따르고 있다는 직접 증거입니다.

## 7. Event Study — 무엇이 작동하지 않았나

공식 관보(Federal Register) 기록을 대규모로 확장하고, 다시 경제적으로 좁혔습니다.

```text
  공식 문서 11,293건  →  사안(Episode) 3,124개  →  Material Event 53건
```

네 조건을 **모두** 만족해야 Material Event 로 인정합니다 — 전달 경로 · 새 정보 · 확실성 · 경제적 폭. 그럼에도 증분 예측 가치는 나타나지 않았고, 사전 동결한 중단 규칙 8조건 중 1개만 통과했습니다.

> **Event 는 이제 예측 동력이 아니라 설명·진단·리스크 맥락 층으로 다룹니다.** 
> 이 결론은 검증된 공식 Event 프레임워크·대상·기간에 한정되며 일반화하지 않습니다.

## 8. Streamlit 연구 데모

대화형 **연구 데모**입니다. 실시간 가격 시스템이나 구매 의사결정 엔진이 아닙니다.

| 페이지 | 내용 |
|---|---|
| 개요 | 현재 가장 강한 결론과 대표 그림 |
| Rolling Nowcast | **50개월 OOS 예측 대 실제 시계열** · 대상월별 W0→W4 궤적 · 주별 정보 도착표 |
| 리서치 분석 | 상품 비교 · 예측 수렴 · 정보 기여 · Event 진단 |
| 데이터 & 방법 | target universe · true-PIT 규약 · 데이터 권리 · prospective 상태 · Agent Team |
| 연구 여정 | V1 → V11 세대별 기록 (실패한 결과까지 보존) |

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 9. 재현성 · 데이터 거버넌스

- **동결 선행**: 방법론을 성능보다 먼저 커밋하고, 동결 커밋에 성능 산출물이 없음을 테스트가 `git ls-tree` 로 강제합니다.
- **true known_at**: 발표일을 원문 릴리스 캘린더에서 읽고, 확인하지 못한 회차는 **추정하지 않고 폐기**합니다. 현재 개정값으로 과거를 채우지 않습니다.
- **matched-history 비교**: 상품 간 학습 지지를 통제하고 잔여 불균형을 명시합니다.
- **결정적 산출물**: 모든 표·그림이 정본 CSV/JSON 에서 재생성됩니다.
- **권리 매니페스트**: PASS 소스만 사용하고 REVIEW 는 REJECT 와 동일하게 취급합니다.
- **자동 테스트**로 위 규율을 강제합니다.

## 10. Prospective Validation

V11 동결 이후, **실제 결과가 공개되기 전에** 예측을 잠그는 전향적 검증을 수집합니다.

- 대상월이 끝난 뒤, 그 달의 공식 지수가 **발표되기 전에** 1회 실행
- 동결된 known_at 논리로 W0~W4 vintage 를 재구성
- 해시 + Git 커밋으로 불변 잠금
- 실제값이 공개되면 **별도 산출물**로 평가 (잠긴 예측은 절대 수정하지 않음)

정확한 지위: **pre-outcome locked prospective monthly evaluation with PIT-reconstructed weekly vintages**. 도구는 한 달에 한 번 돌고, 주간 vintage 는 그 시점 정보로 재구성한 것입니다 — 매주 실시간으로 도는 운영 시스템이 아닙니다.

| 현재 상태 | 값 |
|---|---|
| 잠긴 달 | 0 |
| 채점된 달 | 0 |
| 첫 예정 잠금 | 2026-09-02 (대상월 2026-08) |
| 결과 등급 | Tier D — 과거 창 통계에 섞지 않음 |

아직 잠긴 달이 없다는 것은 결측이 아니라 **상태**입니다. 전향 관측은 소급해서 만들 수 없고, 시간이 지나야 쌓입니다. 누적되는 동안에는 과거 창(Tier A)이 주 증거로 남습니다.

## 11. 연구 여정 (V1 → V11)

| 세대 | 버전 | 핵심 |
|---|---|---|
| 1세대 | V1~V4 | Event 표현·스케일링·아키텍처 진단 |
| 2세대 | V5~V8 | 예측 역할·위험·충격 구제·독립 경로 — 모두 음의 결과 |
| 3세대 | V9 | 더 긴 true-PIT 이력 → **첫 유의한 개선** |
| 4세대 | V10 | Event 이력 11,293건 확장 · 교차 상품 · 주간 nowcast |
| 5세대 | V11 | Release-Aware Nowcasting · Sparse Material Event · Event 중단 |

**부정적 결과를 지우지 않았습니다.** 각 세대의 실패가 다음 세대를 만든 근거입니다. 
자세한 기록은 데모의 *연구 여정* 페이지와 `docs/findings_v*.md` 에 있습니다.

## 12. 연구의 한계

1. 주 historical evaluation 은 **50개의 월별 out-of-sample origin** 으로 구성된 multi-year window 입니다. 전체 주효과를 평가하기에 의미 있는 길이지만, **동일한 historical period 가 V5~V11 연구 iteration 에서 반복 관찰**되었습니다.
2. 따라서 완전히 untouched 한 external holdout 으로 해석하지 않습니다.
3. 이를 보완하기 위해 **prospective 사전 잠금 검증**을 누적하고 있으며, 초기 prospective n 은 작습니다.
4. 급변·Event 활성 구간 등 **하위집단 분석은 실제로 small-n** 일 수 있습니다.
5. 예측 대상은 공식 가격지수/대리지표이며 모든 물리적 현물·거래 가격이 아닙니다.
6. 큰 rolling 이득은 **전월 공식 지수의 발표 시점 구조**와 강하게 결부돼 있습니다. 다른 발표 구조를 가진 자료로의 일반화는 별도 검증이 필요합니다.
7. Event 결론은 검증된 공식 Event 프레임워크·대상·기간에 한정됩니다.
8. 일부 분석(하위집단·진단)은 **탐색적**이며, 확증 근거로 쓰지 않습니다. 확증에 쓰는 것은 성능을 보기 전에 **사전등록**된 설계뿐입니다.

### 연구 지위 표기

- **사전등록(freeze-before-performance)**: target·X·이력창·단계·Event 규칙·지표·추론을 성능 수치가 존재하기 전에 커밋했고, 동결 커밋에 결과가 없음을 테스트가 git 으로 강제합니다.
- **탐색적 분석**은 그렇게 표시하고 주장 근거로 승격하지 않습니다.
- **Material Event 층은 예측을 개선하지 못했습니다.** 여덟 번의 서로 다른 시도 끝에 나온 결과이며, 숨기지 않고 그대로 보고합니다.

## 13. 저장소 구성

```text
├─ streamlit_app.py      연구 데모 인터페이스
├─ data/                 공개 안전 파생 산출물 (CSV / JSON)
├─ assets/               프로젝트가 직접 만든 그림
├─ docs/                 방법론 요약 · 세대별 findings · 배포 감사
├─ requirements.txt
├─ CITATION.cff
└─ COPYRIGHT_NOTICE.md
```

이 공개 저장소는 **큐레이션된 연구 데모/포트폴리오 표면**입니다. 전체 연구 기록(동결본·진단·원고 준비 자료·전향 검증 아카이브)은 **별도의 비공개 연구 저장소**에서 관리하며, 공개 산출물은 허용 목록 기반 export 로만 나옵니다.

## 14. 프로젝트 현황

| | |
|---|---|
| 연구 단계 | **V11 완료** — Release-Aware Nowcasting 이 현재 중심 framing |
| Event 연구 | 사전 동결한 중단 규칙에 따라 **예측 재설계 종료** |
| 논문 준비 | paper-ready consolidation 진행 — 재현 가능한 그림/표·claim-evidence 정리 |
| Prospective | 2026-09 부터 사전 잠금 수집 시작 |
| 원고 | **미제출** — 충분한 전향 검증과 최종 검토 후 계획 |

게재·심사 통과 사실은 없습니다. 향후 논문화 시 DOI 가 생기면 그때 추가합니다.

## 인용

이 저장소의 원본 분석·그림·실증 결과를 인용할 때는 `CITATION.cff` 를 참고해 저장소를 인용해 주십시오.

---

### Copyright & Use

© 2026 Repository author. All rights reserved, except for third-party or public-domain materials identified in this repository.

This repository is made publicly viewable for research transparency, portfolio review, and academic evaluation. Public availability does not, by itself, grant permission to copy, redistribute, republish, modify, commercialize, or present the repository's original code, documentation, figures, or research presentation as another person's work.

Academic citation and linking are welcome. For reuse of substantial original materials beyond applicable legal exceptions, please obtain prior permission.

Official source data and third-party materials remain subject to their respective licenses, terms, or public-domain status — including U.S. Bureau of Labor Statistics and Federal Register materials, which are U.S. Government works. See `COPYRIGHT_NOTICE.md`.

<sub>생성: 2026-08-29 · 이 README 의 모든 수치는 정본 산출물에서 자동 생성됩니다.</sub>
