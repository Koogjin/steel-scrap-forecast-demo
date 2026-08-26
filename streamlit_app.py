"""미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo — presentation layer (V5).

이 앱은 **저장된 결과만 읽는다.** 연구 파이프라인을 다시 돌리지 않는다:
원문 데이터를 내려받지 않고, PIT 패널을 재구성하지 않고, 사건을 수집하지 않고,
모델을 학습하지 않고, 외부 API 를 호출하지 않는다.

## V5 의 설계 원칙 — Executive vs Research 분리 (§PART I)

이전 버전은 **과학적으로는 완전했지만 시각적으로 과부하**였다. 10개 모델이 기본
화면에 동시에 떠 있었다.

V5 는 둘을 분리한다.

    기본 화면(Executive)   M0 / M1* / M2* **세 개만**. 30초 안에 핵심이 읽힌다.
    Research Archive       V1~V5 전체 실험을 **하나도 지우지 않고** 접어서 보관.

연구 결과는 전부 보존된다. 다만 **모든 실험이 기본 화면에서 같은 크기로 보일
필요는 없다.**

## 스크린샷 규약 (§PART K)

주요 차트는 개별 스크린샷으로 잘라 PowerPoint 에 붙여도 뜻이 통해야 한다.
제목이 비즈니스 질문을 말하고, 범례가 의미를 먼저 말하고, 축이 한국어이며,
각주가 **그림 안에** 들어간다.
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
# §38/§42 — 경영진용 모델 표기. 의미를 먼저, 코드는 괄호 안에.
# ---------------------------------------------------------------------------
LABEL = {
    "actual": "실제 WPU1012",
    "N0": "직전 가용치 그대로 (N0)",
    "M0": "과거 PPI 기반 (M0)",
    "M1_star": "시장·산업 정보 추가 (M1*)",
    "ME_star": "Event 정보만 추가 (ME*)",
    "M2_star": "공식 Event 정보 추가 (M2*)",
    "M1_official": "시장·산업 정보 추가 (M1, 구버전)",
    "M2_V2": "공식 Event 확장 V2 (M2-V2)",
    "M2_V3": "Event 표현 고도화 V3 (M2-V3)",
    "M1R": "시장정보 보정 V4 (M1-R)",
    "M2R": "Event 정보 보정 V4 (M2-R)",
    "M0_ctrl": "과거 PPI 기반 · 통제 (M0)",
    "M1_ctrl": "시장·산업 정보 · 통제 (M1)",
    "ME_ctrl": "Event 정보만 · 통제 (ME)",
    "M2_ctrl": "시장 + Event · 통제 (M2)",
}
COLORS = {"actual": "#111827", "N0": "#9CA3AF", "M0": "#2563EB",
          "M1_star": "#0D9488", "ME_star": "#F59E0B", "M2_star": "#DB2777",
          "M1_official": "#059669", "M2_V2": "#D97706", "M2_V3": "#BE185D",
          "M1R": "#0891B2", "M2R": "#7C3AED",
          "M0_ctrl": "#2563EB", "M1_ctrl": "#0D9488", "ME_ctrl": "#F59E0B",
          "M2_ctrl": "#DB2777"}
UP_COLOR, DOWN_COLOR = "#DC2626", "#2563EB"

#: §42 — 스크린샷이 홀로 돌아다녀도 문맥이 남도록 그림 **안에** 넣는 각주.
FOOT_TARGET = ("Target: BLS WPU1012 — Iron and steel scrap PPI  ·  "
               "주의: 실제 $/ton 거래가격이 아니라 미국 철·강 스크랩 생산자물가지수")
FOOT_EVENT = ("PEP/NEP: 공식 Event 를 경제적 전달경로에 따라 구조화한 상·하방 "
              "pressure score이며 확률이 아닙니다")

st.set_page_config(page_title="철·강 스크랩 PPI 예측 Demo",
                   page_icon="🏭", layout="wide")


@st.cache_data
def load():
    d = {}
    for key, name in (
        ("v5_metrics", "demo_v5_metrics.csv"),
        ("v5_preds", "demo_v5_predictions.csv"),
        ("v5_sel", "demo_v5_selected_models.csv"),
        ("v5_attr", "demo_v5_event_attribution.csv"),
        ("v5_cmp", "demo_v5_comparisons.csv"),
        ("channels", "event_channel_panel_v5.csv"),
        ("v6_metrics", "demo_v6_metrics.csv"),
        ("v6_support", "demo_v6_support.csv"),
        ("v6_comparisons", "demo_v6_comparisons.csv"),
        ("v6_selected", "demo_v6_selected_models.csv"),
        ("x_registry", "x_feature_registry.csv"),
        ("official_metrics", "metrics.csv"),
        ("v3_metrics", "demo_v3_metrics.csv"),
        ("v4_metrics", "demo_v4_metrics.csv"),
        ("episodes", "event_episode_registry_v3.csv"),
        ("transitions", "event_transition_registry_v3.csv"),
        ("pressure_v3", "pep_nep_v3.csv"),
        ("cat_state", "event_monthly_category_state_v3.csv"),
    ):
        d[key] = pd.read_csv(DATA / name)
    d["meta"] = json.loads((DATA / "run_metadata.json").read_text(encoding="utf-8"))
    return d


D = load()
meta = D["meta"]
tgt = meta["target"]
k = meta["kpi"]
v3 = meta["demo_v3"]
v5 = meta["demo_v5"]
v6 = meta["demo_v6"]
OPS = v5["operational"]
CTRL = v5["controlled"]


# ---------------------------------------------------------------------------
# 차트 헬퍼 — §PART K 규약을 한 곳에서 강제한다
# ---------------------------------------------------------------------------

def finish(fig: go.Figure, *, title: str, question: str | None = None,
           ylab: str = "", xlab: str = "", footnote: str | None = None,
           height: int = 430, legend: bool = True,
           yrange: list | None = None) -> go.Figure:
    head = f"<b>{title}</b>"
    if question:
        head = (f"<span style='font-size:12px;color:#6B7280'>{question}</span>"
                f"<br>{head}")
    fig.update_layout(
        title=dict(text=head, x=0.0, xanchor="left", y=0.96, yanchor="top",
                   font=dict(size=17, color="#111827")),
        height=height, yaxis_title=ylab, xaxis_title=xlab,
        hovermode="x unified",
        margin=dict(t=96 if question else 78, b=66 if footnote else 44,
                    l=64, r=24),
        font=dict(size=13), plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.005, xanchor="left",
                    x=0.0, font=dict(size=12.5)) if legend else None,
        showlegend=legend)
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
    st.markdown(
        f"<div style='background:#F8FAFC;border-left:4px solid #2563EB;"
        f"padding:10px 14px;margin:6px 0 18px 0;border-radius:4px;"
        f"font-size:14px;line-height:1.6'>"
        f"<b style='color:#2563EB'>핵심 해석</b><br>{text}</div>",
        unsafe_allow_html=True)


def reading_guide(how: str, now: str, caution: str) -> None:
    """§41 — 이 그래프를 보는 법 / 현재 결과 해석 / 해석 시 주의."""
    with st.expander("이 그래프를 보는 법"):
        st.markdown(f"**보는 법** — {how}")
        st.markdown(f"**현재 결과 해석** — {now}")
        st.markdown(f"**해석 시 주의** — {caution}")


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def mae(view: str, model: str) -> float:
    r = D["v5_metrics"]
    return float(r[(r["view"] == view) & (r["model"] == model)]["mae"].iloc[0])


N0 = mae("OFFICIAL_REFERENCE", "N0")

# ---------------------------------------------------------------------------
# 헤더
# ---------------------------------------------------------------------------
st.title("미국 철·강 스크랩 생산자물가지수(PPI) 예측 Demo")
st.markdown(f"#### BLS {tgt['series_id']} — {tgt['name_en']}")
st.markdown(
    "> **쉽게 말하면, 미국 철·강 스크랩 시장의 전반적인 생산자 가격 움직임을 "
    "보여주는 BLS 공식 가격지수입니다.**  \n"
    "> 각 과거 시점에 실제로 공개되어 있던 정보만 사용해서 다음 달을 예측했습니다."
)

tabs = st.tabs([
    "📌 Executive Summary",
    "🎯 예측 대상 & 데이터",
    "🌍 Event Intelligence",
    "🤖 Agent Team",
    "🗂️ 연구 과정 (Research Archive)",
])

# ===========================================================================
# 1. EXECUTIVE SUMMARY  (§27-§33)
# ===========================================================================
with tabs[0]:
    d_m1 = 100.0 * (OPS["M1_star"] / OPS["M0"] - 1.0)
    d_m2 = 100.0 * (OPS["M2_star"] / OPS["M0"] - 1.0)

    c = st.columns(4)
    c[0].metric("과거 PPI 기반 (M0)", f"{OPS['M0']:.2f}", help="MAE ↓ 낮을수록 정확")
    c[1].metric("시장·산업 정보 추가 (M1*)", f"{OPS['M1_star']:.2f}",
                delta=f"{d_m1:+.1f}%", delta_color="inverse")
    c[2].metric("공식 Event 정보 추가 (M2*)", f"{OPS['M2_star']:.2f}",
                delta=f"{d_m2:+.1f}%", delta_color="inverse")
    c[3].metric("예측 시점", f"{k['n_origins']}개",
                help="같은 시점·같은 학습행·같은 대상월로 모든 모델을 비교했습니다")

    st.markdown(meta["executive_takeaway_md"])
    st.info(meta["executive_caveat_md"])

    # ---- 주 성능 차트: 세 모델만 (§28) --------------------------------
    st.divider()
    order = ["M0", "M1_star", "M2_star"]
    vals = [OPS[m] for m in order]
    best = int(min(range(3), key=lambda i: vals[i]))
    fig = go.Figure()
    for i, m in enumerate(order):
        fig.add_bar(x=[LABEL[m]], y=[vals[i]], showlegend=False,
                    marker_color=COLORS[m], text=[f"{vals[i]:.2f}"],
                    textposition="outside", textfont=dict(size=13),
                    hovertemplate=f"{LABEL[m]}<br>MAE %{{y:.2f}}<extra></extra>")
    fig.add_hline(y=N0, line=dict(color="#9CA3AF", width=1.4, dash="dash"))
    fig.add_annotation(xref="paper", x=0.99, y=N0, xanchor="right",
                       text=f"단순 기준선 N0 {N0:.1f}", showarrow=False, yshift=11,
                       font=dict(size=11, color="#6B7280"))
    fig.add_annotation(x=LABEL[order[best]], y=vals[best],
                       text="가장 낮은 평균오차", showarrow=True, arrowhead=0,
                       ax=0, ay=-46, font=dict(size=11.5, color="#111827"),
                       bgcolor="rgba(255,255,255,0.85)")
    fig.update_yaxes(range=[0, max(vals + [N0]) * 1.22])
    show(finish(
        fig,
        question="Q. 시장·Event 정보를 추가하면 예측 정확도가 좋아지는가?",
        title="시장·Event 정보를 추가하면 예측 정확도가 좋아지는가?  "
              "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
        ylab="평균 예측오차 MAE (지수 Point)", xlab="",
        footnote=FOOT_TARGET, height=470, legend=False))
    takeaway(
        f"<b>{LABEL[order[best]]}</b> 가 가장 낮은 평균오차 "
        f"({vals[best]:.2f})를 보였습니다. "
        f"시장 정보는 M0 대비 <b>{abs(d_m1):.1f}% "
        f"{'개선' if d_m1 < 0 else '악화'}</b>, "
        f"Event 정보까지 더하면 <b>{abs(d_m2):.1f}% "
        f"{'개선' if d_m2 < 0 else '악화'}</b> 입니다.")
    reading_guide(
        "막대가 낮을수록 예측이 정확합니다. 점선은 '지난달 값을 그대로 쓰는' "
        "단순 기준선입니다.",
        f"시장 정보를 더한 M1* 가 M0 보다 조금 낮고, Event 를 더한 M2* 는 "
        f"오히려 높습니다.",
        "차이가 작고 예측 시점이 50개뿐이라 **통계적으로 유의하지 않습니다.** "
        "'유의하지 않음'과 '효과 없음'은 다릅니다.")

    # ---- 모델 스토리 (§29) --------------------------------------------
    st.divider()
    st.markdown("#### 모델은 이렇게 정보를 쌓습니다")
    p = ASSETS / "model_story.png"
    if p.exists():
        st.image(str(p), width="stretch")
    a, b, cc = st.columns(3)
    a.markdown("**M0 — 과거 PPI 정보**  \n가격 자체가 가진 정보")
    b.markdown("**M1\\* — + 시장·산업 정보**  \n시장이 추가로 설명한 부분")
    cc.markdown("**M2\\* — + 공식 Event 정보**  \nEvent 가 추가로 설명한 부분")

    # ---- 실제 vs 예측 (최대 4선, §30) ---------------------------------
    st.divider()
    dd = D["v5_preds"].copy()
    dd["month"] = pd.to_datetime(dd["target_month"] + "-01")
    fig = go.Figure()
    fig.add_scatter(x=dd["month"], y=dd["y_true"], name=LABEL["actual"],
                    line=dict(color=COLORS["actual"], width=3.2))
    for m in ("M0", "M1_star", "M2_star"):
        fig.add_scatter(x=dd["month"], y=dd[m], name=LABEL[m],
                        line=dict(color=COLORS[m], width=2,
                                  dash="dot" if m == "M2_star" else None))
    show(finish(
        fig,
        question="Q. 실제 지수의 급등·급락을 어떤 모델이 더 잘 따라갔는가?",
        title="각 모델은 실제 철·강 스크랩 PPI 움직임을 얼마나 따라가는가",
        ylab="PPI 지수 (1982-06 = 100)", xlab="대상 월",
        footnote=FOOT_TARGET, height=500))
    reading_guide(
        "검은 선이 실제 지수입니다. 모델 선이 검은 선에 가까울수록 잘 맞힌 것입니다.",
        "세 모델이 큰 흐름은 비슷하게 따라가며, 급변 구간에서 차이가 벌어집니다.",
        "**선이 가까워 보이는 것과 통계적으로 유의한 개선은 다릅니다.**")

    # ---- 2x2 (§33) ----------------------------------------------------
    st.divider()
    st.markdown("#### 시장 정보와 Event 정보는 각각 도움이 되었는가?")
    tb = v5["two_by_two"]
    grid = [[OPS["M0"], OPS["ME_star"]], [OPS["M1_star"], OPS["M2_star"]]]
    names = [["M0", "ME*"], ["M1*", "M2*"]]
    fig = go.Figure(go.Heatmap(
        z=grid, x=["Event 없음", "Event 있음"], y=["시장 없음", "시장 있음"],
        colorscale="RdYlGn_r", showscale=True,
        colorbar=dict(title="MAE"), hovertemplate="%{y} / %{x}<br>MAE %{z:.2f}<extra></extra>"))
    for i in range(2):
        for j in range(2):
            fig.add_annotation(
                x=["Event 없음", "Event 있음"][j], y=["시장 없음", "시장 있음"][i],
                text=f"<b>{names[i][j]}</b><br>{grid[i][j]:.2f}",
                showarrow=False, font=dict(size=15, color="#111827"))
    show(finish(
        fig, question="Q. 시장과 Event 가 각각 도움이 되었는가?",
        title="2×2 정보 실험  "
              "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확 · "
              "초록이 좋고 빨강이 나쁨</span>",
        ylab="", xlab="", footnote=FOOT_TARGET, height=380, legend=False))
    takeaway(
        f"시장 정보를 넣으면 오차가 줄고(M0 {OPS['M0']:.2f} → M1* "
        f"{OPS['M1_star']:.2f}), Event 정보를 넣으면 오차가 늘어납니다 "
        f"(M0 → ME* {OPS['ME_star']:.2f}, M1* → M2* {OPS['M2_star']:.2f}). "
        "네 칸 모두 같은 예측 시점·같은 학습 데이터로 계산했습니다.")
    reading_guide(
        "왼쪽 위가 가장 단순한 모델, 오른쪽 아래가 정보를 가장 많이 쓴 모델입니다. "
        "위→아래는 시장 정보 추가, 왼→오른쪽은 Event 정보 추가입니다.",
        "**시장 정보만 아래쪽으로 갈 때 오차가 줄어듭니다.** Event 정보는 어느 "
        "방향에서든 오차를 늘렸습니다.",
        "칸 사이 차이가 작습니다. Event 추가의 악화만이 통제 비교에서 "
        "통계적으로 뚜렷했습니다.")

# ===========================================================================
# 2. 예측 대상 & 데이터  (§PART M)
# ===========================================================================
with tabs[1]:
    st.subheader("무엇을 예측하나")
    st.markdown(meta["target_explainer_md"])

    st.divider()
    st.markdown("#### 지수를 읽는 법")
    a, b = st.columns(2)
    a.markdown("**지수 상승 ↑**  \n전반적인 미국 철·강 스크랩 "
               "**생산자 가격 수준 상승** 방향")
    b.markdown("**지수 하락 ↓**  \n전반적인 **생산자 가격 수준 하락** 방향")
    st.error(
        "**지수 600 ≠ $600/ton 입니다.**  \n"
        "예: 500 → 550 은 **약 10% 지수 상승**이지 **$50/ton 상승이 아닙니다.** "
        "지수 차이는 항상 **변화율**로 읽습니다.")
    st.warning(
        "본 Demo는 특정 기업의 구매가격, 특정 스크랩 grade 의 거래가격, "
        "또는 $/ton 현물가격을 예측하는 모델이 **아닙니다**.")

    st.divider()
    st.subheader("어떤 시장·산업 데이터를 쓰나")
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
        "생성한 것입니다.")

    st.markdown("#### 원천지표 설명")
    xr = D["x_registry"]
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
        "아닙니다. 공식 계열명·출처는 프로젝트 registry 에 기록된 값입니다.")

    with st.expander("왜 이 6개인가"):
        st.markdown(
            "단순히 상관이 높은 변수를 넣은 것이 아닙니다. Primary 모델에는 다음 "
            "조건을 **모두** 만족한 Clean-PIT 계열만 사용했습니다.\n\n"
            "- **원기관 원문 출처** — 재배포 플랫폼이 아니라 BLS · Federal Reserve 원문\n"
            "- **충분한 과거 커버리지** — 학습에 필요한 기간이 실제로 존재\n"
            "- **Point-in-Time 재구성 가능** — 그 시점에 발표되어 있던 값을 복원 가능\n"
            "- **발표일 검증** · **개정(revision) 처리** · **매월 재현 가능**\n"
            "- **공개 배포 안전성** — 저작권·이용약관상 공개 Demo 에 적합")
        st.info(meta["x_explainer"]["historical_only_note"])
        st.success(f"이번 단계에서도 **새로운 외부 데이터 소스를 추가하지 "
                   f"않았습니다** — {meta['x_explainer']['future_work_note']}")

    st.divider()
    st.markdown("#### 왜 Clean-PIT 인가")
    a, b = st.columns(2)
    a.markdown("**⚠️ 기존 방식의 위험**  \n과거를 모델링할 때 **현재 최종 수정된 "
               "과거 데이터**를 쓰면, 그 시점에는 알 수 없었던 정보가 모델에 "
               "들어갑니다. 경제지표는 최초 발표 후 여러 차례 개정됩니다.")
    b.markdown(f"**✅ 본 프로젝트의 방식**  \n2023년 시점을 예측할 때 2026년에 "
               f"수정된 최종 {tgt['series_id']} 값을 쓰는 것이 아니라, 당시 실제로 "
               "공개되어 있던 값만 사용합니다.")
    st.dataframe(pd.DataFrame(meta["revision_examples"]), hide_index=True,
                 width="stretch")

# ===========================================================================
# 3. EVENT INTELLIGENCE  (§PART L)
# ===========================================================================
with tabs[2]:
    st.subheader("공식 Event 정보는 예측에 무엇을 더하는가")
    st.markdown(meta["v5_event_md"])

    q = st.columns(4)
    ev_m2 = v5["event_m2"]
    q[0].metric("Event 를 쓴 예측시점", f"{ev_m2['event_used_pct']:.0f}%",
                help="나머지는 모델이 학습 근거를 보고 쓰지 않기로 선택했습니다")
    q[1].metric("중앙값 보정폭", f"{ev_m2['median_abs_impact']:.1f}",
                help="지수 Point. 0 이면 예측이 전혀 안 움직였다는 뜻입니다")
    q[2].metric("공식 사건", f"{v3['n_episodes']}건 / {v3['n_transitions']}상태")
    q[3].metric("V4 대비 개선",
                f"{100 * (1 - OPS['M2_star'] / mae('HISTORICAL_DEMO', 'M2R')):+.0f}%",
                help="V4 의 Event 모델(M2-R) 대비 MAE 개선")

    # =======================================================================
    # §27/§28/§34 — Event 는 어디에서 가장 유용한가? (V6 예측역할 연구)
    # =======================================================================
    st.divider()
    st.markdown("### Event는 어디에서 가장 유용한가?")
    st.markdown(
        "Event 정보가 **다음 달 지수 수준**을 맞히지 못한다는 것은 이미 확인했습니다. "
        "그렇다면 **방향**, **큰 변동**, **전환점** 같은 다른 질문에는 도움이 될까요? "
        "V6 는 이 세 가지를 각각 사전등록해 시험했습니다."
    )

    # ---- §34 네 개의 역할 카드 ----------------------------------------
    cards = st.columns(4)
    VCOLOR = {"개선": "#059669", "악화": "#DC2626", "결론 유보": "#6B7280"}
    for col, card in zip(cards, v6["role_cards"]):
        v = card["verdict"]
        p = card.get("p_value")
        pstr = (f"<br><span style='font-size:11.5px;color:#9CA3AF'>"
                f"p = {p:.3f}</span>" if p is not None else "")
        col.markdown(
            f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
            f"border-left:5px solid {VCOLOR[v]};border-radius:8px;padding:14px;"
            f"height:100%'>"
            f"<span style='font-size:12.5px;color:#6B7280'>{card['label']}</span>"
            f"<br><b style='font-size:20px;color:{VCOLOR[v]}'>{v}</b>"
            f"<br><span style='font-size:12.5px;color:#374151'>"
            f"{card['detail']}</span>"
            f"<br><span style='font-size:11.5px;color:#9CA3AF'>"
            f"{card['metric']}</span>{pstr}</div>",
            unsafe_allow_html=True)
    st.caption(
        "각 카드는 **시장 정보 위에 Event 를 더했을 때의 변화**입니다. "
        "네 가지를 하나의 점수로 합치지 않습니다 — 예측 역할마다 질문이 다릅니다.")

    # ---- §28 역할 선택기 — 한 번에 하나만 -----------------------------
    role_view = st.radio(
        "어떤 예측 역할을 볼까요?",
        ["Level (지수 수준)", "Direction (방향)", "Large Move (큰 변동)",
         "Turning Point (전환점)"],
        index=1, horizontal=True, key="v6_role")

    v6m = D["v6_metrics"]
    v6s = D["v6_support"]

    def _val(role, h, cell, metric):
        s = v6m[(v6m["role"] == role) & (v6m["horizon"] == h)
                & (v6m["cell"] == cell)]
        if s.empty or pd.isna(s[metric].iloc[0]):
            return None
        return float(s[metric].iloc[0])

    # ================= LEVEL (§29) =====================================
    if role_view.startswith("Level"):
        st.markdown("#### 지수 수준 예측 — V5 에서 동결된 결과")
        order = ["M0", "M1_star", "M2_star"]
        vals = [OPS[m] for m in order]
        fig = go.Figure()
        for m, v in zip(order, vals):
            fig.add_bar(x=[LABEL[m]], y=[v], showlegend=False,
                        marker_color=COLORS[m], text=[f"{v:.2f}"],
                        textposition="outside", textfont=dict(size=13))
        show(finish(
            fig, question="Q. Event 정보가 다음 달 지수 수준을 더 잘 맞히는가?",
            title="Event 정보는 지수 수준 예측을 개선하지 못했다  "
                  "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
            ylab="평균 예측오차 MAE (지수 Point)", xlab="",
            footnote=FOOT_TARGET, height=420, legend=False))
        takeaway(
            f"시장 정보를 더한 M1\\* ({OPS['M1_star']:.2f})가 가장 정확했고, "
            f"공식 Event 정보를 더한 M2\\* 는 {OPS['M2_star']:.2f} 로 "
            "<b>더 나빠졌습니다.</b> 이 결과는 V5 에서 동결되어 바뀌지 않습니다.")

    # ================= DIRECTION (§30) =================================
    elif role_view.startswith("Direction"):
        st.markdown("#### 방향 예측 — **1개월이 1차 가설입니다**")
        st.caption(
            "사전등록된 우선순위: **PRIMARY = 1개월** · 확인용 = 2개월 · 3개월. "
            "나중에 결과가 좋은 기간을 골라 primary 라고 부르지 않습니다.")

        fig = go.Figure()
        hs = [1, 2, 3]
        fig.add_bar(x=[f"{h}개월" for h in hs],
                    y=[_val("direction", h, "D1", "balanced_accuracy") for h in hs],
                    name="시장 정보만 (M1)", marker_color=COLORS["M1_star"],
                    text=[f"{_val('direction', h, 'D1', 'balanced_accuracy'):.3f}"
                          for h in hs], textposition="outside")
        fig.add_bar(x=[f"{h}개월" for h in hs],
                    y=[_val("direction", h, "D2", "balanced_accuracy") for h in hs],
                    name="시장 + Event 정보 (M2)", marker_color=COLORS["M2_star"],
                    text=[f"{_val('direction', h, 'D2', 'balanced_accuracy'):.3f}"
                          for h in hs], textposition="outside")
        fig.add_hline(y=0.5, line=dict(color="#9CA3AF", width=1.4, dash="dash"))
        fig.add_annotation(xref="paper", x=0.99, y=0.5, xanchor="right",
                           text="동전 던지기 0.50", showarrow=False, yshift=11,
                           font=dict(size=11, color="#6B7280"))
        fig.add_annotation(x="1개월", y=0.02, yref="y",
                           text="◀ PRIMARY", showarrow=False,
                           font=dict(size=12, color="#111827"))
        fig.update_layout(barmode="group")
        show(finish(
            fig, question="Q. Event 정보가 향후 가격 방향 예측을 개선하는가?",
            title="Event 정보가 향후 가격 방향 예측을 개선하는가?  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "Balanced Accuracy ↑ 높을수록 정확 · 0.50 = 동전 던지기</span>",
            ylab="방향 정확도 (Balanced Accuracy)", xlab="예측 기간",
            footnote=FOOT_TARGET + "  ·  PRIMARY = 1개월 (사전등록된 우선순위)",
            height=460))
        pc = v6["primary_comparison"]
        takeaway(
            f"1차 가설인 <b>1개월 방향</b>에서 Event 를 더하면 정확도가 "
            f"<b>{pc['diff']:+.3f}</b> 변합니다 "
            f"(95% 구간 [{pc['ci_low']:.3f}, {pc['ci_high']:.3f}], "
            f"p = {pc['p_value']:.3f}). <b>개선의 증거가 없습니다.</b>")
        reading_guide(
            "막대가 높을수록 방향을 잘 맞힌 것입니다. 점선(0.50)은 동전 던지기 "
            "수준입니다.",
            "1개월에서 시장 정보만 쓴 모델이 가장 높고, Event 를 더하면 오히려 "
            "낮아집니다.",
            "예측 시점이 50개뿐이라 이 차이는 **통계적으로 유의하지 않습니다.** "
            "3개월 결과가 달라 보여도 **확인용 기간**이며 1차 가설을 대체하지 않습니다.")

        with st.expander("2×2 상세 — 시장·Event 를 각각 켜고 끄면"):
            grid = [[_val("direction", 1, "D0", "balanced_accuracy"),
                     _val("direction", 1, "DE", "balanced_accuracy")],
                    [_val("direction", 1, "D1", "balanced_accuracy"),
                     _val("direction", 1, "D2", "balanced_accuracy")]]
            names = [["M0", "ME"], ["M1", "M2"]]
            fig = go.Figure(go.Heatmap(
                z=grid, x=["Event 없음", "Event 있음"],
                y=["시장 없음", "시장 있음"], colorscale="RdYlGn",
                colorbar=dict(title="정확도"),
                hovertemplate="%{y} / %{x}<br>%{z:.3f}<extra></extra>"))
            for i in range(2):
                for j in range(2):
                    fig.add_annotation(
                        x=["Event 없음", "Event 있음"][j],
                        y=["시장 없음", "시장 있음"][i],
                        text=f"<b>{names[i][j]}</b><br>{grid[i][j]:.3f}",
                        showarrow=False, font=dict(size=14, color="#111827"))
            show(finish(
                fig, question="Q. 시장과 Event 가 각각 방향 예측에 기여했는가?",
                title="1개월 방향 — 2×2 정보 실험  "
                      "<span style='font-size:13px;color:#6B7280'>"
                      "Balanced Accuracy ↑ 높을수록 정확</span>",
                ylab="", xlab="", footnote=FOOT_TARGET, height=360,
                legend=False))
            st.caption(
                "시장 정보를 넣으면 위→아래로 정확도가 올라가고, Event 정보를 "
                "넣으면 왼→오른쪽으로 내려갑니다.")

    # ================= LARGE MOVE (§31) ================================
    elif role_view.startswith("Large"):
        st.markdown("#### 큰 가격변동 감지")
        st.caption(
            "‘큰 변동’은 각 시점의 **과거 데이터만으로** 정한 기준(상위 25%)을 "
            "넘는 움직임입니다. 정답을 보고 기준을 정하지 않았습니다.")
        hs = [1, 2, 3]
        fig = go.Figure()
        fig.add_bar(x=[f"{h}개월" for h in hs],
                    y=[_val("large_move", h, "D1", "pr_auc") for h in hs],
                    name="시장 정보만 (M1)", marker_color=COLORS["M1_star"],
                    text=[f"{_val('large_move', h, 'D1', 'pr_auc'):.3f}"
                          for h in hs], textposition="outside")
        fig.add_bar(x=[f"{h}개월" for h in hs],
                    y=[_val("large_move", h, "D2", "pr_auc") for h in hs],
                    name="시장 + Event 정보 (M2)", marker_color=COLORS["M2_star"],
                    text=[f"{_val('large_move', h, 'D2', 'pr_auc'):.3f}"
                          for h in hs], textposition="outside")
        fig.update_layout(barmode="group")
        show(finish(
            fig, question="Q. Event 정보가 큰 가격변동을 미리 감지하는가?",
            title="Event 정보가 큰 가격변동을 미리 감지하는가?  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "PR-AUC ↑ 높을수록 잘 감지</span>",
            ylab="큰 변동 감지력 (PR-AUC)", xlab="예측 기간",
            footnote=FOOT_TARGET + "  ·  PRIMARY = 1개월", height=440))
        c = next((x for x in v6["role_cards"] if x["role"] == "large_move"), None)
        takeaway(
            f"1개월 기준으로 Event 를 더하면 감지력이 "
            f"<b>{c['diff']:+.3f}</b> 변합니다 (p = {c['p_value']:.3f}). "
            "<b>개선되지 않았습니다.</b>")

    # ================= TURNING POINT (§32) =============================
    else:
        st.markdown("#### 상승↔하락 전환 감지")
        sup = v6s[(v6s["role"] == "turning_point") & (v6s["horizon"] == 1)]
        verdict = sup["verdict"].iloc[0] if not sup.empty else "UNDERPOWERED"
        if verdict != "OK":
            st.warning("**표본 부족 — 결론 유보.** 전환점 사례가 통계적으로 "
                       "판단하기에 충분하지 않았습니다.")
        else:
            n_pos = int(sup["n_positive"].iloc[0])
            n_neg = int(sup["n_negative"].iloc[0])
            cells = ["D0", "D1", "DE", "D2"]
            lbl = {"D0": "과거 PPI 기반 (M0)", "D1": "시장 정보 (M1)",
                   "DE": "Event 정보 (ME)", "D2": "시장 + Event (M2)"}
            vals = [_val("turning_point", 1, c, "balanced_accuracy")
                    for c in cells]
            fig = go.Figure()
            for c, v in zip(cells, vals):
                fig.add_bar(x=[lbl[c]], y=[v], showlegend=False,
                            marker_color="#9CA3AF" if v < 0.5 else "#059669",
                            text=[f"{v:.3f}"], textposition="outside")
            fig.add_hline(y=0.5, line=dict(color="#DC2626", width=1.6,
                                           dash="dash"))
            fig.add_annotation(xref="paper", x=0.99, y=0.5, xanchor="right",
                               text="동전 던지기 0.50", showarrow=False,
                               yshift=11, font=dict(size=11, color="#DC2626"))
            show(finish(
                fig, question="Q. Event 정보가 상승↔하락 전환을 감지하는가?",
                title="Event 정보가 상승↔하락 전환을 감지하는가?  "
                      "<span style='font-size:13px;color:#6B7280'>"
                      "Balanced Accuracy ↑ 높을수록 정확</span>",
                ylab="전환 감지 정확도 (Balanced Accuracy)", xlab="",
                footnote=f"전환 사례 {n_pos}건 / 비전환 {n_neg}건 — 표본은 "
                         f"충분했습니다.  ·  {FOOT_TARGET}",
                height=440, legend=False))
            takeaway(
                f"<b>모든 모델이 동전 던지기(0.50)보다 낮습니다.</b> 전환 사례가 "
                f"{n_pos}건으로 표본은 충분했으므로, 이것은 표본 부족이 아니라 "
                "<b>이 데이터에서 전환점 자체가 예측되지 않는다</b>는 뜻입니다. "
                "Event 를 더하면 더 낮아집니다.")

    # ---- §33 Event 표현 설명 -------------------------------------------
    st.divider()
    with st.expander("Event 정보를 모델에 넣는 다섯 가지 방식"):
        st.markdown(
            "- **STATE (상태)** — 현재 Event 환경. 지금 어떤 상·하방 압력이 "
            "걸려 있는가.\n"
            "- **SHOCK (충격)** — 이번 달 Event 압력의 변화. 무엇이 **새로** "
            "바뀌었는가.\n"
            "- **TRANSITION (전이)** — 새로운 발표 / 시행 / 격화 같은 **상태 변화** "
            "그 자체.\n"
            "- **FRESHNESS (신선도)** — 최근 Event 가 얼마나 **새로운 정보**인지. "
            "몇 년째 유지 중인 조치는 신선도가 낮습니다.\n"
            "- **NOVEL EVENT (새로운 정보)** — 기존 가격·시장정보만으로는 예상되지 "
            "않던 Event 성분. 이미 아는 것과 겹치는 부분을 뺀 나머지입니다.")
        tf = v6["freshness_distribution"]
        a, b, c = st.columns(3)
        a.metric("Transition 이 발생한 달",
                 f"{v6['transition_impulse_active_pct']:.0f}%")
        b.metric("Freshness 중앙값", f"{tf['median']:.2f}")
        c.metric("Event 표현 선택",
                 " · ".join(f"{k} {v}" for k, v in
                            v6["ev_family_selection_counts"].items()))
        st.caption(
            "V6 가 새로 만든 **TRANSITION · FRESHNESS** 는 의도대로 동작했지만, "
            "학습 데이터는 이들을 넣지 않는 표현(EV-F0)을 더 자주 선택했습니다.")

    with st.expander("Event 는 학습에서만 유용해 보였는가?"):
        st.markdown(meta["v6_generalization_md"])


    # ---- 1. PEP / NEP --------------------------------------------------
    st.divider()
    st.markdown("#### 1. PEP / NEP 란 무엇인가")
    st.markdown(
        "**뉴스기사 원문 대신 공식적으로 확인된 사건·상태를 구조화하여 두 개의 "
        "압력 변수로 변환했습니다.**\n\n"
        "- **PEP ↑** — 공식 Event 근거상 **가격 상승 압력**이 강해짐\n"
        "- **NEP ↑** — 공식 Event 근거상 **가격 하락 압력**이 강해짐\n"
        "- **둘 다 높음** — 상·하방 근거가 동시에 존재하는 **상충 환경**\n"
        "- **둘 다 낮음** — 조용한 Event 환경\n\n"
        "긍/부정 뉴스 감성이 아니며, **확률이 아닙니다.** 두 지표는 독립입니다.")

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
        fig, question="Q. 공식 Event 가 가격 상·하방 압력을 얼마나 만들었는가?",
        title="공식 Event 가 가격 상·하방 압력을 얼마나 만들었는가  "
              "<span style='font-size:13px;color:#6B7280'>"
              "PEP ↑ 상방 압력 · NEP ↑ 하방 압력</span>",
        ylab="Event 압력 (0 ~ 1, 확률 아님)", xlab="월",
        footnote=FOOT_EVENT, height=420, yrange=[0, 1]))

    # ---- 2. State vs Shock --------------------------------------------
    st.divider()
    st.markdown("#### 2. Event 상태(State) vs Event 충격(Shock)")
    st.markdown(
        "같은 Event 라도 **이미 알려진 지속 상태**와 **이번 달에 새로 바뀐 것**은 "
        "다른 정보입니다.\n\n"
        "- **State** = `PEP`, `NEP` — 지금 어떤 압력 환경인가\n"
        "- **Shock** = `ΔPEP`, `ΔNEP` — 이번 달에 무엇이 **새로** 바뀌었나\n\n"
        "시장은 몇 년째 유지 중인 관세보다 **새로 발표된 조치**에 더 반응할 수 "
        "있습니다. V5 는 이 둘을 분리해 시험했습니다.")
    dd = D["v5_preds"].copy()
    dd["month"] = pd.to_datetime(dd["target_month"] + "-01")
    fig = go.Figure()
    fig.add_bar(x=dd["month"], y=dd["dPEP"], name="상방 압력 변화 (ΔPEP)",
                marker_color=UP_COLOR)
    fig.add_bar(x=dd["month"], y=dd["dNEP"], name="하방 압력 변화 (ΔNEP)",
                marker_color=DOWN_COLOR)
    fig.add_hline(y=0, line=dict(color="#6B7280", width=1.2))
    show(finish(
        fig, question="Q. Event 환경이 이번 달에 새로 바뀐 부분은 얼마인가?",
        title="Event 충격 — 전월 대비 압력 변화",
        ylab="압력 변화 (전월 대비)", xlab="대상 월",
        footnote=FOOT_EVENT, height=380))

    # ---- 3. 세 개의 거시 채널 ------------------------------------------
    st.divider()
    st.markdown("#### 3. 세 가지 경제 Event 채널")
    st.markdown(
        "하나의 PEP/NEP 쌍은 경제적으로 서로 다른 여러 메커니즘을 한데 묶습니다. "
        "그래서 **동결된 공식 사건 분류를 3개 채널로 묶어** 각각의 충격을 따로 "
        "만들었습니다.")
    ch = st.columns(3)
    for col, (cid, cats) in zip(ch, v5["channels"].items()):
        lbl = {"A_TRADE_POLICY": "철강·무역 정책",
               "B_GEO_SUPPLY": "지정학·공급",
               "C_DEMAND_MACRO": "수요·거시 충격"}[cid]
        col.markdown(f"**{lbl}**  \n" + "  \n".join(f"· {c}" for c in cats))

    cf = D["channels"].copy()
    cf["month_dt"] = pd.to_datetime(cf["month"] + "-01")
    cf = cf[cf["month_dt"] >= lo]
    fig = go.Figure()
    for cid, colr in (("A_TRADE_POLICY", "#DC2626"),
                      ("B_GEO_SUPPLY", "#2563EB"),
                      ("C_DEMAND_MACRO", "#059669")):
        lbl = {"A_TRADE_POLICY": "철강·무역 정책",
               "B_GEO_SUPPLY": "지정학·공급",
               "C_DEMAND_MACRO": "수요·거시 충격"}[cid]
        fig.add_scatter(x=cf["month_dt"], y=cf[f"net_{cid}"], name=lbl,
                        line=dict(color=colr, width=2))
    fig.add_hline(y=0, line=dict(color="#6B7280", width=1.2))
    show(finish(
        fig, question="Q. 어떤 종류의 공식 Event 가 압력을 만들었는가?",
        title="채널별 순 압력 (상방 − 하방)",
        ylab="순 Event 압력 (+상방 / −하방)", xlab="월",
        footnote=FOOT_EVENT, height=400))
    bc = v5["by_channel"]
    takeaway(
        f"철강·무역 정책과 지정학·공급 채널은 평가 구간 "
        f"<b>50개월 내내 활성</b>이고, 수요·거시 충격 채널은 "
        f"<b>{bc['C_DEMAND_MACRO']['n_active']}개월</b>만 활성입니다. "
        "따라서 <b>어떤 채널이 더 유용한지는 이 표본으로 판별할 수 없습니다.</b> "
        "월을 채우려고 사건을 만들지 않았습니다.")

    # ---- 4. Raw vs Novel ----------------------------------------------
    st.divider()
    st.markdown("#### 4. 원본 Event vs 새로운 Event 정보 (Novel)")
    st.markdown(meta["v5_novel_md"])

    # ---- 5. Event 신뢰도 (§44) -----------------------------------------
    st.divider()
    st.markdown("#### 5. 모델이 Event 정보를 얼마나 신뢰했는가")
    at = D["v5_attr"].copy()
    at["month"] = pd.to_datetime(at["target_month"] + "-01")
    fig = go.Figure()
    fig.add_bar(x=at["month"], y=at["lambda_E_M2"], showlegend=False,
                marker_color=["#DB2777" if v > 0 else "#D1D5DB"
                              for v in at["lambda_E_M2"]],
                hovertemplate="%{x|%Y-%m}<br>신뢰도 %{y:.2f}<extra></extra>")
    show(finish(
        fig, question="Q. 모델은 언제 Event 정보를 믿기로 했는가?",
        title="모델이 Event 정보를 얼마나 신뢰했는가  "
              "<span style='font-size:13px;color:#6B7280'>"
              "0 = 사용 안 함 · 0.5 = 일부만 반영 · 1 = 전부 반영</span>",
        ylab="Event 신뢰도 (0 ~ 1)", xlab="대상 월",
        footnote="신뢰도는 각 시점의 **과거 학습 데이터만으로** 결정됩니다. "
                 "최종 정답을 보고 고른 값이 아닙니다.",
        height=380, legend=False, yrange=[0, 1.05]))
    takeaway(
        f"모델은 <b>{ev_m2['no_event_fallback_pct']:.0f}% 의 예측시점에서 Event "
        f"정보를 쓰지 않기로 스스로 선택</b>했습니다. V4 에서는 Event 가 모든 "
        "시점에서 강제로 사용되어 예측을 크게 흔들었습니다 — 이 자동 fallback 이 "
        "그 노이즈를 막았습니다.")
    reading_guide(
        "분홍 막대가 높을수록 그 달에 Event 정보를 많이 반영했다는 뜻입니다. "
        "회색(0)은 아예 쓰지 않은 달입니다.",
        f"대부분의 달이 회색입니다 — 학습 데이터가 Event 사용을 지지하지 "
        f"않았습니다.",
        "신뢰도가 높다고 그 달의 예측이 맞았다는 뜻은 아닙니다.")

    # ---- 6. Event 영향 (§45) -------------------------------------------
    st.divider()
    st.markdown("#### 6. Event 정보가 최종 예측값을 얼마나 바꾸었는가")
    fig = go.Figure()
    fig.add_bar(x=at["month"], y=at["event_impact_M2"], showlegend=False,
                marker_color=[UP_COLOR if v > 0 else DOWN_COLOR
                              for v in at["event_impact_M2"]],
                hovertemplate="%{x|%Y-%m}<br>%{y:+.1f} 지수 Point<extra></extra>")
    fig.add_hline(y=0, line=dict(color="#6B7280", width=1.2))
    show(finish(
        fig, question="Q. Event 정보가 실제 예측값을 움직였는가?",
        title="Event 정보가 최종 예측값을 얼마나 바꾸었는가  "
              "<span style='font-size:13px;color:#6B7280'>"
              "+ = 더 높은 지수 예측 · − = 더 낮은 지수 예측</span>",
        ylab="Event 보정폭 (지수 Point)", xlab="대상 월",
        footnote="예측모델 내 추가 정보의 영향이며, 실제 사건의 인과효과 "
                 "추정치가 아닙니다.",
        height=400, legend=False))
    st.caption(
        "**이것은 인과효과가 아닙니다.** 예측모델 안에서 Event 변수를 추가했을 때 "
        "예측값이 얼마나 달라졌는지를 보여줄 뿐입니다.")

    with st.expander("공식 사건 목록 (전부 공식 출처)"):
        eps, trs = D["episodes"], D["transitions"]
        cats = st.multiselect("분류", sorted(eps["category_label"].unique()),
                              default=sorted(eps["category_label"].unique()),
                              key="ev_cats")
        for _, e in eps[eps["category_label"].isin(cats)].iterrows():
            mine = trs[trs["episode_id"] == e["episode_id"]].sort_values(
                "known_at_date")
            with st.expander(f"{e['episode_name']}  ·  {e['category_label']}  ·  "
                             f"상태 변화 {len(mine)}건"):
                st.markdown(f"**경제적 경로** — {e['economic_channel']}")
                for _, t in mine.iterrows():
                    st.markdown(
                        f"- `{t['known_at_date']}` **{t['stage']}**  \n"
                        f"  {t['short_summary']}  \n"
                        f"  [{t['official_source_name']}]"
                        f"({t['official_source_url']})")

    with st.expander("채점 규칙 — 결과를 보기 전에 고정했습니다"):
        st.markdown(meta["event_method_v3_md"])

# ===========================================================================
# 4. AGENT TEAM  (§PART N)
# ===========================================================================
with tabs[3]:
    st.subheader("Claude Code Agent Team 구성")
    st.markdown(
        "**한 모델에게 모든 업무를 한 번에 시킨 것이 아니라, 프로젝트를 역할별로 "
        "분해하고 전문 Agent 가 각 업무를 수행하도록 구성했습니다.**")
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
                    + "<br>".join(f"· {o}" for o in ag["outputs"]) +
                    "</span></div>", unsafe_allow_html=True)
        st.write("")

    st.divider()
    st.markdown("#### 공유 규칙(Skill)로 원칙을 강제했습니다")
    st.dataframe(pd.DataFrame(team["skills"]), hide_index=True, width="stretch")
    st.markdown("#### 작업 흐름")
    st.markdown(" → ".join(f"**{s}**" for s in team["workflow"]))
    st.markdown(meta["claude_code_md"])

# ===========================================================================
# 5. RESEARCH ARCHIVE  (§PART J)
# ===========================================================================
with tabs[4]:
    st.subheader("연구 과정 (Research Archive)")
    st.info(
        "**모든 실험 결과가 그대로 보존되어 있습니다.** 기본 화면에는 최종 세 모델만 "
        "보여주고, 중간 실험은 여기에 접어 두었습니다 — 지운 것이 아닙니다.")

    section = st.selectbox(
        "보고 싶은 항목", [
            "A. 공식 사전등록 실험 (N0 / M0 / M1)",
            "B. Event 연구 발전 과정 (V1 → V5)",
            "C. V5 통제 실험 (2×2)",
            "D. 진단 결과",
            "E. 전체 Metrics Table",
            "F. 방법론 · 산출물",
        ])

    if section.startswith("A"):
        st.markdown("결과를 보기 **전에** 규칙을 고정한 실험의 원본 결과입니다. "
                    "이후 어떤 Demo 도 이 결과를 대체하지 않습니다.")
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
            f"DM 검정 p = **{pi['dm_p']:.3f}** — 개선 증거 없음.")

    elif section.startswith("B"):
        ev = meta["m2_evolution"]
        fig = go.Figure()
        fig.add_bar(x=[e["label"] for e in ev], y=[e["mae"] for e in ev],
                    marker_color=["#9CA3AF", "#D97706", "#BE185D", "#7C3AED",
                                  "#DB2777"][:len(ev)],
                    text=[f"{e['mae']:.1f}" for e in ev],
                    textposition="outside", showlegend=False)
        fig.add_hline(y=OPS["M0"], line=dict(color="#2563EB", width=1.6,
                                             dash="dash"))
        fig.add_annotation(xref="paper", x=0.01, y=OPS["M0"], xanchor="left",
                           text=f"과거 PPI 기반 기준선 {OPS['M0']:.1f}",
                           showarrow=False, yshift=12,
                           font=dict(size=11.5, color="#2563EB"))
        show(finish(
            fig, question="Q. Event 모델은 단계마다 무엇을 고쳤는가?",
            title="Event 모델(M2) 재설계 이력  "
                  "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
            ylab="평균 예측오차 MAE (지수 Point)", xlab="",
            footnote=FOOT_TARGET, height=420, legend=False))
        for e in ev:
            with st.expander(f"**{e['label']}** — MAE {e['mae']:.2f} · "
                             f"{e['headline']}"):
                st.markdown(f"**무엇이 문제였나** — {e['problem']}")
                st.markdown(f"**Agent 진단이 찾은 것** — {e['diagnosis']}")
                st.markdown(f"**다음 단계에서 무엇을 바꿨나** — {e['next_change']}")

    elif section.startswith("C"):
        st.markdown(
            "**통제 실험**은 네 칸 모두에 같은 모형 계열을 쓰고 잡음 방어 장치를 "
            "끕니다. 정보가 늘었을 때의 순수한 효과를 보기 위한 것입니다.")
        grid = [[CTRL["M0"], CTRL["ME"]], [CTRL["M1"], CTRL["M2"]]]
        names = [["M0", "ME"], ["M1", "M2"]]
        fig = go.Figure(go.Heatmap(
            z=grid, x=["Event 없음", "Event 있음"], y=["시장 없음", "시장 있음"],
            colorscale="RdYlGn_r", colorbar=dict(title="MAE"),
            hovertemplate="%{y} / %{x}<br>MAE %{z:.2f}<extra></extra>"))
        for i in range(2):
            for j in range(2):
                fig.add_annotation(
                    x=["Event 없음", "Event 있음"][j],
                    y=["시장 없음", "시장 있음"][i],
                    text=f"<b>{names[i][j]}</b><br>{grid[i][j]:.2f}",
                    showarrow=False, font=dict(size=15, color="#111827"))
        show(finish(
            fig, question="Q. 아키텍처를 고정하면 정보 증분은 얼마인가?",
            title="V5 통제 실험 2×2  "
                  "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
            ylab="", xlab="", footnote=FOOT_TARGET, height=380, legend=False))
        st.markdown(meta["v5_market_md"])
        st.dataframe(
            pd.DataFrame([
                {"비교": f"{b} → {t}", "skill": f"{v['skill']:+.2%}",
                 "DM p": f"{v['dm_p']:.3f}", "MBB p": f"{v['mbb_p']:.3f}"}
                for (bt, v) in v5["significance"].items()
                for b, t in [bt.split("->")]]),
            hide_index=True, width="stretch")

    elif section.startswith("D"):
        st.markdown("#### M1 이 왜 약했나 (V4 진단)")
        md = meta["m1_diagnosis"]
        a = st.columns(4)
        a[0].metric("학습행 / feature (최소)", f"{md['rows_per_feature_min']:.2f}")
        a[1].metric("시장 X 계수 수축률", f"{md['shrinkage_market']:.2f}")
        a[2].metric("과거이력 계수 수축률", f"{md['shrinkage_hist']:.2f}")
        a[3].metric("X 를 과거이력으로 설명한 R² (최대)",
                    f"{md['max_R2_X_on_hist']:.2f}")
        st.markdown(meta["m1_diagnosis_md"])

        st.divider()
        st.markdown("#### 모델 선택 자체의 과적합 위험 (V5 합성 실험)")
        st.markdown(meta["v5_limitation_md"])
        nc = v5["null_calibration"]
        st.dataframe(pd.DataFrame([
            {"층": "시장", "중앙값": f"{nc['market']['median']:.2f}%",
             "p90": f"{nc['market']['p90']:.2f}%",
             "최대": f"{nc['market']['max']:.2f}%"},
            {"층": "Event", "중앙값": f"{nc['event']['median']:.2f}%",
             "p90": f"{nc['event']['p90']:.2f}%",
             "최대": f"{nc['event']['max']:.2f}%"}]),
            hide_index=True, width="stretch")
        st.caption(
            "예측 대상과 **아무 관계가 없는 난수**를 넣었을 때 내부 검증 오차가 "
            "얼마나 '개선'되는지를 잰 것입니다. 이 값보다 큰 개선을 요구하는 "
            f"문턱({v5['selection_margin']:.0%})을 두어 잡음 채택을 막았습니다.")

        st.divider()
        st.markdown("#### V5 가 고른 것들")
        sel = D["v5_sel"]
        a, b = st.columns(2)
        with a:
            cnt = sel["market_label"].value_counts()
            fig = go.Figure(go.Bar(x=cnt.index.tolist(), y=cnt.values,
                                   marker_color="#0D9488", text=cnt.values,
                                   textposition="outside", showlegend=False))
            show(finish(fig, title="시장 모델 선택 분포",
                        ylab="선택된 예측 시점 수", xlab="", height=380,
                        legend=False,
                        footnote="학습 데이터 내부 CV 로만 선택 · 최종 Test 미사용"))
        with b:
            cnt2 = sel["m2_family"].value_counts()
            fig = go.Figure(go.Bar(x=cnt2.index.tolist(), y=cnt2.values,
                                   marker_color="#DB2777", text=cnt2.values,
                                   textposition="outside", showlegend=False))
            show(finish(fig, title="Event 표현 선택 분포",
                        ylab="선택된 예측 시점 수", xlab="", height=380,
                        legend=False,
                        footnote="NO_EVENT = 모델이 Event 를 쓰지 않기로 선택"))

    elif section.startswith("E"):
        st.markdown("모든 실험의 전체 지표입니다. **하나도 삭제되지 않았습니다.**")
        vm = D["v5_metrics"].copy()
        vm["모델"] = vm["model"].map(lambda m: LABEL.get(m, m))
        vm["지위"] = vm["status"].map(
            {"OFFICIAL_PREREGISTERED": "공식 사전등록", "EXPLORATORY": "탐색적 확장"})
        st.dataframe(
            vm[["view", "모델", "mae", "rmse", "smape",
                "directional_accuracy", "지위"]]
            .rename(columns={"view": "그룹", "mae": "MAE ↓", "rmse": "RMSE ↓",
                             "smape": "sMAPE ↓", "directional_accuracy": "방향 정확도 ↑"})
            .style.format({"MAE ↓": "{:.2f}", "RMSE ↓": "{:.2f}",
                           "sMAPE ↓": "{:.3f}", "방향 정확도 ↑": "{:.2f}"}),
            hide_index=True, width="stretch")
        st.download_button(
            "전체 지표 CSV 내려받기",
            D["v5_metrics"].to_csv(index=False).encode("utf-8-sig"),
            "steel_scrap_all_metrics.csv", "text/csv")

    else:
        st.markdown(
            f"- V5 방법론 동결본: `{v5['freeze_version']}` "
            "(예측 결과를 보기 **전에** 커밋)\n"
            f"- 새 외부 데이터 추가: **{'예' if v5['new_raw_x_added'] else '아니오'}**\n"
            f"- 공식 사건 기록 변경: "
            f"**{'예' if v5['event_registry_changed'] else '아니오'}**\n"
            f"- Event 신뢰도 문턱: **{v5['selection_margin']:.0%}** "
            "(난수 실험으로 보정)\n"
            f"- 자동 테스트: **{k['n_tests']}개**")
        st.markdown("#### 동봉 문서")
        for label, path in (("경영진 요약", "docs/executive_summary.md"),
                            ("방법론 요약", "docs/methodology_summary.md"),
                            ("V6 결과와 해석", "docs/findings_v6.md"),
                            ("V5 결과와 해석", "docs/findings_v5.md"),
                            ("V4 결과와 해석", "docs/findings_v4.md"),
                            ("V3 결과와 해석", "docs/findings_v3.md"),
                            ("사건 압력 방법론 V3", "docs/event_method_v3.md"),
                            ("배포 보안 감사", "docs/DEPLOYMENT_AUDIT.md")):
            st.markdown(f"- [{label}]({path})")

st.divider()
st.caption(
    f"공식 실행 커밋 `{meta['git_commit'][:12]}` · "
    f"사전등록 해시 `{meta['preregistration_sha256'][:12]}` · "
    f"V3 registry `{v3['registry_version']}` · "
    f"V5 동결 `{v5['freeze_version']}` · 생성 {meta['exported_at']}"
)
