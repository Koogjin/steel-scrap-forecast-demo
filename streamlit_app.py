"""미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo — presentation layer.

이 앱은 **저장된 결과만 읽는다.** 연구 파이프라인을 다시 돌리지 않는다:
원문 데이터를 내려받지 않고, PIT 패널을 재구성하지 않고, 사건을 수집하지 않고,
모델을 학습하지 않고, 외부 API 를 호출하지 않는다.

따라서 연구용 노트북을 모두 꺼도 이 대시보드는 계속 동작한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
ASSETS = Path(__file__).parent / "assets"

COLORS = {"actual": "#111827", "N0": "#9CA3AF", "M0": "#2563EB",
          "M1": "#059669", "M2": "#D97706"}
STAGE_LABEL = {"N0": "N0 · 단순 기준선", "M0": "M0 · 과거 PPI 정보",
               "M1": "M1 · + 시장/산업 데이터", "M2": "M2 · + 공식 사건 압력"}

st.set_page_config(page_title="철·강 스크랩 PPI 예측 Demo",
                   page_icon="🏭", layout="wide")


@st.cache_data
def load():
    d = {}
    d["official_metrics"] = pd.read_csv(DATA / "metrics.csv")
    d["official_preds"] = pd.read_csv(DATA / "predictions.csv")
    d["v2_metrics"] = pd.read_csv(DATA / "demo_v2_metrics.csv")
    d["v2_preds"] = pd.read_csv(DATA / "demo_v2_predictions.csv")
    d["v2_selected"] = pd.read_csv(DATA / "demo_v2_selected_models.csv")
    d["events"] = pd.read_csv(DATA / "event_registry_v2.csv")
    d["pressure"] = pd.read_csv(DATA / "pep_nep_v2.csv")
    d["meta"] = json.loads((DATA / "run_metadata.json").read_text(encoding="utf-8"))
    return d


D = load()
meta = D["meta"]
tgt = meta["target"]

# ---------------------------------------------------------------------------
# 헤더
# ---------------------------------------------------------------------------
st.title("미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo")
st.markdown(
    f"#### Target: **BLS {tgt['series_id']}** — {tgt['name_en']}\n"
    "*U.S. Iron & Steel Scrap Producer Price Index Forecasting*"
)
st.markdown(
    "> **각 과거 시점에 실제로 공개되어 있던 정보만 사용해서 예측했습니다.**"
)

k = meta["kpi"]
c = st.columns(7)
c[0].metric("예측 대상", tgt["series_id"])
c[1].metric("Clean-PIT 지표", f"{k['clean_pit_ready_x']}개")
c[2].metric("예측 시점", f"{k['n_origins']}개")
c[3].metric("공식 사건·상태", f"{k['n_event_records']}건")
c[4].metric("자동 테스트", f"{k['n_tests']}개")
c[5].metric("FRED 의존", f"{k['fred_dependency']}")
c[6].metric("동일 Train/Test", "YES")

st.info(
    "🎯 **예측 대상** — 실제 $/ton 거래가격이 아니라 **BLS 공식 생산자물가지수(PPI)** 입니다."
)

tabs = st.tabs(["📌 요약", "🎯 예측 대상 설명", "📊 성능 비교", "📈 예측 추이",
                "🌍 공식 사건 압력", "🤖 모델 벤치마크", "🔬 Clean-PIT 란",
                "🧠 Agent Team 활용"])

# ---------------------------------------------------------------------------
# 요약
# ---------------------------------------------------------------------------
with tabs[0]:
    st.subheader("경영진 요약")
    st.markdown(meta["executive_summary_md"])
    st.divider()
    st.subheader("3단계 모델 구조")
    p = ASSETS / "model_stages.png"
    if p.exists():
        st.image(str(p), width="stretch")
    st.success(
        "✅ **Demo V2 의 모든 비교는 동일한 Train/Test 기준입니다** — "
        f"같은 예측 시점 {k['n_origins']}개, 같은 학습 행, 같은 대상 월, 같은 지표."
    )

# ---------------------------------------------------------------------------
# 예측 대상 설명
# ---------------------------------------------------------------------------
with tabs[1]:
    st.subheader("이 Demo가 예측하는 것은 무엇인가?")
    a, b = st.columns(2)
    with a:
        st.markdown("#### 📘 이 지수는 무엇인가?")
        st.markdown(
            f"**BLS {tgt['series_id']}** — *{tgt['name_en']}*\n\n"
            "미국 노동통계국(BLS)이 발표하는 **철·강 스크랩 제품군의 "
            "생산자물가지수(PPI)** 입니다.\n\n"
            f"BLS 상품코드 `{tgt['bls_commodity_code']}` · 월간 · "
            f"{'비계절조정 지수' if tgt['seasonal_adjustment'] == 'NSA' else ''}\n\n"
            "기준시점을 100으로 두고 그 이후의 **상대적인 가격 변화**를 측정합니다."
        )
        st.markdown("#### 📈 지수가 오르면?")
        st.markdown(
            "철·강 스크랩 제품군에 대해 **생산자들이 받는 가격 수준이 "
            "기준시점 대비 상승**하는 방향입니다."
        )
    with b:
        st.markdown("#### 📉 지수가 내리면?")
        st.markdown(
            "해당 제품군의 **생산자 가격 수준이 기준시점 대비 하락**하는 방향입니다."
        )
        st.markdown("#### ⛔ 무엇이 아닌가?")
        st.markdown(
            "- 특정 기업의 **구매가격**이 아닙니다\n"
            "- 특정 스크랩 grade 의 **거래가격**이 아닙니다\n"
            "- **$/ton 현물가격**이 아닙니다\n\n"
            "지수 값과 달러 금액을 같게 해석하면 안 됩니다 — "
            "예를 들어 지수 600은 톤당 600달러라는 뜻이 **아닙니다**."
        )
    st.warning(
        "본 Demo는 특정 기업의 구매가격, 특정 스크랩 grade 의 거래가격, "
        "또는 $/ton 현물가격을 예측하는 모델이 **아닙니다**."
    )
    st.caption(
        "월별 변화는 지수 포인트 차이보다 **percent change** 로 읽는 것이 "
        "경제적으로 더 자연스럽습니다(BLS 설명 기준)."
    )

# ---------------------------------------------------------------------------
# 성능 비교
# ---------------------------------------------------------------------------
with tabs[2]:
    st.subheader("모델 성능 비교")
    st.markdown(
        "**M0/M1은 기존 사전등록 실험 결과이며, M2는 공식 사건 정보를 추가한 "
        "탐색적 확장 Demo입니다.** Demo V2에서는 M0/M1/M2를 **동일한 Train/Test "
        "조건**에서 추가 비교합니다."
    )

    view = st.radio(
        "비교 방식",
        ["A. 통제 비교 — 알고리즘을 Ridge로 고정하고 정보만 추가",
         "B. Best-CV 벤치마크 — 학습 데이터 안에서만 모델 선택"],
        index=0)
    view_key = "CONTROLLED_RIDGE" if view.startswith("A") else "BEST_CV_MULTIMODEL"

    vm = D["v2_metrics"]
    sub = vm[vm["view"] == view_key].copy()
    base = float(sub.loc[sub["stage"] == "M0", "mae"].iloc[0])
    sub["상대 개선(vs M0)"] = (1 - sub["mae"] / base).map(lambda v: f"{v:+.1%}")
    sub["단계"] = sub["stage"].map(STAGE_LABEL)
    n0row = vm[vm["view"] == "BASELINE"]

    left, right = st.columns([3, 2])
    with left:
        fig = go.Figure()
        if not n0row.empty:
            fig.add_bar(x=["N0 · 기준선"], y=[float(n0row["mae"].iloc[0])],
                        marker_color=COLORS["N0"], showlegend=False,
                        text=[f"{float(n0row['mae'].iloc[0]):.1f}"],
                        textposition="outside")
        for _, r in sub.iterrows():
            fig.add_bar(x=[STAGE_LABEL[r["stage"]]], y=[r["mae"]],
                        marker_color=COLORS[r["stage"]], showlegend=False,
                        text=[f"{r['mae']:.1f}"], textposition="outside")
        fig.update_layout(title=f"MAE (낮을수록 정확) — {view.split('.')[0]} view",
                          height=380, yaxis_title="MAE (지수 포인트)",
                          margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")
    with right:
        st.dataframe(
            sub[["단계", "mae", "rmse", "상대 개선(vs M0)"]]
            .rename(columns={"mae": "MAE", "rmse": "RMSE"})
            .style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}"}),
            hide_index=True, width="stretch")
        st.caption(
            f"동일 조건: 예측 시점 {k['n_origins']}개 · 학습행 "
            f"{meta['common_support']['train_rows_min']}~"
            f"{meta['common_support']['train_rows_max']} · 세 단계 모두 동일")

    st.caption("M2는 향후 사건 정의와 장기 이력 보강 후 정식 연구 검증 예정입니다.")

    st.divider()
    with st.expander("기존 사전등록 결과 (원본 보존)"):
        st.markdown(
            "아래는 **결과를 보기 전에 규칙을 고정한** 사전등록 실험의 원본 결과입니다. "
            "Demo V2는 이 결과를 대체하지 않습니다."
        )
        om = D["official_metrics"]
        st.dataframe(
            om[om["target_id"] == tgt["series_id"]][
                ["model", "n_origins", "mae", "rmse", "status"]]
            .rename(columns={"model": "모델", "n_origins": "시점 수",
                             "mae": "MAE", "rmse": "RMSE", "status": "지위"})
            .style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}"}),
            hide_index=True, width="stretch")
        pi = meta["primary_inference"]
        st.markdown(
            f"사전등록된 주요 가설(M0 vs M1): 상대 개선 **{pi['skill']:+.1%}**, "
            f"DM 검정 p = **{pi['dm_p']:.3f}**, 95% 신뢰구간 "
            f"[{pi['ci_low']:.1f}, {pi['ci_high']:.1f}] — 개선 증거 없음."
        )

# ---------------------------------------------------------------------------
# 예측 추이
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("실제값 vs 예측값")
    d = D["v2_preds"].copy()
    d["month"] = pd.to_datetime(d["target_month"] + "-01")
    prefix = "ridge" if st.radio(
        "비교 방식", ["A. 통제 비교 (Ridge 고정)", "B. Best-CV 벤치마크"],
        index=0, key="fc_view").startswith("A") else "bestcv"

    picks = st.multiselect("표시할 모델", ["N0", "M0", "M1", "M2"],
                           default=["M0", "M1", "M2"],
                           format_func=lambda m: STAGE_LABEL[m])
    fig = go.Figure()
    fig.add_scatter(x=d["month"], y=d["y_true"], name="실제 지수",
                    line=dict(color=COLORS["actual"], width=3))
    for m in picks:
        col = "N0" if m == "N0" else f"{prefix}_{m}"
        if col in d.columns:
            fig.add_scatter(x=d["month"], y=d[col], name=STAGE_LABEL[m],
                            line=dict(color=COLORS[m], width=2,
                                      dash="dot" if m == "M2" else None))
    fig.update_layout(height=460, yaxis_title="PPI 지수 (기준시점=100)",
                      xaxis_title="대상 월", hovermode="x unified",
                      margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"{len(d)}개 시점 · {d['month'].min():%Y-%m} ~ {d['month'].max():%Y-%m} · "
        "각 시점에서 그 당시 알 수 있던 정보만으로 다음 달을 예측했습니다.")

# ---------------------------------------------------------------------------
# 공식 사건 압력
# ---------------------------------------------------------------------------
with tabs[4]:
    st.subheader("공식 사건 기반 압력 지표 (PEP / NEP)")
    st.markdown(
        "**뉴스기사 원문 대신 공식적으로 확인된 사건·상태를 구조화하여 두 개의 "
        "압력 변수로 변환했습니다.**\n\n"
        "- **PEP** — 스크랩 가격 **상승** 압력 증거\n"
        "- **NEP** — 스크랩 가격 **하락** 압력 증거\n\n"
        "긍/부정 뉴스 감성이 아니며 두 지표는 **독립**입니다. 관세처럼 상승·하락 "
        "채널을 동시에 갖는 사건은 두 값이 함께 올라갑니다."
    )

    ec = meta["event_coverage"]
    q = st.columns(5)
    q[0].metric("사건·상태 기록", f"{ec['records']}건")
    q[1].metric("이력 시작", ec["first_month"])
    q[2].metric("PEP 활성 월", f"{ec['pep_nonzero_pct']:.0f}%")
    q[3].metric("NEP 활성 월", f"{ec['nep_nonzero_pct']:.0f}%")
    q[4].metric("공식 출처", f"{ec['n_sources']}곳")

    pp = D["pressure"].copy()
    pp["month_dt"] = pd.to_datetime(pp["month"] + "-01")
    lo = pd.Timestamp(meta["common_support"]["first_train_month"] + "-01")
    pp = pp[pp["month_dt"] >= lo]

    fig = go.Figure()
    fig.add_scatter(x=pp["month_dt"], y=pp["PEP"], name="PEP (상승 압력)",
                    line=dict(color="#DC2626", width=2), fill="tozeroy")
    fig.add_scatter(x=pp["month_dt"], y=pp["NEP"], name="NEP (하락 압력)",
                    line=dict(color="#2563EB", width=2))
    ev = D["events"]
    for _, e in ev[ev["kind"] == "POINT"].iterrows():
        km = pd.Timestamp(str(e["known_at_date"]))
        if km >= pp["month_dt"].min():
            fig.add_vline(x=km, line=dict(color="#6B7280", width=1, dash="dot"))
    fig.update_layout(height=380, yaxis_title="압력 (0~1)", xaxis_title="월",
                      hovermode="x unified", yaxis_range=[0, 1],
                      margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("● 점선 = 단발성 발표(POINT) · 면적/선 = 지속 상태(ONGOING)를 포함한 월별 압력")

    st.markdown("#### 사건·상태 목록 (전부 공식 출처)")
    kinds = st.multiselect("유형", ["ONGOING", "POINT"],
                           default=["ONGOING", "POINT"])
    for _, e in ev[ev["kind"].isin(kinds)].sort_values("known_at_date").iterrows():
        mark = "━━" if e["kind"] == "ONGOING" else "●"
        with st.expander(f"{mark}  {e['known_at_date']} · {e['event_name']}"):
            g = st.columns(4)
            g[0].markdown(f"**유형**\n\n`{e['kind']}`")
            g[1].markdown(f"**단계**\n\n`{e['stage']}`")
            g[2].markdown(f"**분류**\n\n`{e['category']}`")
            g[3].markdown(f"**상승/하락 점수**\n\n"
                          f"`{e['upward_pressure_score']} / "
                          f"{e['downward_pressure_score']}`")
            st.markdown(f"**경제적 경로** — {e['economic_channel']}")
            st.markdown(f"**요약** — {e['short_summary']}")
            st.markdown(f"**공식 출처** — [{e['official_source_name']}]"
                        f"({e['official_source_url']})")

# ---------------------------------------------------------------------------
# 모델 벤치마크
# ---------------------------------------------------------------------------
with tabs[5]:
    st.subheader("모델 벤치마크 — 학습 데이터 안에서만 선택")
    st.info(
        "**최종 Test 성능을 보고 모델을 고른 것이 아니라, 각 예측시점의 과거 "
        "학습데이터 내부에서만 모델을 선택했습니다.**"
    )
    st.markdown(
        f"후보 모델: {', '.join(meta['models']['candidate_families'])} — "
        f"총 {meta['models']['n_candidate_configs']}개 설정. "
        "M0/M1/M2에 **동일한 후보군과 동일한 CV 예산**을 적용했습니다."
    )

    vm = D["v2_metrics"]
    a, b = st.columns(2)
    with a:
        st.markdown("##### 단계별 MAE")
        cmp_df = vm[vm["view"].isin(["CONTROLLED_RIDGE", "BEST_CV_MULTIMODEL"])].copy()
        cmp_df["비교 방식"] = cmp_df["view"].map(
            {"CONTROLLED_RIDGE": "A. Ridge 고정", "BEST_CV_MULTIMODEL": "B. Best-CV"})
        fig = go.Figure()
        for label, grp in cmp_df.groupby("비교 방식"):
            fig.add_bar(x=grp["stage"], y=grp["mae"], name=label,
                        text=grp["mae"].map(lambda v: f"{v:.1f}"),
                        textposition="outside")
        fig.update_layout(barmode="group", height=360, yaxis_title="MAE",
                          margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")
    with b:
        st.markdown("##### 선택된 모델 분포 (Best-CV)")
        sel = D["v2_selected"]
        counts = (sel.groupby(["stage", "selected_family"]).size()
                  .reset_index(name="선택 횟수"))
        fig = go.Figure()
        for fam, grp in counts.groupby("selected_family"):
            fig.add_bar(x=grp["stage"], y=grp["선택 횟수"], name=fam)
        fig.update_layout(barmode="stack", height=360,
                          yaxis_title="선택된 예측시점 수",
                          margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")

    st.dataframe(
        counts.pivot(index="selected_family", columns="stage",
                     values="선택 횟수").fillna(0).astype(int),
        width="stretch")
    st.caption(
        "개별 모델의 전체 Test 순위는 참고용 기술 통계입니다. 정당한 '최적' 결과는 "
        "위의 **학습 내부 선택(Best-CV)** 결과입니다.")

# ---------------------------------------------------------------------------
# Clean-PIT
# ---------------------------------------------------------------------------
with tabs[6]:
    st.subheader("왜 Clean-PIT 인가")
    a, b = st.columns(2)
    with a:
        st.markdown("#### ⚠️ 기존 방식의 위험")
        st.markdown(
            "과거를 모델링할 때 **현재 최종 수정된 과거 데이터**를 쓰면, "
            "그 시점에는 알 수 없었던 정보가 모델에 들어갑니다.\n\n"
            "경제지표는 최초 발표 후 여러 차례 개정됩니다.")
    with b:
        st.markdown("#### ✅ 본 프로젝트의 방식")
        st.markdown(
            f"**2023년 시점을 예측할 때 2026년에 수정된 최종 {tgt['series_id']} 값을 "
            "쓰는 것이 아니라, 당시 실제로 공개되어 있던 값만 사용합니다.**\n\n"
            "BLS · Federal Reserve 의 당시 historical release 를 직접 재구성했습니다.")
    st.divider()
    st.markdown("#### 실제로 개정이 일어난다는 증거")
    st.dataframe(pd.DataFrame(meta["revision_examples"]), hide_index=True,
                 width="stretch")

# ---------------------------------------------------------------------------
# Agent Team
# ---------------------------------------------------------------------------
with tabs[7]:
    st.subheader("Claude Code Agent Team 활용")
    p = ASSETS / "claude_code_workflow.png"
    if p.exists():
        st.image(str(p), width="stretch")
    st.markdown(meta["claude_code_md"])

st.divider()
st.caption(
    f"공식 실행 커밋 `{meta['git_commit'][:12]}` · "
    f"사전등록 해시 `{meta['preregistration_sha256'][:12]}` · "
    f"동결 데이터 해시 `{meta['freeze_manifest_sha256'][:12]}` · "
    f"생성 {meta['exported_at']}"
)
