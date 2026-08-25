"""미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo — presentation layer (V3).

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
          "M1": "#059669", "M2": "#D97706", "M2_V2": "#D97706",
          "M2_V3": "#BE185D"}
STAGE_LABEL = {
    "N0": "N0 · 단순 기준선",
    "M0": "M0 · 과거 PPI 정보",
    "M1": "M1 · + 시장/산업 데이터",
    "M2": "M2 · + 공식 사건 압력",
    "M2_V2": "M2-V2 · 사건 압력 (V2 정의)",
    "M2_V3": "M2-V3 · 사건 압력 (V3 정의)",
}
UP_COLOR, DOWN_COLOR = "#DC2626", "#2563EB"

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
    d["events_v2"] = pd.read_csv(DATA / "event_registry_v2.csv")
    d["pressure_v2"] = pd.read_csv(DATA / "pep_nep_v2.csv")
    d["v3_metrics"] = pd.read_csv(DATA / "demo_v3_metrics.csv")
    d["v3_preds"] = pd.read_csv(DATA / "demo_v3_predictions.csv")
    d["v3_selected"] = pd.read_csv(DATA / "demo_v3_selected_models.csv")
    d["episodes"] = pd.read_csv(DATA / "event_episode_registry_v3.csv")
    d["transitions"] = pd.read_csv(DATA / "event_transition_registry_v3.csv")
    d["pressure_v3"] = pd.read_csv(DATA / "pep_nep_v3.csv")
    d["cat_state"] = pd.read_csv(DATA / "event_monthly_category_state_v3.csv")
    d["contrib"] = pd.read_csv(DATA / "event_contribution_v3.csv")
    d["meta"] = json.loads((DATA / "run_metadata.json").read_text(encoding="utf-8"))
    return d


D = load()
meta = D["meta"]
tgt = meta["target"]
k = meta["kpi"]
v3 = meta["demo_v3"]

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

c = st.columns(7)
c[0].metric("예측 대상", tgt["series_id"])
c[1].metric("Clean-PIT 지표", f"{k['clean_pit_ready_x']}개")
c[2].metric("예측 시점", f"{k['n_origins']}개")
c[3].metric("공식 사건", f"{v3['n_episodes']}건 / {v3['n_transitions']}상태")
c[4].metric("자동 테스트", f"{k['n_tests']}개")
c[5].metric("FRED 의존", f"{k['fred_dependency']}")
c[6].metric("동일 Train/Test", "YES")

st.info(
    "🎯 **예측 대상** — 실제 $/ton 거래가격이 아니라 **BLS 공식 생산자물가지수(PPI)** 입니다. "
    "지수 600은 톤당 600달러라는 뜻이 아닙니다."
)

tabs = st.tabs(["📌 요약", "🎯 무엇을 예측하나", "📊 성능 비교", "📈 예측 추이",
                "🌍 사건 압력 (V3)", "🔍 사건 기여 진단", "🤖 모델 벤치마크",
                "🔬 Clean-PIT 란", "🧠 Agent Team 활용"])

# ---------------------------------------------------------------------------
# 0. 요약
# ---------------------------------------------------------------------------
with tabs[0]:
    st.subheader("경영진 요약")
    st.markdown(meta["executive_summary_md"])
    st.divider()
    st.subheader("모델 단계 구조")
    p = ASSETS / "model_stages.png"
    if p.exists():
        st.image(str(p), width="stretch")
    st.success(
        "✅ **모든 비교는 동일한 Train/Test 기준입니다** — "
        f"같은 예측 시점 {k['n_origins']}개, 같은 학습 행, 같은 대상 월, 같은 지표. "
        "M2-V2 와 M2-V3 는 **피처 개수도 2개로 같습니다** — 차이는 오직 정의입니다."
    )

# ---------------------------------------------------------------------------
# 1. 무엇을 예측하나 (§PART A — 훨씬 쉬운 설명)
# ---------------------------------------------------------------------------
with tabs[1]:
    st.subheader("무엇을 예측하나")
    st.markdown(meta["target_explainer_md"])
    st.divider()
    st.markdown("#### 실제 지수는 이렇게 움직였습니다")
    d = D["v3_preds"].copy()
    d["month"] = pd.to_datetime(d["target_month"] + "-01")
    fig = go.Figure()
    fig.add_scatter(x=d["month"], y=d["y_true"], name="실제 지수",
                    line=dict(color=COLORS["actual"], width=3), fill="tozeroy",
                    fillcolor="rgba(17,24,39,0.06)")
    fig.update_layout(height=320, yaxis_title="PPI 지수 (1982-06 = 100)",
                      xaxis_title="월", hovermode="x unified",
                      margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    lo, hi = float(d["y_true"].min()), float(d["y_true"].max())
    st.caption(
        f"이 구간에서 지수는 **{lo:.0f} ~ {hi:.0f}** 사이를 움직였습니다. "
        f"{lo:.0f} 에서 {hi:.0f} 로 가는 것은 **{(hi / lo - 1):+.0%}** 변화입니다 — "
        "지수 차이는 항상 이렇게 **변화율**로 읽습니다."
    )
    st.warning(
        "본 Demo는 특정 기업의 구매가격, 특정 스크랩 grade 의 거래가격, "
        "또는 $/ton 현물가격을 예측하는 모델이 **아닙니다**."
    )

# ---------------------------------------------------------------------------
# 2. 성능 비교
# ---------------------------------------------------------------------------
with tabs[2]:
    st.subheader("모델 성능 비교")
    st.markdown(
        "**M0/M1 은 기존 사전등록 실험의 단계이며, M2 는 공식 사건 정보를 추가한 "
        "탐색적 확장입니다.** Demo V3 에서는 M2 를 두 가지 정의(V2 / V3)로 나누어 "
        "**동일한 Train/Test 조건**에서 비교합니다."
    )

    view = st.radio(
        "비교 방식",
        ["A. 통제 비교 — 알고리즘을 Ridge 로 고정하고 정보만 추가",
         "B. Best-CV 벤치마크 — 학습 데이터 안에서만 모델 선택"],
        index=0)
    view_key = "CONTROLLED_RIDGE" if view.startswith("A") else "BEST_CV_MULTIMODEL"

    vm = D["v3_metrics"]
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
                          height=400, yaxis_title="MAE (지수 포인트)",
                          margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")
    with right:
        st.dataframe(
            sub[["단계", "mae", "rmse", "상대 개선(vs M0)"]]
            .rename(columns={"mae": "MAE", "rmse": "RMSE"})
            .style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}"}),
            hide_index=True, width="stretch")
        cs = meta["common_support"]
        st.caption(
            f"동일 조건: 예측 시점 {k['n_origins']}개 · 학습행 "
            f"{cs['train_rows_min']}~{cs['train_rows_max']} · 모든 단계 동일")
        st.caption(
            "M2-V2 와 M2-V3 는 **둘 다 피처 2개**입니다. 차이는 개수가 아니라 정의입니다.")

    st.markdown(meta["result_reading_md"])

    st.divider()
    with st.expander("기존 사전등록 결과 (원본 보존 · 수정하지 않음)"):
        st.markdown(
            "아래는 **결과를 보기 전에 규칙을 고정한** 사전등록 실험의 원본 결과입니다. "
            "Demo V2·V3 는 이 결과를 대체하지 않습니다."
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
    with st.expander("Demo V2 결과 (historical artifact · 수정하지 않음)"):
        v2m = D["v2_metrics"]
        st.dataframe(
            v2m[["view", "stage", "mae", "rmse", "smape",
                 "directional_accuracy"]]
            .rename(columns={"view": "비교 방식", "stage": "단계", "mae": "MAE",
                             "rmse": "RMSE", "smape": "sMAPE",
                             "directional_accuracy": "방향 정확도"})
            .style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}", "sMAPE": "{:.4f}",
                           "방향 정확도": "{:.3f}"}),
            hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# 3. 예측 추이
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("실제값 vs 예측값")
    d = D["v3_preds"].copy()
    d["month"] = pd.to_datetime(d["target_month"] + "-01")
    prefix = "ridge" if st.radio(
        "비교 방식", ["A. 통제 비교 (Ridge 고정)", "B. Best-CV 벤치마크"],
        index=0, key="fc_view").startswith("A") else "bestcv"

    available = [m for m in ("N0", "M0", "M1", "M2_V2", "M2_V3")
                 if m == "N0" or f"{prefix}_{m}" in d.columns]
    picks = st.multiselect("표시할 모델", available,
                           default=[m for m in ("M1", "M2_V3") if m in available],
                           format_func=lambda m: STAGE_LABEL[m])
    fig = go.Figure()
    fig.add_scatter(x=d["month"], y=d["y_true"], name="실제 지수",
                    line=dict(color=COLORS["actual"], width=3))
    for m in picks:
        col = "N0" if m == "N0" else f"{prefix}_{m}"
        if col in d.columns:
            fig.add_scatter(x=d["month"], y=d[col], name=STAGE_LABEL[m],
                            line=dict(color=COLORS[m], width=2,
                                      dash="dot" if m.startswith("M2") else None))
    fig.update_layout(height=460, yaxis_title="PPI 지수 (기준시점=100)",
                      xaxis_title="대상 월", hovermode="x unified",
                      margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"{len(d)}개 시점 · {d['month'].min():%Y-%m} ~ {d['month'].max():%Y-%m} · "
        "각 시점에서 그 당시 알 수 있던 정보만으로 다음 달을 예측했습니다.")

    if f"{prefix}_M2_V3" in d.columns and f"{prefix}_M1" in d.columns:
        st.markdown("#### 사건 압력이 예측을 얼마나 움직였나")
        fig = go.Figure()
        for m, name in (("M2_V2", "M2-V2 − M1"), ("M2_V3", "M2-V3 − M1")):
            col = f"{prefix}_{m}"
            if col in d.columns:
                fig.add_scatter(x=d["month"], y=d[col] - d[f"{prefix}_M1"],
                                name=name, line=dict(color=COLORS[m], width=2))
        fig.add_hline(y=0, line=dict(color="#9CA3AF", width=1))
        fig.update_layout(height=300, yaxis_title="M1 대비 차이 (지수 포인트)",
                          xaxis_title="대상 월", hovermode="x unified",
                          margin=dict(t=20, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "0 에 붙어 있을수록 '사건 정보를 넣어도 예측이 달라지지 않는다'는 뜻입니다. "
            "Demo V2 에서 M2 와 M1 이 거의 겹쳐 보였던 이유가 바로 이것입니다.")

# ---------------------------------------------------------------------------
# 4. 사건 압력 (V3)
# ---------------------------------------------------------------------------
with tabs[4]:
    st.subheader("공식 사건 기반 압력 지표 (PEP / NEP · V3)")
    st.markdown(
        "**뉴스기사 원문 대신 공식적으로 확인된 사건·상태를 구조화하여 두 개의 "
        "압력 변수로 변환했습니다.**\n\n"
        "- **PEP** — 스크랩 가격 **상승** 압력 증거\n"
        "- **NEP** — 스크랩 가격 **하락** 압력 증거\n\n"
        "긍/부정 뉴스 감성이 아니며 두 지표는 **독립**입니다. 관세처럼 상승·하락 "
        "채널을 동시에 갖는 사건은 두 값이 함께 올라갑니다."
    )

    q = st.columns(6)
    q[0].metric("사안(episode)", f"{v3['n_episodes']}건")
    q[1].metric("상태 변화(transition)", f"{v3['n_transitions']}건")
    q[2].metric("분류 수 K", v3["K"])
    q[3].metric("이력 시작", v3["first_known_at"])
    q[4].metric("PEP 값 종류", v3["coverage"]["pep_distinct"])
    q[5].metric("공식 출처 도메인", v3["n_source_hosts"])

    pp = D["pressure_v3"].copy()
    pp["month_dt"] = pd.to_datetime(pp["month"] + "-01")
    lo = pd.Timestamp(meta["common_support"]["first_train_month"] + "-01")
    pp = pp[pp["month_dt"] >= lo]

    fig = go.Figure()
    fig.add_scatter(x=pp["month_dt"], y=pp["PEP"], name="PEP (상승 압력)",
                    line=dict(color=UP_COLOR, width=2), fill="tozeroy",
                    fillcolor="rgba(220,38,38,0.10)")
    fig.add_scatter(x=pp["month_dt"], y=pp["NEP"], name="NEP (하락 압력)",
                    line=dict(color=DOWN_COLOR, width=2))
    fig.update_layout(height=380, yaxis_title="압력 (0~1)", xaxis_title="월",
                      hovermode="x unified", yaxis_range=[0, 1],
                      margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "새로 발생한 조치일수록 강하고, 오래 유지된 상태는 낮은 수준으로 가라앉습니다 — "
        "**이미 몇 년째 유지 중인 관세는 '압력'이 아니라 'baseline'** 이기 때문입니다.")

    with st.expander("V2 정의와 무엇이 달라졌나 (같은 기간, 같은 사건 원칙)"):
        p2 = D["pressure_v2"].copy()
        p2["month_dt"] = pd.to_datetime(p2["month"] + "-01")
        p2 = p2[p2["month_dt"] >= lo]
        fig = go.Figure()
        fig.add_scatter(x=p2["month_dt"], y=p2["PEP"], name="PEP (V2 정의)",
                        line=dict(color="#D97706", width=2, dash="dot"))
        fig.add_scatter(x=pp["month_dt"], y=pp["PEP"], name="PEP (V3 정의)",
                        line=dict(color=UP_COLOR, width=2))
        fig.update_layout(height=320, yaxis_title="압력 (0~1)", xaxis_title="월",
                          hovermode="x unified", yaxis_range=[0, 1],
                          margin=dict(t=20, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")
        st.markdown(
            f"V2 의 PEP 는 전체 예측 시점에서 **서로 다른 값이 "
            f"{meta['demo_v2_contrib']['pep_distinct']}개**뿐이었습니다. "
            f"거의 상수인 변수는 모델에 정보를 줄 수 없습니다. "
            f"V3 는 같은 구간에서 **{v3['coverage']['pep_distinct']}개**의 값을 갖습니다."
        )

    st.markdown("#### 분류별 압력")
    cs = D["cat_state"].copy()
    cs["month_dt"] = pd.to_datetime(cs["month"] + "-01")
    cs = cs[cs["month_dt"] >= lo]
    direction = st.radio("방향", ["상승 압력", "하락 압력"], index=0,
                         horizontal=True, key="cat_dir")
    col = "up" if direction == "상승 압력" else "down"
    fig = go.Figure()
    for label, grp in cs.groupby("category_label"):
        if grp[col].max() == 0:
            continue
        fig.add_scatter(x=grp["month_dt"], y=grp[col], name=label,
                        stackgroup=None, line=dict(width=1.6))
    fig.update_layout(height=360, yaxis_title=f"{direction} (0~1)",
                      xaxis_title="월", hovermode="x unified",
                      yaxis_range=[0, 1], margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    empty_cats = sorted(set(cs["category_label"]) -
                        set(cs[cs["up"] > 0]["category_label"]) -
                        set(cs[cs["down"] > 0]["category_label"]))
    if empty_cats:
        st.caption(
            f"기록이 없는 분류: {', '.join(empty_cats)} — 월을 채우려고 사건을 "
            "만들지 않았습니다. 집계 방식상 빈 분류는 다른 분류를 희석하지 않습니다.")

    st.markdown("#### 사안과 상태 변화 (전부 공식 출처)")
    eps = D["episodes"]
    trs = D["transitions"]
    cats = st.multiselect("분류", sorted(eps["category_label"].unique()),
                          default=sorted(eps["category_label"].unique()))
    for _, e in eps[eps["category_label"].isin(cats)].iterrows():
        mine = trs[trs["episode_id"] == e["episode_id"]].sort_values("known_at_date")
        head = (f"{e['episode_name']}  ·  {e['category_label']}  ·  "
                f"상태 변화 {len(mine)}건  ({e['first_known_at']} ~ "
                f"{e['last_known_at']})")
        with st.expander(head):
            g = st.columns(3)
            g[0].markdown(f"**직접성 (directness)**\n\n`{e['directness']} / 3`")
            g[1].markdown(f"**범위 (scope)**\n\n`{e['scope']} / 3`")
            g[2].markdown(f"**종료**\n\n`{e['end_date'] if isinstance(e['end_date'], str) and e['end_date'] else '진행 중'}`")
            st.markdown(f"**경제적 경로** — {e['economic_channel']}")
            st.markdown("**상태 변화 이력**")
            for _, t in mine.iterrows():
                st.markdown(
                    f"- `{t['known_at_date']}` **{t['stage']}** "
                    f"(확실성 {t['certainty']:.2f} · 기본강도 "
                    f"{t['base_strength']:.3f} · 상승 {t['direction_up']:.2f} / "
                    f"하락 {t['direction_down']:.2f})  \n"
                    f"  {t['short_summary']}  \n"
                    f"  [{t['official_source_name']}]({t['official_source_url']})")

    with st.expander("채점 규칙 — 결과를 보기 전에 고정했습니다"):
        st.markdown(meta["event_method_v3_md"])

# ---------------------------------------------------------------------------
# 5. 사건 기여 진단 (§PART B / H)
# ---------------------------------------------------------------------------
with tabs[5]:
    st.subheader("사건 정보가 모델에 실제로 어떻게 쓰였나")
    st.markdown(
        "Demo V2 에서 M1 과 M2 의 예측선이 거의 겹쳐 보였습니다. 원인을 추측하지 않고 "
        "**측정**했습니다. 가능한 원인은 셋이었습니다.\n\n"
        "- **A.** 압력 지표(PEP/NEP)가 거의 움직이지 않는다\n"
        "- **B.** 모델의 규제(regularization)가 계수를 0 근처로 눌러버린다\n"
        "- **C.** 둘 다"
    )

    dv2 = meta["demo_v2_contrib"]
    a, b = st.columns(2)
    a.metric("사실상 0 인 계수", f"{dv2['n_zero_coef']} / {dv2['n_coef_total']}",
             help="0 이면 모델이 사건 정보를 버린 것이 아니라는 뜻입니다.")
    b.metric("PEP 값 종류 (V2)", dv2["pep_distinct"],
             help="예측 시점 전체에서 서로 다른 값이 몇 개였는지.")
    st.error(
        f"**원인은 A 였습니다.** 계수가 0 인 경우는 "
        f"{dv2['n_zero_coef']}/{dv2['n_coef_total']} 건뿐이었습니다 — 모델은 사건 "
        f"정보를 버리지 않았습니다. 그런데 PEP 는 전체 예측 시점에서 서로 다른 값이 "
        f"**{dv2['pep_distinct']}개**뿐이었습니다. 모델이 신호를 무시한 것이 아니라 "
        f"**줄 신호가 없었습니다.**"
    )

    st.divider()
    st.markdown("#### V3 에서 달라진 것")
    cdf = D["contrib"]
    rows = []
    for stage in ("M2_V2", "M2_V3"):
        s = v3["contribution"][stage]
        rows.append({
            "단계": STAGE_LABEL[stage],
            "median |예측 − M1|": s["median_abs_delta_vs_M1"],
            "max |예측 − M1|": s["max_abs_delta_vs_M1"],
            "|차이| < 1 인 시점": f"{s['pct_delta_lt_1']:.0f}%",
            "median |계수|": s["median_abs_event_coefficient"],
            "PEP 값 종류": s["feature_1_live"]["n_distinct"],
            "NEP 값 종류": s["feature_2_live"]["n_distinct"],
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    st.markdown("#### 시점별 사건 기여분 (Ridge · 계수 × 압력값)")
    fig = go.Figure()
    for stage in ("M2_V2", "M2_V3"):
        g = cdf[cdf["stage"] == stage].copy()
        g["month"] = pd.to_datetime(g["target_month"] + "-01")
        fig.add_scatter(x=g["month"], y=g["direct_event_contribution"],
                        name=STAGE_LABEL[stage],
                        line=dict(color=COLORS[stage], width=2))
    fig.update_layout(height=340, yaxis_title="사건 기여분 (지수 포인트)",
                      xaxis_title="대상 월", hovermode="x unified",
                      margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "PEP/NEP 는 [0,1] 로 정의되어 표준화하지 않으므로, 계수는 "
        "'압력이 0 에서 1 로 갈 때 예측이 몇 지수 포인트 움직이는가'로 바로 읽힙니다.")

    st.markdown("#### 사건 정보를 껐다면 (counterfactual)")
    g = cdf[cdf["stage"] == "M2_V3"].copy()
    g["month"] = pd.to_datetime(g["target_month"] + "-01")
    fig = go.Figure()
    fig.add_scatter(x=g["month"], y=g["prediction"], name="M2-V3 예측",
                    line=dict(color=COLORS["M2_V3"], width=2))
    fig.add_scatter(x=g["month"], y=g["prediction_events_off"],
                    name="사건 압력을 0 으로 두었을 때",
                    line=dict(color="#9CA3AF", width=2, dash="dot"))
    fig.update_layout(height=340, yaxis_title="예측 (지수)", xaxis_title="대상 월",
                      hovermode="x unified", margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "같은 학습·같은 시점에서 **사건 변수만 0 으로 바꿔** 다시 예측한 것입니다. "
        "두 선의 간격이 곧 '사건 정보가 실제로 한 일'입니다.")

    st.info(meta["contribution_reading_md"])

# ---------------------------------------------------------------------------
# 6. 모델 벤치마크
# ---------------------------------------------------------------------------
with tabs[6]:
    st.subheader("모델 벤치마크 — 학습 데이터 안에서만 선택")
    st.info(
        "**최종 Test 성능을 보고 모델을 고른 것이 아니라, 각 예측시점의 과거 "
        "학습데이터 내부에서만 모델을 선택했습니다.**"
    )
    st.markdown(
        f"후보 모델: {', '.join(meta['models']['candidate_families'])} — "
        f"총 {meta['models']['n_candidate_configs']}개 설정. "
        "모든 단계에 **동일한 후보군과 동일한 CV 예산**을 적용했으며, "
        "**V3 에서 새 모델 계열을 추가하지 않았습니다.**"
    )

    vm = D["v3_metrics"]
    a, b = st.columns(2)
    with a:
        st.markdown("##### 단계별 MAE")
        cmp_df = vm[vm["view"].isin(["CONTROLLED_RIDGE",
                                     "BEST_CV_MULTIMODEL"])].copy()
        cmp_df["비교 방식"] = cmp_df["view"].map(
            {"CONTROLLED_RIDGE": "A. Ridge 고정",
             "BEST_CV_MULTIMODEL": "B. Best-CV"})
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
        sel = D["v3_selected"]
        sel = sel[sel["view"] == "BEST_CV_MULTIMODEL"]
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
# 7. Clean-PIT
# ---------------------------------------------------------------------------
with tabs[7]:
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
    st.divider()
    st.markdown("#### 사건 정보에도 같은 규칙을 적용했습니다")
    st.markdown(
        f"각 사건은 **인용한 공식 문서가 공개된 날짜**로 기록됩니다. 대상 월 `m` 의 "
        f"예측에는 `m` 이 시작되기 **전**에 알려진 것만 씁니다. "
        f"평가 구간 종료일(`{v3['backtest_last_origin']}`) 이후에 처음 알려진 정보는 "
        f"레지스트리 로더가 **거부**합니다 — 조사 중 실제로 마주쳤지만 이 규칙 때문에 "
        f"제외한 사건들이 있습니다."
    )

# ---------------------------------------------------------------------------
# 8. Agent Team
# ---------------------------------------------------------------------------
with tabs[8]:
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
    f"V3 registry `{v3['registry_version']}` / rubric `{v3['rubric_version']}` · "
    f"생성 {meta['exported_at']}"
)
