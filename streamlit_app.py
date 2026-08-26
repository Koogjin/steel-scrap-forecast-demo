"""미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo — presentation layer (V4).

이 앱은 **저장된 결과만 읽는다.** 연구 파이프라인을 다시 돌리지 않는다:
원문 데이터를 내려받지 않고, PIT 패널을 재구성하지 않고, 사건을 수집하지 않고,
모델을 학습하지 않고, 외부 API 를 호출하지 않는다.

## 경영진 리포팅 규약 (§PART Q)

이 대시보드는 **개별 차트를 스크린샷으로 잘라 PowerPoint 에 붙여도** 뜻이 통해야
한다. 그래서 모든 주요 그래프는

  - 제목이 **비즈니스 질문**을 말하고 (§33)
  - 범례가 **모델 코드가 아니라 의미**를 먼저 말하고 (§31, §42)
  - 축 이름이 한국어이며 단위를 담고 (§35)
  - 방향 단서(↓ 낮을수록 정확 등)를 제목에 넣고 (§36)
  - **각주가 그림 안에** 들어가며 (§40)
  - 그림 밖에는 한 줄 핵심 해석이 따라붙는다 (§39)

핵심 해석 문구는 **저장된 수치에서 계산**한다 — 손으로 쓴 성공 주장을 넣지 않는다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
ASSETS = Path(__file__).parent / "assets"

# ---------------------------------------------------------------------------
# §42 — 경영진용 모델 표기 표준. 의미를 먼저, 코드는 괄호 안에.
# ---------------------------------------------------------------------------
LABEL = {
    "actual": "실제 WPU1012 지수",
    "N0": "직전 가용치 그대로 (N0)",
    "M0": "과거 PPI 기반 (M0)",
    "M1": "시장·산업 정보 추가 (M1)",
    "M2_V2": "공식 Event 확장 V2 (M2-V2)",
    "M2_V3": "Event 표현 고도화 V3 (M2-V3)",
    "M1_shared": "동일 규제 시장정보 (M1-shared)",
    "M2_shared": "동일 규제 + Event (M2-shared)",
    "M1R": "시장정보 보정 모델 (M1-R)",
    "M2R": "Event 정보 보정 모델 (M2-R)",
}
SHORT = {"N0": "N0", "M0": "M0", "M1": "M1", "M2_V2": "M2-V2", "M2_V3": "M2-V3",
         "M1_shared": "M1-shared", "M2_shared": "M2-shared",
         "M1R": "M1-R", "M2R": "M2-R"}
COLORS = {"actual": "#111827", "N0": "#9CA3AF", "M0": "#2563EB", "M1": "#059669",
          "M2_V2": "#D97706", "M2_V3": "#BE185D", "M1_shared": "#0891B2",
          "M2_shared": "#7C3AED", "M1R": "#0D9488", "M2R": "#DB2777"}
UP_COLOR, DOWN_COLOR = "#DC2626", "#2563EB"

#: §40 — 스크린샷이 홀로 돌아다녀도 문맥이 남도록 그림 **안에** 넣는 각주.
FOOT_TARGET = ("Target: BLS WPU1012 — Iron and steel scrap PPI  ·  "
               "주의: 실제 $/ton 현물가격이 아니라 생산자물가지수입니다")
FOOT_EVENT = ("PEP/NEP: 공식 Event 를 경제적 전달경로에 따라 구조화한 상·하방 "
              "pressure score이며 확률이 아님")

st.set_page_config(page_title="철·강 스크랩 PPI 예측 Demo",
                   page_icon="🏭", layout="wide")


@st.cache_data
def load():
    d = {}
    for key, name in (
        ("official_metrics", "metrics.csv"),
        ("episodes", "event_episode_registry_v3.csv"),
        ("transitions", "event_transition_registry_v3.csv"),
        ("pressure_v3", "pep_nep_v3.csv"),
        ("cat_state", "event_monthly_category_state_v3.csv"),
        ("contrib", "event_contribution_v3.csv"),
        ("v4_metrics", "demo_v4_metrics.csv"),
        ("v4_preds", "demo_v4_predictions.csv"),
        ("v4_attr", "demo_v4_event_attribution.csv"),
        ("v4_selected", "demo_v4_selected_models.csv"),
        ("x_registry", "x_feature_registry.csv"),
    ):
        d[key] = pd.read_csv(DATA / name)
    d["meta"] = json.loads((DATA / "run_metadata.json").read_text(encoding="utf-8"))
    return d


D = load()
meta = D["meta"]
tgt = meta["target"]
k = meta["kpi"]
v3 = meta["demo_v3"]
v4 = meta["demo_v4"]


# ---------------------------------------------------------------------------
# 차트 헬퍼 — §PART Q 규약을 한 곳에서 강제한다
# ---------------------------------------------------------------------------

def finish(fig: go.Figure, *, title: str, question: str | None = None,
           ylab: str = "", xlab: str = "", footnote: str | None = None,
           height: int = 420, legend: bool = True,
           yrange: list | None = None) -> go.Figure:
    """제목·질문·축·각주·범례를 **그림 안에** 넣어 스크린샷 자립성을 확보한다."""
    head = f"<b>{title}</b>"
    if question:
        head = (f"<span style='font-size:12px;color:#6B7280'>{question}</span>"
                f"<br>{head}")
    bottom = 66 if footnote else 44
    fig.update_layout(
        title=dict(text=head, x=0.0, xanchor="left", y=0.96, yanchor="top",
                   font=dict(size=17, color="#111827")),
        height=height,
        yaxis_title=ylab, xaxis_title=xlab,
        hovermode="x unified",
        margin=dict(t=96 if question else 78, b=bottom, l=64, r=24),
        font=dict(size=13),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.005, xanchor="left",
                    x=0.0, font=dict(size=12.5)) if legend else None,
        showlegend=legend,
    )
    if yrange:
        fig.update_yaxes(range=yrange)
    fig.update_xaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    if footnote:
        fig.add_annotation(
            text=f"<span style='font-size:10.5px;color:#9CA3AF'>{footnote}</span>",
            xref="paper", yref="paper", x=0.0, y=-0.20, xanchor="left",
            yanchor="top", showarrow=False, align="left")
    return fig


def takeaway(text: str) -> None:
    """§39 — 저장된 수치에서 계산한 한 줄 핵심 해석."""
    st.markdown(
        f"<div style='background:#F8FAFC;border-left:4px solid #2563EB;"
        f"padding:10px 14px;margin:6px 0 18px 0;border-radius:4px;"
        f"font-size:14px;line-height:1.6'>"
        f"<b style='color:#2563EB'>핵심 해석</b><br>{text}</div>",
        unsafe_allow_html=True)


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch",
                    config={"displayModeBar": False})


def m(view: str, model: str) -> float:
    """저장된 V4 지표표에서 MAE 를 꺼낸다."""
    r = D["v4_metrics"]
    s = r[(r["view"] == view) & (r["model"] == model)]
    return float(s["mae"].iloc[0])


# ---------------------------------------------------------------------------
# 헤더 (§PART M)
# ---------------------------------------------------------------------------
st.title("미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo")
st.markdown(f"#### BLS {tgt['series_id']} — {tgt['name_en']}")
st.markdown(
    "> **쉽게 말하면, 미국 철·강 스크랩 시장의 전반적인 생산자 가격 움직임을 "
    "보여주는 BLS 공식 가격지수입니다.**  \n"
    "> 각 과거 시점에 실제로 공개되어 있던 정보만 사용해서 다음 달을 예측했습니다."
)

c = st.columns(7)
c[0].metric("예측 대상", tgt["series_id"])
c[1].metric("원천지표", f"{k['clean_pit_ready_x']}개 → 파생 12개")
c[2].metric("예측 시점", f"{k['n_origins']}개")
c[3].metric("공식 사건", f"{v3['n_episodes']}건 / {v3['n_transitions']}상태")
c[4].metric("자동 테스트", f"{k['n_tests']}개")
c[5].metric("FRED 의존", f"{k['fred_dependency']}")
c[6].metric("동일 Train/Test", "YES")

st.info(
    "🎯 **예측 대상** — 실제 $/ton 거래가격이 아니라 **BLS 공식 생산자물가지수(PPI)** "
    "입니다. 지수 600은 톤당 600달러라는 뜻이 아닙니다."
)

tabs = st.tabs([
    "📌 요약", "🎯 무엇을 예측하나", "🧾 어떤 데이터를 쓰나", "📊 성능 비교",
    "📈 예측 추이", "🌍 사건 압력", "🔍 Event 보정 진단", "🧮 왜 이 모델인가",
    "🧬 M2 진화", "🔬 Clean-PIT 란", "🤖 Agent Team",
])

# ===========================================================================
# 0. 요약
# ===========================================================================
with tabs[0]:
    st.subheader("경영진 요약")
    st.markdown(meta["executive_summary_md"])

    st.divider()
    st.subheader("모델은 이렇게 정보를 쌓습니다 (§PART N)")
    p = ASSETS / "model_story.png"
    if p.exists():
        st.image(str(p), width="stretch")
    a, b, cc = st.columns(3)
    a.markdown("**M0 — 과거 PPI 기반**  \n가격 자체가 가진 정보")
    b.markdown("**M1-R — 시장정보 보정**  \n시장·산업 정보가 추가로 설명한 부분")
    cc.markdown("**M2-R — Event 정보 보정**  \n공식 Event 정보가 추가로 설명한 부분")

    st.divider()
    best = D["v4_metrics"].loc[D["v4_metrics"]["mae"].idxmin()]
    st.success(
        "✅ **모든 비교는 동일한 Train/Test 기준입니다** — "
        f"같은 예측 시점 {k['n_origins']}개, 같은 학습 행, 같은 대상 월, 같은 지표."
    )
    st.warning(
        f"현재 결과에서 가장 낮은 평균오차는 **{LABEL[best['model']]}** "
        f"(MAE {best['mae']:.2f}) 이며, 이는 **공식 사전등록 결과**입니다. "
        "시장·Event 정보를 추가한 확장 모델은 아직 이 값을 넘지 못했습니다 — "
        "부정적 결과를 그대로 보고합니다."
    )

# ===========================================================================
# 1. 무엇을 예측하나 (§PART M)
# ===========================================================================
with tabs[1]:
    st.subheader("무엇을 예측하나")
    st.markdown(meta["target_explainer_md"])

    st.divider()
    st.markdown("#### 지수를 읽는 법 (§24)")
    a, b = st.columns(2)
    a.markdown(
        "**지수 상승 ↑**  \n전반적인 미국 철·강 스크랩 **생산자 가격 수준 상승** 방향")
    b.markdown(
        "**지수 하락 ↓**  \n전반적인 **생산자 가격 수준 하락** 방향")
    st.error(
        "**지수 600 ≠ $600/ton 입니다.**  \n"
        "예: 500 → 550 은 **약 10% 지수 상승**이지 **$50/ton 상승이 아닙니다.** "
        "지수 차이는 항상 **변화율**로 읽습니다."
    )

    d = D["v4_preds"].copy()
    d["month"] = pd.to_datetime(d["target_month"] + "-01")
    fig = go.Figure()
    fig.add_scatter(x=d["month"], y=d["y_true"], name=LABEL["actual"],
                    line=dict(color=COLORS["actual"], width=3.2), fill="tozeroy",
                    fillcolor="rgba(17,24,39,0.06)")
    lo, hi = float(d["y_true"].min()), float(d["y_true"].max())
    imin = d["y_true"].idxmin()
    imax = d["y_true"].idxmax()
    for i, txt in ((imax, f"최고 {hi:.0f}"), (imin, f"최저 {lo:.0f}")):
        fig.add_annotation(x=d.loc[i, "month"], y=d.loc[i, "y_true"], text=txt,
                           showarrow=True, arrowhead=0, ax=0, ay=-26,
                           font=dict(size=11.5, color="#374151"))
    show(finish(fig, question="Q. 예측 대상 지수는 실제로 어떻게 움직였는가?",
                title="미국 철·강 스크랩 PPI 지수의 실제 궤적",
                ylab="PPI 지수 (1982-06 = 100)", xlab="대상 월",
                footnote=FOOT_TARGET, height=400, legend=False))
    takeaway(
        f"이 구간에서 지수는 <b>{lo:.0f} ~ {hi:.0f}</b> 사이를 움직였습니다. "
        f"{lo:.0f} 에서 {hi:.0f} 로 가는 것은 <b>{(hi / lo - 1):+.0%}</b> 변화이며, "
        f"달러 금액이 아니라 <b>변화율</b>로 읽어야 합니다.")

    st.warning(
        "본 Demo는 특정 기업의 구매가격, 특정 스크랩 grade 의 거래가격, "
        "또는 $/ton 현물가격을 예측하는 모델이 **아닙니다**."
    )

# ===========================================================================
# 2. 어떤 데이터를 쓰나 (§PART A · §6 · §7 · §8 · §9)
# ===========================================================================
with tabs[2]:
    st.subheader("어떤 시장·산업 데이터를 쓰나")

    st.markdown("#### 6개의 원천지표 → 12개의 파생 Feature (§7)")
    a, b, cc = st.columns([2, 1, 2])
    a.markdown(
        "<div style='background:#EFF6FF;border-radius:8px;padding:16px;"
        "text-align:center'><b style='font-size:28px;color:#2563EB'>6</b><br>"
        "<b>원천지표</b><br><span style='font-size:12.5px;color:#6B7280'>"
        "BLS · Federal Reserve 공식 계열</span></div>", unsafe_allow_html=True)
    b.markdown(
        "<div style='text-align:center;padding-top:26px;font-size:13px;"
        "color:#6B7280'>각각<br><b>현재 수준 (Level)</b><br>+<br>"
        "<b>최근 3개월 변화 (Momentum)</b><br>→</div>", unsafe_allow_html=True)
    cc.markdown(
        "<div style='background:#ECFDF5;border-radius:8px;padding:16px;"
        "text-align:center'><b style='font-size:28px;color:#059669'>12</b><br>"
        "<b>파생 Feature</b><br><span style='font-size:12.5px;color:#6B7280'>"
        "6 × 2 형태</span></div>", unsafe_allow_html=True)

    st.error(
        "**12개의 서로 다른 외부 데이터셋이 아닙니다.** "
        "6개의 검증된 원천지표에서 2개 형태(수준 · 3개월 변화)의 feature 를 "
        "생성한 것입니다."
    )

    st.markdown("#### 원천지표 설명 (§6)")
    xr = D["x_registry"].copy()
    st.dataframe(
        xr[["series_id", "official_name", "source", "measures",
            "possible_channel", "derived_features"]]
        .rename(columns={"series_id": "Series ID", "official_name": "공식 계열명",
                         "source": "출처", "measures": "무엇을 측정하나",
                         "possible_channel": "스크랩 PPI 와 관련 가능한 경로",
                         "derived_features": "파생 Feature"}),
        hide_index=True, width="stretch")
    st.caption(
        "‘관련 가능한 경로’는 **가능한 관련 경로**를 서술한 것이며 인과관계 주장이 "
        "아닙니다. 공식 계열명·출처·발간물은 프로젝트 registry 에 기록된 값입니다.")

    st.divider()
    st.markdown("#### 왜 이 6개인가 (§8)")
    st.markdown(
        "단순히 상관이 높은 변수를 넣은 것이 아닙니다. Primary 모델에는 다음 조건을 "
        "**모두** 만족한 Clean-PIT 계열만 사용했습니다.\n\n"
        "- **원기관 원문 출처** — FRED 같은 재배포처가 아니라 BLS · Federal Reserve 원문\n"
        "- **충분한 과거 커버리지** — 학습에 필요한 기간이 실제로 존재\n"
        "- **Point-in-Time 재구성 가능** — 그 시점에 발표되어 있던 값을 복원 가능\n"
        "- **발표일 검증** — 언제 공개됐는지를 문서로 확인\n"
        "- **개정(revision) 처리** — 이후 수정본이 과거로 새어들지 않음\n"
        "- **재현 가능성** — 매월 같은 경로로 갱신 가능\n"
        "- **공개 배포 안전성** — 저작권·이용약관상 공개 Demo 에 적합"
    )
    st.info(
        f"**{meta['x_explainer']['historical_only_note']}**"
    )

    st.divider()
    st.markdown("#### 출처 · 저작권 (§9)")
    st.markdown(
        "이 Demo 는 **Series ID · 출처 기관 · 짧은 요약 설명 · 파생 결과**만 "
        "사용합니다. 원문 PDF/XLSX, 공식 문서 전문, 기사 본문, 제3자 설명문, "
        "로고, 자격증명, 회사 내부 정보는 **포함하지 않습니다.**"
    )
    st.success(f"이번 단계에서 **새로운 외부 데이터 소스를 추가하지 않았습니다** — "
               f"{meta['x_explainer']['future_work_note']}")

# ===========================================================================
# 3. 성능 비교 (§PART J · §25 · §33 · §37)
# ===========================================================================
with tabs[3]:
    st.subheader("모델 성능 비교")
    st.markdown(
        "**공식 사전등록 결과(N0/M0/M1)와 탐색적 확장(M2·M1-R·M2-R)을 분리해서** "
        "보여줍니다. 모두 같은 예측 시점·같은 학습 행·같은 대상 월입니다."
    )

    vm = D["v4_metrics"].copy()
    view_names = {
        "VIEW_A_OFFICIAL": "A. 공식 사전등록 (N0 / M0 / M1)",
        "VIEW_B_HISTORICAL_DEMO": "B. 과거 Event Demo (M2-V2 / M2-V3)",
        "VIEW_C_SHARED_ALPHA": "C. 동일 규제 대조 (M1-shared / M2-shared)",
        "VIEW_D_MAIN_V4": "D. V4 단계 보정 (M0 → M1-R → M2-R)",
    }
    picks = st.multiselect(
        "표시할 비교 그룹", list(view_names), default=list(view_names),
        format_func=lambda v: view_names[v])
    sub = vm[vm["view"].isin(picks)].copy()
    sub = sub.drop_duplicates(subset=["view", "model"])
    sub["라벨"] = sub["model"].map(SHORT)
    sub["표시"] = sub.apply(
        lambda r: f"{SHORT[r['model']]}<br><span style='font-size:10px'>"
                  f"{'공식' if r['status'] == 'OFFICIAL_PREREGISTERED' else '탐색'}"
                  f"</span>", axis=1)

    best_i = sub["mae"].idxmin()
    fig = go.Figure()
    for _, r in sub.iterrows():
        official = r["status"] == "OFFICIAL_PREREGISTERED"
        fig.add_bar(
            x=[r["표시"]], y=[r["mae"]], showlegend=False,
            marker=dict(color=COLORS[r["model"]],
                        line=dict(color="#111827" if official else "#FFFFFF",
                                  width=2 if official else 0)),
            text=[f"{r['mae']:.1f}"], textposition="outside",
            textfont=dict(size=12),
            hovertemplate=f"{LABEL[r['model']]}<br>MAE %{{y:.2f}}<extra></extra>")
    br = sub.loc[best_i]
    fig.add_annotation(
        x=br["표시"], y=br["mae"], text="가장 낮은 평균오차<br>(공식 결과)"
        if br["status"] == "OFFICIAL_PREREGISTERED" else "가장 낮은 평균오차<br>(탐색)",
        showarrow=True, arrowhead=0, ax=0, ay=-46,
        font=dict(size=11.5, color="#111827"), bgcolor="rgba(255,255,255,0.85)")
    show(finish(
        fig,
        question="Q. 시장·Event 정보를 추가하면 예측 정확도가 좋아지는가?",
        title="시장·Event 정보를 추가하면 예측 정확도가 좋아지는가?  "
              "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
        ylab="평균 예측오차 MAE (지수 Point)", xlab="모델",
        footnote=FOOT_TARGET + "  ·  테두리 있는 막대 = 공식 사전등록 결과",
        height=470, legend=False))

    m0 = m("VIEW_A_OFFICIAL", "M0")
    takeaway(
        f"현재 결과에서는 <b>과거 PPI 기반 (M0)</b> 이 가장 낮은 평균오차 "
        f"(MAE {m0:.2f})를 보였습니다. 시장 정보를 더한 M1 은 {m('VIEW_A_OFFICIAL','M1'):.2f}, "
        f"V4 의 단계 보정 모델 M1-R 은 {m('VIEW_D_MAIN_V4','M1R'):.2f}, "
        f"M2-R 은 {m('VIEW_D_MAIN_V4','M2R'):.2f} 로 <b>모두 M0 보다 나빴습니다.</b>")

    st.markdown("##### 전체 수치")
    disp = sub.copy()
    disp["모델"] = disp["model"].map(LABEL)
    disp["지위"] = disp["status"].map(
        {"OFFICIAL_PREREGISTERED": "공식 사전등록", "EXPLORATORY": "탐색적 확장"})
    st.dataframe(
        disp[["모델", "mae", "rmse", "smape", "directional_accuracy", "지위"]]
        .rename(columns={"mae": "MAE ↓", "rmse": "RMSE ↓", "smape": "sMAPE ↓",
                         "directional_accuracy": "방향 정확도 ↑"})
        .style.format({"MAE ↓": "{:.2f}", "RMSE ↓": "{:.2f}", "sMAPE ↓": "{:.3f}",
                       "방향 정확도 ↑": "{:.2f}"}),
        hide_index=True, width="stretch")

    st.divider()
    st.markdown("#### 동일 규제 대조가 밝혀낸 것 (§20)")
    ms1, ms2 = m("VIEW_C_SHARED_ALPHA", "M1_shared"), m("VIEW_C_SHARED_ALPHA", "M2_shared")
    v3d = m("VIEW_B_HISTORICAL_DEMO", "M2_V3")
    a, b, cc = st.columns(3)
    a.metric("M2-V3 − M1 (V3, 규제 재선택 허용)", f"{v3d - ms1:+.3f}")
    b.metric("M2-shared − M1-shared (규제 고정)", f"{ms2 - ms1:+.3f}")
    cc.metric("Event 정보가 아니었던 몫",
              f"{100 * (1 - (ms2 - ms1) / (v3d - ms1)):.0f}%")
    st.info(meta["v4_shared_alpha_md"])

    st.divider()
    with st.expander("공식 사전등록 결과 원본 (수정하지 않음)"):
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
            f"[{pi['ci_low']:.1f}, {pi['ci_high']:.1f}] — 개선 증거 없음.")
    st.markdown(meta["result_reading_md"])

# ===========================================================================
# 4. 예측 추이 (§26)
# ===========================================================================
with tabs[4]:
    st.subheader("각 모델이 실제 움직임을 얼마나 따라갔나")
    d = D["v4_preds"].copy()
    d["month"] = pd.to_datetime(d["target_month"] + "-01")
    d = d.rename(columns={"M0_official": "M0off", "M1_official": "M1off"})

    options = ["M0", "M1", "M2_V3", "M1R", "M2R", "N0"]
    colmap = {"M0": "M0", "M1": "M1off", "M2_V3": "M2_V3", "M1R": "M1R",
              "M2R": "M2R", "N0": "N0"}
    picks = st.multiselect("표시할 모델", options, default=["M0", "M1R", "M2R"],
                           format_func=lambda x: LABEL[x])

    fig = go.Figure()
    fig.add_scatter(x=d["month"], y=d["y_true"], name=LABEL["actual"],
                    line=dict(color=COLORS["actual"], width=3.2))
    for mm in picks:
        fig.add_scatter(x=d["month"], y=d[colmap[mm]], name=LABEL[mm],
                        line=dict(color=COLORS[mm], width=2,
                                  dash="dot" if mm in ("M2R", "M2_V3") else None))
    show(finish(
        fig,
        question="Q. 실제 지수의 급등·급락을 어떤 모델이 더 잘 따라갔는가?",
        title="각 모델이 실제 철·강 스크랩 PPI 움직임을 얼마나 따라갔는가",
        ylab="PPI 지수 (1982-06 = 100)", xlab="대상 월",
        footnote=FOOT_TARGET, height=520))
    err = {mm: float((d["y_true"] - d[colmap[mm]]).abs().mean()) for mm in picks}
    if err:
        bestm = min(err, key=err.get)
        takeaway(
            f"표시된 모델 중 실제값에 가장 가까웠던 것은 <b>{LABEL[bestm]}</b> "
            f"(평균 오차 {err[bestm]:.1f} 지수 Point)입니다. "
            "다만 <b>선이 가까워 보이는 것과 통계적으로 유의한 개선은 다릅니다</b> — "
            f"예측 시점 {len(d)}개로는 검정력이 제한적입니다.")
    st.caption(
        f"{len(d)}개 시점 · {d['month'].min():%Y-%m} ~ {d['month'].max():%Y-%m} · "
        "각 시점에서 그 당시 알 수 있던 정보만으로 다음 달을 예측했습니다.")

# ===========================================================================
# 5. 사건 압력 (§27 · §32)
# ===========================================================================
with tabs[5]:
    st.subheader("공식 사건 기반 압력 지표 (PEP / NEP)")
    st.markdown(
        "**뉴스기사 원문 대신 공식적으로 확인된 사건·상태를 구조화하여 두 개의 "
        "압력 변수로 변환했습니다.**\n\n"
        "- **PEP ↑** — 공식 Event 근거상 **가격 상승 압력**이 강해짐\n"
        "- **NEP ↑** — 공식 Event 근거상 **가격 하락 압력**이 강해짐\n"
        "- **둘 다 높음** — 상·하방 근거가 동시에 존재하는 **상충 환경**\n"
        "- **둘 다 낮음** — 조용한 Event 환경\n\n"
        "긍/부정 뉴스 감성이 아니며, **확률이 아닙니다.** 두 지표는 독립입니다."
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
    fig.add_scatter(x=pp["month_dt"], y=pp["PEP"], name="상방 Event 압력 (PEP)",
                    line=dict(color=UP_COLOR, width=2.4), fill="tozeroy",
                    fillcolor="rgba(220,38,38,0.10)")
    fig.add_scatter(x=pp["month_dt"], y=pp["NEP"], name="하방 Event 압력 (NEP)",
                    line=dict(color=DOWN_COLOR, width=2.4))
    show(finish(
        fig,
        question="Q. 공식 Event 가 가격 상·하방 압력을 얼마나 만들었는가?",
        title="공식 Event 가 가격 상·하방 압력을 얼마나 만들었는가  "
              "<span style='font-size:13px;color:#6B7280'>"
              "PEP ↑ 상방 압력 강함 · NEP ↑ 하방 압력 강함</span>",
        ylab="Event 압력 (0 ~ 1, 확률 아님)", xlab="월",
        footnote=FOOT_EVENT, height=440, yrange=[0, 1]))
    takeaway(
        f"평가 구간에서 상방 압력(PEP)은 서로 다른 값 "
        f"{v3['coverage']['pep_distinct']}개로 실제로 움직였습니다. "
        "새로 발생한 조치일수록 강하고, 오래 유지된 상태는 낮은 수준으로 "
        "가라앉습니다 — 몇 년째 유지 중인 관세는 ‘압력’이 아니라 ‘baseline’ 이기 "
        "때문입니다.")

    st.markdown("#### 분류별 압력")
    cs = D["cat_state"].copy()
    cs["month_dt"] = pd.to_datetime(cs["month"] + "-01")
    cs = cs[cs["month_dt"] >= lo]
    direction = st.radio("방향", ["상방 압력 (PEP)", "하방 압력 (NEP)"], index=0,
                         horizontal=True, key="cat_dir")
    col = "up" if direction.startswith("상방") else "down"
    fig = go.Figure()
    for label, grp in cs.groupby("category_label"):
        if grp[col].max() == 0:
            continue
        fig.add_scatter(x=grp["month_dt"], y=grp[col], name=label,
                        line=dict(width=1.8))
    show(finish(
        fig, question="Q. 어떤 종류의 공식 Event 가 압력을 만들었는가?",
        title=f"분류별 {direction}",
        ylab=f"{direction} (0 ~ 1)", xlab="월", footnote=FOOT_EVENT,
        height=420, yrange=[0, 1]))
    empty_cats = sorted(set(cs["category_label"]) -
                        set(cs[cs["up"] > 0]["category_label"]) -
                        set(cs[cs["down"] > 0]["category_label"]))
    if empty_cats:
        st.caption(
            f"기록이 없는 분류: {', '.join(empty_cats)} — 월을 채우려고 사건을 "
            "만들지 않았습니다. 집계 방식상 빈 분류는 다른 분류를 희석하지 않습니다.")

    st.markdown("#### 사안과 상태 변화 (전부 공식 출처)")
    eps, trs = D["episodes"], D["transitions"]
    cats = st.multiselect("분류", sorted(eps["category_label"].unique()),
                          default=sorted(eps["category_label"].unique()))
    for _, e in eps[eps["category_label"].isin(cats)].iterrows():
        mine = trs[trs["episode_id"] == e["episode_id"]].sort_values("known_at_date")
        with st.expander(f"{e['episode_name']}  ·  {e['category_label']}  ·  "
                         f"상태 변화 {len(mine)}건  ({e['first_known_at']} ~ "
                         f"{e['last_known_at']})"):
            g = st.columns(3)
            g[0].markdown(f"**직접성 (directness)**\n\n`{e['directness']} / 3`")
            g[1].markdown(f"**범위 (scope)**\n\n`{e['scope']} / 3`")
            g[2].markdown(
                f"**종료**\n\n`{e['end_date'] if isinstance(e['end_date'], str) and e['end_date'] else '진행 중'}`")
            st.markdown(f"**경제적 경로** — {e['economic_channel']}")
            for _, t in mine.iterrows():
                st.markdown(
                    f"- `{t['known_at_date']}` **{t['stage']}** "
                    f"(확실성 {t['certainty']:.2f} · 기본강도 "
                    f"{t['base_strength']:.3f} · 상방 {t['direction_up']:.2f} / "
                    f"하방 {t['direction_down']:.2f})  \n"
                    f"  {t['short_summary']}  \n"
                    f"  [{t['official_source_name']}]({t['official_source_url']})")

    with st.expander("채점 규칙 — 결과를 보기 전에 고정했습니다"):
        st.markdown(meta["event_method_v3_md"])

# ===========================================================================
# 6. Event 보정 진단 (§28 · §22 · §23 · §29)
# ===========================================================================
with tabs[6]:
    st.subheader("Event 정보가 기본 예측을 얼마나 수정했나")
    st.markdown(meta["v4_architecture_md"])

    at = v4["attribution"]
    a = st.columns(5)
    a[0].metric("median 보정폭", f"{at['median_abs_event_correction']:.1f}",
                help="지수 Point. 0 에 가까울수록 Event 가 예측을 안 움직인 것.")
    a[1].metric("max 보정폭", f"{at['max_abs_event_correction']:.1f}")
    a[2].metric("|보정| < 1 인 시점", f"{at['pct_abs_lt_1']:.0f}%")
    a[3].metric("|보정| > 5 인 시점", f"{at['pct_abs_gt_5']:.0f}%")
    a[4].metric("방향이 맞은 비율",
                f"{at['sign_agreement_with_actual_residual_pct']:.0f}%",
                help="보정 방향이 실제 잔차 방향과 일치한 비율. 50% = 동전 던지기.")

    d = D["v4_attr"].copy()
    d["month"] = pd.to_datetime(d["target_month"] + "-01")
    fig = go.Figure()
    fig.add_bar(x=d["month"], y=d["event_correction"],
                marker_color=[UP_COLOR if v > 0 else DOWN_COLOR
                              for v in d["event_correction"]],
                name="Event 보정폭", showlegend=False,
                hovertemplate="%{x|%Y-%m}<br>보정 %{y:+.1f} 지수 Point<extra></extra>")
    fig.add_hline(y=0, line=dict(color="#6B7280", width=1.2))
    imx = d["event_correction"].abs().idxmax()
    fig.add_annotation(
        x=d.loc[imx, "month"], y=d.loc[imx, "event_correction"],
        text=f"최대 보정 {d.loc[imx, 'event_correction']:+.0f}",
        showarrow=True, arrowhead=0,
        ay=-34 if d.loc[imx, "event_correction"] > 0 else 34, ax=0,
        font=dict(size=11.5), bgcolor="rgba(255,255,255,0.85)")
    show(finish(
        fig,
        question="Q. Event 정보가 실제 예측값을 움직였는가?",
        title="Event 정보가 기본 예측을 얼마나 수정했는가  "
              "<span style='font-size:13px;color:#6B7280'>"
              "+ = Event 반영 후 더 높은 지수 예측 · − = 더 낮은 지수 예측</span>",
        ylab="Event 보정폭 (지수 Point)", xlab="대상 월",
        footnote=FOOT_EVENT + "  ·  단계 구조상 M2-R − M1-R 이 곧 Event 보정폭",
        height=460, legend=False))
    takeaway(meta["v4_event_takeaway_md"])

    st.divider()
    st.markdown("#### Event 보정 전 vs 후 (§22)")
    b1, b2, b3 = st.columns(3)
    b1.metric("보정 전 MAE (M1-R)", f"{at['mae_before_event_correction_M1R']:.2f}")
    b2.metric("보정 후 MAE (M2-R)", f"{at['mae_after_event_correction_M2R']:.2f}",
              delta=f"{at['mae_delta']:+.2f}", delta_color="inverse")
    b3.metric("개선 / 악화 시점",
              f"{at['n_origins_improved']} / {at['n_origins_worsened']}")

    st.markdown(f"#### Event 활발한 시기 vs 조용한 시기 (§23)")
    ea, eq = at["event_active"], at["event_quiet"]
    fig = go.Figure()
    xs, ys1, ys2 = [], [], []
    for name, g in (("Event 활발한 달", ea), ("조용한 달", eq)):
        if g["n"]:
            xs.append(f"{name}  (n={g['n']})")
            ys1.append(g["m1r_mae"])
            ys2.append(g["m2r_mae"])
    fig.add_bar(x=xs, y=ys1, name=LABEL["M1R"], marker_color=COLORS["M1R"],
                text=[f"{v:.1f}" for v in ys1], textposition="outside")
    fig.add_bar(x=xs, y=ys2, name=LABEL["M2R"], marker_color=COLORS["M2R"],
                text=[f"{v:.1f}" for v in ys2], textposition="outside")
    fig.update_layout(barmode="group")
    show(finish(
        fig,
        question="Q. Event 가 강한 시기에 Event 모델이 더 유용했는가?",
        title="Event 활발한 시기 vs 조용한 시기의 예측 정확도  "
              "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
        ylab="평균 예측오차 MAE (지수 Point)", xlab="",
        footnote=f"Event-active 기준: max(PEP, NEP) ≥ "
                 f"{at['event_active_threshold']} — 결과를 보기 **전에** 동결한 "
                 f"임계값. 서술적 비교이며 유의성을 주장하지 않음.",
        height=440))
    takeaway(meta["v4_regime_takeaway_md"])

    st.divider()
    st.markdown("#### 어떤 Event 표현과 모델이 선택됐나 (§40 · §41)")
    sel = D["v4_selected"]
    a, b = st.columns(2)
    with a:
        cnt = sel["event_feature_family"].value_counts().reindex(
            ["E0", "E1", "E2"]).fillna(0).astype(int)
        fig = go.Figure(go.Bar(
            x=["E0 · 현재 압력 수준", "E1 · 수준 + 변화", "E2 · 수준 + 1개월 전"],
            y=cnt.values, marker_color=["#94A3B8", "#0D9488", "#7C3AED"],
            text=cnt.values, textposition="outside", showlegend=False))
        show(finish(fig, title="가장 자주 선택된 Event 표현",
                    ylab="선택된 예측 시점 수", xlab="", height=380, legend=False,
                    footnote="학습 데이터 내부 CV 로만 선택 · 최종 Test 미사용"))
    with b:
        cnt2 = sel["event_model"].value_counts()
        fig = go.Figure(go.Bar(
            x=[{"ols": "OLS (규제 없음)", "ridge": "Ridge (규제)",
                "huber": "Huber (이상치 강건)"}.get(i, i) for i in cnt2.index],
            y=cnt2.values, marker_color="#2563EB",
            text=cnt2.values, textposition="outside", showlegend=False))
        show(finish(fig, title="가장 자주 선택된 Event 보정 모델",
                    ylab="선택된 예측 시점 수", xlab="", height=380, legend=False,
                    footnote="학습 데이터 내부 CV 로만 선택 · 최종 Test 미사용"))

    st.divider()
    with st.expander("V3 에서는 왜 Event 효과를 분리할 수 없었나 (historical)"):
        cdf = D["contrib"]
        fig = go.Figure()
        for stage in ("M2_V2", "M2_V3"):
            g = cdf[cdf["stage"] == stage].copy()
            g["month"] = pd.to_datetime(g["target_month"] + "-01")
            fig.add_scatter(x=g["month"], y=g["direct_event_contribution"],
                            name=LABEL[stage],
                            line=dict(color=COLORS[stage], width=2))
        show(finish(fig, title="V3 의 직접 Event 기여분 (계수 × 압력값)",
                    ylab="직접 기여분 (지수 Point)", xlab="대상 월",
                    footnote=FOOT_EVENT, height=380))
        st.markdown(meta["contribution_reading_md"])

# ===========================================================================
# 7. 왜 이 모델인가 (§PART O · §29)
# ===========================================================================
with tabs[7]:
    st.subheader("왜 Ridge 를 사용했나")
    st.markdown(
        "- 초기 학습 표본이 **72개월** 수준으로 작습니다.\n"
        "- 그에 비해 feature 수가 상대적으로 많습니다 (M1 기준 **22개**).\n"
        "- 시장 X 끼리 **상관이 높습니다** "
        f"(관측된 최대 상관 **{meta['m1_diagnosis']['max_abs_corr_within_X']:.2f}**).\n"
        "- 이 조건에서 규제 없는 OLS 는 계수가 불안정해집니다.\n"
        "- **Ridge 는 계수를 안정화**시켜 표본이 작을 때 과적합을 줄입니다."
    )

    st.markdown("#### 왜 다른 모델도 비교하나")
    st.markdown(
        "| 모델 | 왜 후보에 넣었나 |\n|---|---|\n"
        "| **ElasticNet** | 불필요한 변수 일부를 선택적으로 축소·제거할 수 있습니다 |\n"
        "| **PLS** | 상관이 높은 시장 X 를 소수의 잠재 산업 요인으로 압축합니다 |\n"
        "| **Bayesian Ridge** | 작은 표본에서 규제 강도를 안정적으로 추정하는 후보입니다 |\n"
        "| **Event 층의 OLS** | Event 층은 예측변수가 2~4개뿐이므로 강한 축소 없이 "
        "추가 신호를 직접 검증할 수 있습니다 |\n"
        "| **Huber** | 소수의 극단 시점에 계수가 끌려가지 않게 합니다 |"
    )
    st.info(
        "**어느 방법도 보편적으로 최고라고 말하지 않습니다.** 각 예측 시점마다 "
        "**그 시점의 과거 학습 데이터 안에서만** 후보를 비교해 선택했고, "
        "최종 Test 성능은 선택에 사용하지 않았습니다."
    )

    st.divider()
    st.markdown("#### 실제로 무엇이 선택됐나")
    sel = D["v4_selected"]
    cnt = sel["market_family"].value_counts()
    name_map = {"ridge": "Ridge", "elasticnet": "ElasticNet", "pls": "PLS",
                "bayesian_ridge": "Bayesian Ridge"}
    fig = go.Figure(go.Bar(
        x=[name_map.get(i, i) for i in cnt.index], y=cnt.values,
        marker_color="#059669", text=cnt.values, textposition="outside",
        showlegend=False))
    show(finish(
        fig, question="Q. 시장정보 보정에는 어떤 모델이 뽑혔는가?",
        title="시장정보 보정 층에서 선택된 모델 분포",
        ylab="선택된 예측 시점 수", xlab="",
        footnote="학습 데이터 내부 시간순 CV 로만 선택 · 최종 Test 미사용",
        height=400, legend=False))
    takeaway(
        f"{len(sel)}개 예측 시점에서 "
        + " · ".join(f"<b>{name_map.get(i, i)}</b> {v}회"
                     for i, v in cnt.items())
        + " 선택됐습니다. 상관이 높은 시장 X 를 소수 요인으로 압축하는 PLS 가 "
          f"{int(cnt.get('pls', 0))}회 뽑힌 것은, 12개 변수가 실제로 겹친다는 "
          "학습 데이터상의 신호입니다.")

    st.divider()
    st.markdown("#### 왜 시장 정보를 더해도 좋아지지 않았나 (실행 전 진단)")
    md = meta["m1_diagnosis"]
    a = st.columns(4)
    a[0].metric("학습행 / feature (최소)", f"{md['rows_per_feature_min']:.2f}")
    a[1].metric("시장 X 계수 수축률", f"{md['shrinkage_market']:.2f}",
                help="1.0 이면 전혀 안 눌린 것, 0 에 가까울수록 강하게 눌린 것.")
    a[2].metric("과거이력 계수 수축률", f"{md['shrinkage_hist']:.2f}")
    a[3].metric("X 를 과거이력으로 설명한 R² (최대)",
                f"{md['max_R2_X_on_hist']:.2f}")
    st.markdown(meta["m1_diagnosis_md"])

# ===========================================================================
# 8. M2 진화 (§PART S)
# ===========================================================================
with tabs[8]:
    st.subheader("Event 모델(M2)은 이렇게 진화했습니다")
    ev = meta["m2_evolution"]
    fig = go.Figure()
    fig.add_bar(x=[e["label"] for e in ev], y=[e["mae"] for e in ev],
                marker_color=["#9CA3AF", "#D97706", "#BE185D", "#DB2777"],
                text=[f"{e['mae']:.1f}" for e in ev], textposition="outside",
                showlegend=False)
    fig.add_hline(y=m("VIEW_A_OFFICIAL", "M0"), line=dict(
        color="#2563EB", width=1.6, dash="dash"))
    fig.add_annotation(xref="paper", x=0.01, y=m("VIEW_A_OFFICIAL", "M0"),
                       text=f"공식 M0 기준선 {m('VIEW_A_OFFICIAL', 'M0'):.1f}",
                       showarrow=False, yshift=12, xanchor="left",
                       font=dict(size=11.5, color="#2563EB"))
    show(finish(
        fig, question="Q. Event 모델은 단계마다 무엇을 고쳤고 무엇이 남았는가?",
        title="M2 진화 — 매 단계 진단 후 재설계  "
              "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
        ylab="평균 예측오차 MAE (지수 Point)", xlab="",
        footnote=FOOT_TARGET, height=440, legend=False))
    takeaway(
        "네 단계 모두 <b>공식 M0 기준선을 넘지 못했습니다.</b> "
        "그러나 V4 에서 처음으로 <b>Event 효과와 규제 재선택 효과가 분리</b>되어, "
        "V3 에서 관측된 악화의 대부분이 Event 정보가 아니었음을 보일 수 있게 "
        "됐습니다.")

    for e in ev:
        with st.expander(f"**{e['label']}** — MAE {e['mae']:.2f} · {e['headline']}"):
            st.markdown(f"**무엇이 문제였나** — {e['problem']}")
            st.markdown(f"**Agent 진단이 찾은 것** — {e['diagnosis']}")
            st.markdown(f"**다음 단계에서 무엇을 바꿨나** — {e['next_change']}")

# ===========================================================================
# 9. Clean-PIT
# ===========================================================================
with tabs[9]:
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
        f"레지스트리 로더가 **거부**합니다.")
    st.divider()
    st.markdown("#### V4 가 추가로 지킨 규칙 — Prequential 잔차")
    st.markdown(meta["v4_prequential_md"])

# ===========================================================================
# 10. Agent Team (§PART R)
# ===========================================================================
with tabs[10]:
    st.subheader("Claude Code Agent Team 구성")
    st.markdown(
        "**한 모델에게 모든 업무를 한 번에 시킨 것이 아니라, 프로젝트를 역할별로 "
        "분해하고 전문 Agent 가 각 업무를 수행하도록 구성했습니다.**"
    )
    p = ASSETS / "agent_team.png"
    if p.exists():
        st.image(str(p), width="stretch")

    st.markdown("#### 실제 Agent 구성과 역할")
    team = meta["agent_team"]
    for grp in team["groups"]:
        st.markdown(f"##### {grp['title']}")
        cols = st.columns(len(grp["agents"]))
        for col, ag in zip(cols, grp["agents"]):
            with col:
                st.markdown(
                    f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
                    f"border-radius:8px;padding:14px;height:100%'>"
                    f"<b style='font-size:15px'>{ag['role_ko']}</b><br>"
                    f"<code style='font-size:11px'>{ag['name']}</code>"
                    f"<span style='font-size:11px;color:#6B7280'> · "
                    f"{ag['model']}</span>"
                    f"<hr style='margin:8px 0;border-color:#E2E8F0'>"
                    f"<b style='font-size:12px;color:#6B7280'>RESPONSIBILITY</b>"
                    f"<br><span style='font-size:13px'>{ag['responsibility']}</span>"
                    f"<br><br>"
                    f"<b style='font-size:12px;color:#6B7280'>REPRESENTATIVE TASKS</b>"
                    f"<br><span style='font-size:13px'>"
                    + "<br>".join(f"· {t}" for t in ag["tasks"]) +
                    f"</span><br><br>"
                    f"<b style='font-size:12px;color:#6B7280'>REPRESENTATIVE OUTPUTS</b>"
                    f"<br><span style='font-size:12.5px;color:#374151'>"
                    + "<br>".join(f"· <code>{o}</code>" for o in ag["outputs"]) +
                    "</span></div>", unsafe_allow_html=True)
        st.write("")

    st.divider()
    st.markdown("#### 공유 규칙(Skill)로 원칙을 강제했습니다")
    st.dataframe(pd.DataFrame(team["skills"]), hide_index=True, width="stretch")

    st.divider()
    st.markdown("#### 작업 흐름")
    st.markdown(
        " → ".join(f"**{s}**" for s in team["workflow"])
    )
    st.markdown(meta["claude_code_md"])

st.divider()
st.caption(
    f"공식 실행 커밋 `{meta['git_commit'][:12]}` · "
    f"사전등록 해시 `{meta['preregistration_sha256'][:12]}` · "
    f"동결 데이터 해시 `{meta['freeze_manifest_sha256'][:12]}` · "
    f"V3 registry `{v3['registry_version']}` / rubric `{v3['rubric_version']}` · "
    f"V4 동결 `{v4['freeze_version']}` · 생성 {meta['exported_at']}"
)
