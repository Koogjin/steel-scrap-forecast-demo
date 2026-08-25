"""철스크랩 가격 예측 — Clean-PIT Forecasting Demo (presentation layer).

이 앱은 **저장된 결과만 읽는다.** 연구 파이프라인을 다시 돌리지 않는다:
BLS 원문을 내려받지 않고, PIT 패널을 재구성하지 않고, 사건을 수집하지 않고,
모델을 학습하지 않고, 외부 API 를 호출하지 않는다.

따라서 노트북 / Claude Code / VS Code 를 모두 꺼도 이 대시보드는 계속 동작한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
ASSETS = Path(__file__).parent / "assets"

OFFICIAL_MODELS = ("N0", "M0", "M1")
DEMO_MODEL = "M2_DEMO"

COLORS = {
    "actual": "#111827",
    "N0": "#9CA3AF",
    "M0": "#2563EB",
    "M1": "#059669",
    "M2_DEMO": "#D97706",
}
LABELS = {
    "N0": "N0 · 단순 기준선",
    "M0": "M0 · 과거 가격만",
    "M1": "M1 · + 시장/산업 데이터",
    "M2_DEMO": "M2 · + 공식 사건 압력 (탐색)",
}

st.set_page_config(page_title="철스크랩 가격 예측 Demo",
                   page_icon="🏭", layout="wide")


@st.cache_data
def load():
    metrics = pd.read_csv(DATA / "metrics.csv")
    preds = pd.read_csv(DATA / "predictions.csv")
    pressure = pd.read_csv(DATA / "event_pressure.csv")
    events = pd.read_csv(DATA / "event_registry.csv")
    meta = json.loads((DATA / "run_metadata.json").read_text(encoding="utf-8"))
    return metrics, preds, pressure, events, meta


metrics, preds, pressure, events, meta = load()

# ---------------------------------------------------------------------------
# 헤더
# ---------------------------------------------------------------------------
st.title("철스크랩 가격 예측")
st.caption("Claude Code 기반 Clean-PIT Forecasting Demo")

st.markdown(
    "> **각 과거 시점에 실제로 공개되어 있던 정보만 사용해서 예측했습니다.**"
)

k = meta["kpi"]
c = st.columns(7)
c[0].metric("예측 대상", k["target_label"])
c[1].metric("Clean-PIT 지표", f"{k['clean_pit_ready_x']}개")
c[2].metric("예측 시점", f"{k['n_origins']}개")
c[3].metric("자동 테스트", f"{k['n_tests']}개")
c[4].metric("원기관", f"{k['n_providers']}곳")
c[5].metric("FRED 의존", f"{k['fred_dependency']}")
c[6].metric("사전등록", "YES" if k["preregistered"] else "NO")

tab_sum, tab_model, tab_fc, tab_event, tab_why, tab_claude = st.tabs(
    ["📌 요약", "📊 모델 비교", "📈 예측 추이", "🌍 사건 압력",
     "🔬 Clean-PIT 란", "🤖 Claude Code 활용"])

# ---------------------------------------------------------------------------
# 요약
# ---------------------------------------------------------------------------
with tab_sum:
    st.subheader("경영진 요약")
    st.markdown(meta["executive_summary_md"])
    st.divider()
    st.subheader("3단계 모델 구조")
    p = ASSETS / "model_stages.png"
    if p.exists():
        st.image(str(p), width="stretch")

# ---------------------------------------------------------------------------
# 모델 비교
# ---------------------------------------------------------------------------
with tab_model:
    st.subheader("모델 성능 비교")
    st.markdown(
        "**공식(사전등록)** 결과와 **탐색적 Demo** 를 구분해서 봅니다. "
        "탐색적 결과는 사전등록된 결론이 아닙니다."
    )

    prim = metrics[metrics["target_id"] == meta["primary_target"]].copy()
    prim["구분"] = prim["model"].map(
        lambda m: "탐색적 Demo" if m == DEMO_MODEL else "공식 · 사전등록")
    prim["모델"] = prim["model"].map(LABELS)

    base = float(prim.loc[prim["model"] == "M0", "mae"].iloc[0])
    prim["상대 개선(vs M0)"] = (1 - prim["mae"] / base).map(lambda v: f"{v:+.1%}")

    left, right = st.columns([3, 2])
    with left:
        fig = go.Figure()
        for _, r in prim.iterrows():
            fig.add_bar(x=[LABELS[r["model"]]], y=[r["mae"]],
                        marker_color=COLORS[r["model"]],
                        name=r["구분"], showlegend=False,
                        text=[f"{r['mae']:.1f}"], textposition="outside")
        fig.update_layout(title="MAE (낮을수록 정확)", height=380,
                          yaxis_title="MAE (지수 포인트)",
                          margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig, width="stretch")
    with right:
        st.dataframe(
            prim[["모델", "구분", "mae", "rmse", "상대 개선(vs M0)"]]
            .rename(columns={"mae": "MAE", "rmse": "RMSE"})
            .style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}"}),
            hide_index=True, width="stretch")

    st.warning(
        "🔸 **M2 는 탐색적 Demo 이며 사전등록된 Primary 결과가 아닙니다.** "
        "공식 결론(N0/M0/M1)과 섞어 해석하지 마십시오."
    )

    st.divider()
    st.subheader("사전등록된 주요 가설 검정 결과")
    inf = meta["primary_inference"]
    a, b, cc, d = st.columns(4)
    a.metric("MAE 차이 (M0 − M1)", f"{inf['mean_d']:+.2f}")
    b.metric("상대 개선", f"{inf['skill']:+.1%}")
    cc.metric("DM 검정 p-value", f"{inf['dm_p']:.3f}")
    d.metric("95% 신뢰구간", f"[{inf['ci_low']:.1f}, {inf['ci_high']:.1f}]")
    st.info(meta["primary_conclusion_md"])

# ---------------------------------------------------------------------------
# 예측 추이
# ---------------------------------------------------------------------------
with tab_fc:
    st.subheader("실제값 vs 예측값")
    d = preds[preds["target_id"] == meta["primary_target"]].copy()
    d["target_month"] = pd.to_datetime(d["target_month"] + "-01")

    picks = st.multiselect(
        "표시할 모델", list(LABELS), default=["M0", "M1", DEMO_MODEL],
        format_func=lambda m: LABELS[m])

    fig = go.Figure()
    fig.add_scatter(x=d["target_month"], y=d["y_true"], name="실제값",
                    line=dict(color=COLORS["actual"], width=3))
    for m in picks:
        if m in d.columns:
            fig.add_scatter(x=d["target_month"], y=d[m], name=LABELS[m],
                            line=dict(color=COLORS[m], width=2,
                                      dash="dot" if m == DEMO_MODEL else None))
    fig.update_layout(height=460, yaxis_title="PPI 지수",
                      xaxis_title="대상 월", hovermode="x unified",
                      margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"평가 시점 {len(d)}개 · {d['target_month'].min():%Y-%m} ~ "
        f"{d['target_month'].max():%Y-%m} · 각 시점에서 그 당시 알 수 있던 "
        "정보만으로 다음 달을 예측했습니다.")

# ---------------------------------------------------------------------------
# 사건 압력
# ---------------------------------------------------------------------------
with tab_event:
    st.subheader("공식 사건 압력 (PEP / NEP)")
    st.markdown(
        "**뉴스기사 원문 대신 공식적으로 확인된 사건을 구조화하여 "
        "두 개의 압력 변수로 변환했습니다.**\n\n"
        "- **PEP** (Positive Evidence Pressure) — 가격 **상승** 압력 증거\n"
        "- **NEP** (Negative Evidence Pressure) — 가격 **하락** 압력 증거\n\n"
        "긍/부정 뉴스 감성이 아니며 두 지표는 서로 독립입니다. "
        "관세처럼 상승·하락 채널을 동시에 갖는 사건은 두 값이 같이 올라갑니다."
    )

    pp = pressure.copy()
    pp["month_dt"] = pd.to_datetime(pp["month"] + "-01")
    lo = pd.Timestamp(meta["window"]["first_target_month"] + "-01")
    pp = pp[pp["month_dt"] >= lo - pd.DateOffset(months=6)]

    fig = go.Figure()
    fig.add_scatter(x=pp["month_dt"], y=pp["PEP"], name="PEP (상승 압력)",
                    line=dict(color="#DC2626", width=2), fill="tozeroy")
    fig.add_scatter(x=pp["month_dt"], y=pp["NEP"], name="NEP (하락 압력)",
                    line=dict(color="#2563EB", width=2))
    for _, e in events.iterrows():
        km = pd.Timestamp(str(e["known_at_date"]))
        if km >= pp["month_dt"].min():
            fig.add_vline(x=km, line=dict(color="#9CA3AF", width=1, dash="dot"))
    fig.update_layout(height=380, yaxis_title="압력 점수",
                      xaxis_title="월", hovermode="x unified",
                      margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")

    st.markdown("#### 사건 목록 (전부 공식 출처)")
    for _, e in events.iterrows():
        with st.expander(f"{e['known_at_date']} · {e['event_name']}"):
            g1, g2, g3 = st.columns(3)
            g1.markdown(f"**단계**\n\n`{e['stage']}`")
            g2.markdown(f"**분류**\n\n`{e['category']}`")
            g3.markdown(f"**PEP / NEP**\n\n`{e['pep_contribution']} / "
                        f"{e['nep_contribution']}`")
            st.markdown(f"**경제적 경로** — {e['economic_channel']}")
            st.markdown(f"**요약** — {e['short_summary']}")
            st.markdown(f"**공식 출처** — [{e['official_source_name']}]"
                        f"({e['official_source_url']})")

    st.warning("🔸 사건 압력을 사용하는 M2 는 **탐색적 Demo** 입니다.")

# ---------------------------------------------------------------------------
# Clean-PIT
# ---------------------------------------------------------------------------
with tab_why:
    st.subheader("왜 Clean-PIT 인가")
    a, b = st.columns(2)
    with a:
        st.markdown("#### ⚠️ 기존 방식의 위험")
        st.markdown(
            "과거를 모델링할 때 **현재 최종 수정된 과거 데이터**를 쓰면, "
            "그 시점에는 알 수 없었던 정보가 모델에 들어갑니다.\n\n"
            "경제지표는 최초 발표 후 여러 차례 개정됩니다. "
            "개정된 값으로 과거를 학습하면 실제 운영에서는 재현되지 않는 "
            "성능이 나옵니다.")
    with b:
        st.markdown("#### ✅ 본 프로젝트의 방식")
        st.markdown(
            "BLS · Federal Reserve 의 **당시 historical release** 를 직접 "
            "재구성했습니다.\n\n"
            "각 예측 시점에서 `release_date <= 예측시점` 인 값만 사용하므로, "
            "그 시점에서 **실제로 가능했던 예측**만 수행합니다.")
    st.divider()
    st.markdown("#### 실제로 개정이 일어난다는 증거")
    st.dataframe(pd.DataFrame(meta["revision_examples"]), hide_index=True,
                 width="stretch")
    st.caption("같은 관측월의 값이 발표 시점에 따라 다릅니다. "
               "Clean-PIT 패널은 이 차이를 그대로 보존합니다.")

# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------
with tab_claude:
    st.subheader("Claude Code 활용 과정")
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
