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

#: 코드 블록 조립용 줄바꿈. V8 아카이브 도식에서 정의 없이 쓰이고 있었다.
NL = chr(10)

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
        ("v7_metrics", "demo_v7_metrics.csv"),
        ("v7_cmp", "demo_v7_comparisons.csv"),
        ("v7_risk", "demo_v7_risk_by_origin.csv"),
        ("v7_cond", "demo_v7_conditional_by_origin.csv"),
        ("v8_metrics", "demo_v8_metrics.csv"),
        ("v8_rescue", "demo_v8_rescue.csv"),
        ("v8_cmp", "demo_v8_comparisons.csv"),
        ("v8_pred", "demo_v8_predictions.csv"),
        ("v8_cases", "demo_v8_shock_cases.csv"),
        ("v8_feas", "demo_v8_pit_feasibility.csv"),
        ("v8_core", "demo_v8_core_comparison.csv"),
        ("v9_metrics", "demo_v9_metrics.csv"),
        ("v9_cmp", "demo_v9_comparisons.csv"),
        ("v9_pred", "demo_v9_predictions.csv"),
        ("v9_weekly_month", "demo_v9_weekly_by_month.csv"),
        ("v9_weekly_attr", "demo_v9_weekly_attribution.csv"),
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


@st.cache_data
def load_v10():
    """V10 자산. 별도 파일로 두어 V1~V9 로딩 경로를 건드리지 않는다."""
    d = {}
    for key, name in (
        ("targets", "demo_v10_targets.csv"),
        ("rights", "demo_v10_rights.csv"),
        ("event_year", "demo_v10_event_by_year.csv"),
        ("event_comp", "demo_v10_event_composition.csv"),
        ("scrap_metrics", "demo_v10_scrap_metrics.csv"),
        ("scrap_cmp", "demo_v10_scrap_comparisons.csv"),
        ("scrap_pred", "demo_v10_scrap_predictions.csv"),
        ("cross_skills", "demo_v10_cross_skills.csv"),
        ("cross_metrics", "demo_v10_cross_metrics.csv"),
    ):
        d[key] = pd.read_csv(DATA / name)
    for key, name in (("weekly_metrics", "demo_v10_weekly_metrics.csv"),
                      ("weekly_traj", "demo_v10_weekly_traj_metrics.csv")):
        p = DATA / name
        if p.exists():
            d[key] = pd.read_csv(p)
    d["meta"] = json.loads((DATA / "v10_metadata.json").read_text(encoding="utf-8"))
    return d


D = load()
meta = D["meta"]
D10 = load_v10()
V10 = D10["meta"]
tgt = meta["target"]
k = meta["kpi"]
v3 = meta["demo_v3"]
v5 = meta["demo_v5"]
v6 = meta["demo_v6"]
v7 = meta["demo_v7"]
v8 = meta["demo_v8"]
v9 = meta["demo_v9"]
#: §31 — 상태 라벨의 단일 출처. export 단계에서 지표 방향을 적용해 만든 값이다.
EXEC_V = v6["exec_verdicts"]
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


def safe_table(obj, **kw) -> None:  # noqa: ANN001
    """표 하나의 스타일링 실패가 페이지 전체를 죽이지 못하게 한다.

    Streamlit Cloud 는 `requirements.txt` 에 적힌 것만 설치한다. pandas Styler 의
    일부 기능(예: `background_gradient`)은 **matplotlib 을 별도로 요구**하는데,
    로컬 개발 환경에는 다른 패키지를 통해 딸려 들어와 있어 로컬 테스트는 통과하고
    Cloud 에서만 빨간 오류 상자가 뜬다(2026-08-29 실측:
    `Styler.background_gradient requires matplotlib`).

    그래서 (1) 선택적 스타일 의존성을 코드에서 없애고, (2) 그래도 남는 스타일 경로는
    실패 시 **서식 없는 표로 자동 강등**한다. 데이터는 그대로 보여 준다.
    """
    try:
        st.dataframe(obj, **kw)
        return
    except Exception:                                   # noqa: BLE001
        pass
    try:
        raw = obj.data if hasattr(obj, "data") else obj
        st.dataframe(raw, **kw)
        st.caption("표 서식을 적용하지 못해 원본 값으로 표시합니다.")
    except Exception:                                   # noqa: BLE001
        st.warning("이 표를 표시하지 못했습니다. 다른 내용은 정상입니다.")


def heat_table(df: pd.DataFrame, *, title: str, zmax: float = 1.0,
               fmt: str = "{:.2f}", height: int = 300) -> None:
    """작은 수치 행렬을 **plotly heatmap** 으로 그린다.

    `Styler.background_gradient` 를 쓰지 않는다 — 같은 시각 인코딩을 이미 의존성인
    plotly 로 얻으면 matplotlib 이 필요 없다.
    """
    fig = go.Figure(go.Heatmap(
        z=df.to_numpy(dtype=float), x=list(df.columns), y=list(df.index),
        zmin=0, zmax=zmax, colorscale="Blues", showscale=False,
        text=[[fmt.format(v) for v in row] for row in df.to_numpy(dtype=float)],
        texttemplate="%{text}", textfont=dict(size=14),
        hovertemplate="%{y} · %{x}: %{z}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    show(finish(fig, title=title, ylab="", xlab="", height=height, legend=False))


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
    d_m2 = 100.0 * (OPS["M2_star"] / OPS["M0"] - 1.0)   # KPI delta 표시용

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
    # 상태 라벨은 **손으로 적지 않는다** — export 단계의 공통 판정기가 지표 방향을
    # 적용해 넘겨 준 값을 그대로 렌더링한다.
    ev1 = EXEC_V["M1_star_vs_M0"]
    ev2 = EXEC_V["M2_star_vs_M0"]
    takeaway(
        f"<b>{LABEL[order[best]]}</b> 가 가장 낮은 평균오차 "
        f"({vals[best]:.2f})를 보였습니다. "
        f"시장 정보는 M0 대비 <b>{abs(ev1['relative_improvement_pct']):.1f}% "
        f"{ev1['verdict']}</b>, Event 정보까지 더하면 "
        f"<b>{abs(ev2['relative_improvement_pct']):.1f}% "
        f"{ev2['verdict']}</b> 입니다.")
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


    # =======================================================================
    # V10 — 데이터 확장 · Target Universe
    # =======================================================================
    st.divider()
    st.subheader("V10 데이터 확장 · Target Universe")
    st.markdown(
        "V9 까지 이 프로젝트가 다룬 것은 **철·강 스크랩 하나**였고, Event 이력은 "
        "**2015-06 이후**만 있었습니다. V10 은 두 축을 동시에 넓혔습니다.")

    eh = V10["event_history"]
    c = st.columns(4)
    c[0].metric("Event 최초 시점", eh["earliest_known_at"][:7],
                delta=f"V9 {eh['v9_earliest_known_at'][:7]} 에서 확장",
                delta_color="off")
    c[1].metric("Event 레코드", f"{eh['records']:,}",
                delta=f"V9 {eh['v9_records']}건", delta_color="off")
    c[2].metric("Event episode", f"{eh['episodes']:,}",
                delta=f"V9 {eh['v9_episodes']}개", delta_color="off")
    c[3].metric("예측 대상 계열", f"{len(V10['cross_target']['targets'])}종",
                delta="V9 는 1종", delta_color="off")

    st.info(
        "**네 계열을 모두 같은 문서에서 뽑았습니다.** BLS PPI Detailed Report 라는 "
        "하나의 공식 간행물, 같은 표, **같은 발표 일정**에서 읽었기 때문에 "
        "‘어떤 상품만 데이터를 더 빨리 받았다’는 불공정이 구조적으로 생기지 않습니다.")

    st.markdown("#### 편입된 예측 대상과 Target-Specific X")
    tg = D10["targets"]
    passed = tg[tg["status"] == "PASS"]
    st.dataframe(
        passed[["label", "series_id", "official_name", "role", "x_core",
                "first_observation_month", "last_observation_month", "months",
                "gaps", "matched_train_start", "maximum_train_start"]]
        .rename(columns={
            "label": "대상", "series_id": "계열 ID", "official_name": "공식 계열명",
            "role": "역할", "x_core": "Target-Specific X",
            "first_observation_month": "최초 관측월",
            "last_observation_month": "최종 관측월", "months": "개월",
            "gaps": "공백", "matched_train_start": "matched 학습시작",
            "maximum_train_start": "maximum 학습시작"}),
        hide_index=True, width="stretch")
    st.caption(
        "X 는 상품마다 다르지만 **설계 원리는 같습니다** — "
        "‘같은 생산사슬의 전방 제품 가격 + 공통 에너지 원가’. "
        "네 대상이 모두 투입재이기 때문에 성립하는 구조이며, 성능을 보기 전에 "
        "고정했습니다.")

    rej = tg[tg["status"] != "PASS"]
    if len(rej):
        with st.expander(f"검토했지만 쓰지 않은 후보 {len(rej)}건 — 이유"):
            st.dataframe(
                rej[["label", "status", "why"]].rename(
                    columns={"label": "후보", "status": "판정", "why": "이유"}),
                hide_index=True, width="stretch")

    st.markdown("#### 학습 지지 — 공통 창은 구리가 결정했습니다")
    ct = V10["cross_target"]
    fig = go.Figure()
    labels = [ct["labels"][t] for t in ct["targets"]]
    matched_n = [next(r["n_train_first"] for r in ct["rows"]
                      if r["target_id"] == t and r["mode"] == "MATCHED")
                 for t in ct["targets"]]
    maximum_n = [next(r["n_train_first"] for r in ct["rows"]
                      if r["target_id"] == t and r["mode"] == "MAXIMUM")
                 for t in ct["targets"]]
    fig.add_bar(x=labels, y=matched_n, name="matched (1차 · 공통)",
                marker_color="#2563EB",
                text=[f"{v}" for v in matched_n], textposition="outside")
    fig.add_bar(x=labels, y=maximum_n, name="maximum (2차 · 각자 최대)",
                marker_color="#94A3B8",
                text=[f"{v}" for v in maximum_n], textposition="outside")
    show(finish(
        fig, question="Q. 네 대상이 정말 같은 조건에서 비교되었는가?",
        title="첫 예측시점의 학습 행 수  "
              "<span style='font-size:13px;color:#6B7280'>matched 에서는 "
              "네 대상이 모두 같은 86행</span>",
        ylab="학습 행 수", xlab="", height=400))
    st.success(
        f"**1차 비교에서 네 대상의 학습행이 정확히 같습니다({matched_n[0]}행).** "
        f"공통 학습 시작월 **{ct['matched_train_start']}** 은 "
        f"**{ct['labels'][ct['binding_target']]}** 의 자료 공백이 결정했고, "
        "창을 늘리려고 그 대상을 빼지 않았습니다.")

    st.markdown("#### 데이터 권리 — PASS 만 씁니다")
    rt = V10["rights"]
    c = st.columns(4)
    c[0].metric("PASS", rt["pass"])
    c[1].metric("REVIEW (사용 금지)", rt["review"])
    c[2].metric("REJECT", rt["reject"])
    c[3].metric("유료 소스", rt["paid_sources_used"])
    st.dataframe(
        D10["rights"].rename(columns={
            "source": "소스", "organization": "기관", "status": "판정",
            "used": "사용", "free": "무료", "url": "공식 URL", "note": "비고"}),
        hide_index=True, width="stretch")
    st.caption(
        "REVIEW 는 모델링 목적에서 REJECT 와 **동일하게** 취급합니다. "
        "Federal Register 는 사이트가 안내한 대로 **공개 API 만** 사용했고 "
        "HTML 을 긁거나 CAPTCHA 를 우회하지 않았습니다.")

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
    _v4 = EXEC_V["M2_star_vs_V4_M2R"]
    q[3].metric(f"V4 대비 {_v4['verdict']}",
                f"{_v4['relative_improvement_pct']:+.0f}%",
                help="V4 의 Event 모델(M2-R) 대비 MAE 변화 (MAE ↓ 낮을수록 정확)")

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

    # =======================================================================
    # §PART N — Event Risk & Conditional Value (V7)
    #
    # 새 최상위 탭을 만들지 않는다. Event Intelligence 안의 한 섹션이다.
    # 카드의 상태 라벨은 손으로 적지 않는다 — export 단계에서 지표 방향 판정기가
    # 만든 값(v7["risk_cards"])을 그대로 읽는다.
    # =======================================================================
    st.divider()
    st.markdown("### Event Risk & Conditional Value")
    st.markdown(meta["v7_intro_md"])

    def _pfmt(p: float) -> str:
        """0.001 미만을 'p = 0.000' 으로 적으면 '정확히 0' 처럼 읽힌다."""
        return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"

    rcards = st.columns(4)
    for col, card in zip(rcards, v7["risk_cards"]):
        v = card["verdict"]
        p = card.get("p_value")
        pstr = (f"<br><span style='font-size:11.5px;color:#9CA3AF'>"
                f"{_pfmt(p)}</span>" if p is not None else "")
        col.markdown(
            f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
            f"border-left:5px solid {VCOLOR[v]};border-radius:8px;padding:14px;"
            f"height:100%'>"
            f"<span style='font-size:12.5px;color:#6B7280'>{card['label']}</span>"
            f"<br><b style='font-size:20px;color:{VCOLOR[v]}'>{v}</b>"
            f"<br><span style='font-size:12.5px;color:#374151'>"
            f"{card['detail']}</span>"
            f"<br><span style='font-size:11.5px;color:#9CA3AF'>"
            f"{card['metric_label']}</span>{pstr}</div>",
            unsafe_allow_html=True)
    st.caption(
        "네 카드는 **서로 다른 지표**를 씁니다 (Interval Score · Brier · MAE). "
        "지표마다 좋아지는 방향이 다르므로 **공통 판정기**가 방향을 적용합니다 — "
        "화면에서 손으로 적은 상태 라벨은 하나도 없습니다. "
        "**p 값이 서술적 방향을 뒤집지 않습니다.**")

    risk_view = st.radio(
        "어떤 위험 질문을 볼까요?",
        ["예측 불확실성", "급등 위험", "시장 상황별 Event 효과",
         "새로 들어온 Event 정보"],
        index=0, horizontal=True, key="v7_risk")

    v7r = D["v7_risk"].copy()
    v7r["month_dt"] = pd.to_datetime(v7r["target_month"] + "-01")
    v7cd = D["v7_cond"].copy()

    def _v7v(track, model, col):
        s = D["v7_metrics"]
        s = s[(s["track"] == track) & (s["model"] == model)]
        if s.empty or pd.isna(s[col].iloc[0]):
            return None
        return float(s[col].iloc[0])

    # ================= 예측 불확실성 (PRIMARY) =========================
    if risk_view.startswith("예측"):
        st.markdown("#### 예측 불확실성 — **1차 가설입니다**")
        pv7 = v7["primary"]
        fig = go.Figure()
        fig.add_scatter(x=v7r["month_dt"], y=v7r["U1_hi"], name="80% 구간 상단",
                        line=dict(color="rgba(219,39,119,0.0)"),
                        showlegend=False, hoverinfo="skip")
        fig.add_scatter(x=v7r["month_dt"], y=v7r["U1_lo"],
                        name="Event 조건부 80% 예측구간", fill="tonexty",
                        fillcolor="rgba(219,39,119,0.14)",
                        line=dict(color="rgba(219,39,119,0.0)"))
        fig.add_scatter(x=v7r["month_dt"], y=v7r["M1_star"],
                        name=LABEL["M1_star"] + " 예측",
                        line=dict(color=COLORS["M1_star"], width=2.2, dash="dot"))
        fig.add_scatter(x=v7r["month_dt"], y=v7r["y_true"], name="실제 WPU1012",
                        line=dict(color=COLORS["actual"], width=2.8))
        show(finish(
            fig, question="Q. 예측이 얼마나 틀릴 수 있는지를 제대로 알려주는가?",
            title="목표 80% 구간이 실제로는 100% 를 덮었다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "실제값이 구간을 벗어난 적이 한 번도 없음</span>",
            ylab="철·강 스크랩 PPI 지수", xlab="대상 월",
            footnote=f"{FOOT_TARGET}  ·  평가 시점 {v7['n_origins_risk']}개",
            height=470))
        a, b, c = st.columns(3)
        a.metric("목표 커버리지", f"{v7['primary_interval']:.0%}")
        b.metric("실제 커버리지 (Event 조건부)", f"{pv7['U1_coverage']:.0%}",
                 delta=f"{pv7['U1_coverage'] - v7['primary_interval']:+.0%}",
                 delta_color="inverse")
        c.metric("평균 구간 폭", f"{pv7['U1_width']:.0f}",
                 help="지수 Point. 폭이 좁을수록 정보가 많다는 뜻입니다")
        takeaway(
            f"Event 조건부 구간이 Event 없는 구간보다 Interval Score 를 "
            f"<b>{pv7['U0_interval_score']:.0f} → {pv7['U1_interval_score']:.0f}</b> "
            f"로 낮췄지만 <b>통계적으로 유의하지 않습니다</b> "
            f"(p = {pv7['inference']['p_value']:.3f}). 그리고 "
            "<b>두 구간 모두 커버리지가 100%</b> 입니다 — 구간이 정확한 것이 "
            "아니라 <b>너무 넓습니다.</b>")
        st.markdown(meta["v7_coverage_md"])
        reading_guide(
            "분홍색 띠가 모델이 제시한 80% 예측 구간이고, 검은 선이 실제값입니다. "
            "제대로 보정됐다면 실제값이 10번 중 2번은 띠 밖으로 나가야 합니다.",
            f"{v7['n_origins_risk']}개 시점에서 <b>한 번도 벗어나지 않았습니다.</b> "
            "구간이 너무 넓다는 뜻입니다.",
            "이것은 Event 의 문제가 아니라 <b>표본 구간의 문제</b>입니다. 구간 폭은 "
            "과거 오차에서 나오는데, 그 과거(2021~22)가 평가 구간(2023~25)보다 "
            "훨씬 격렬했습니다.")

    # ================= 급등 위험 =======================================
    elif risk_view.startswith("급등"):
        st.markdown("#### 급등·급락 위험 — 표본이 부족했습니다")
        tl = v7["tail"]
        st.warning(
            f"**사전에 정한 최소 지지 규칙을 넘지 못했습니다.** 급등 사례 "
            f"**{tl['upper_positive']}건** · 급락 사례 **{tl['lower_positive']}건** "
            f"— 규칙은 각 **{tl['min_positives']}건** 이었습니다. "
            "임계값을 낮춰 사례를 늘리는 것은 **결과를 본 뒤의 조정**이므로 "
            "하지 않았습니다.")
        pairs = [("B_tail_upper", f"급등 (상위 {1 - tl['upper_q']:.0%})"),
                 ("B_tail_lower", f"급락 (하위 {tl['lower_q']:.0%})")]
        fig = go.Figure()
        fig.add_bar(x=[lab for _, lab in pairs],
                    y=[_v7v(t, "T0", "brier") for t, _ in pairs],
                    name="시장 문맥만 (Event 없음)",
                    marker_color=COLORS["M1_star"],
                    text=[f"{_v7v(t, 'T0', 'brier'):.3f}" for t, _ in pairs],
                    textposition="outside")
        fig.add_bar(x=[lab for _, lab in pairs],
                    y=[_v7v(t, "T1", "brier") for t, _ in pairs],
                    name="+ Event 위험 정보", marker_color=COLORS["M2_star"],
                    text=[f"{_v7v(t, 'T1', 'brier'):.3f}" for t, _ in pairs],
                    textposition="outside")
        fig.update_layout(barmode="group")
        show(finish(
            fig, question="Q. Event 정보가 급등·급락 위험을 감지하는가?",
            title="급등·급락 위험 — 판정할 만한 사례 수가 없었다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "Brier Score ↓ 낮을수록 정확</span>",
            ylab="Brier Score (확률 예측 오차)", xlab="",
            footnote=f"급등 {tl['upper_positive']}건 / 급락 "
                     f"{tl['lower_positive']}건 — 사전 규칙 최소 "
                     f"{tl['min_positives']}건 미달  ·  {FOOT_TARGET}",
            height=440))
        takeaway(
            "서술적으로는 <b>두 경우 모두 Event 를 넣은 쪽이 더 나빴습니다.</b> "
            "다만 사례 수가 규칙에 미달하므로 이 실험의 판정은 "
            "<b>결론 유보</b>입니다 — '효과 없음'이 아니라 '판정할 수 없음'입니다.")
        reading_guide(
            "막대가 낮을수록 위험 확률을 정확히 맞힌 것입니다.",
            "Event 를 더한 막대가 두 경우 모두 더 높습니다(더 부정확).",
            "**사례가 4건·1건뿐입니다.** 이 수치는 몇 건이 바뀌면 크게 흔들립니다. "
            "숫자보다 **표본 부족이라는 사실 자체가 결과**입니다.")

    # ================= 시장 상황별 Event 효과 ==========================
    elif risk_view.startswith("시장"):
        st.markdown("#### 시장 상황별 Event 효과 — 사전선언 3개")
        st.caption(
            "**결과를 보기 전에 정확히 3개만** 선언했습니다. 결과를 본 뒤 짝을 "
            "바꾸거나 더하지 않았습니다.")
        st.dataframe(pd.DataFrame([
            {"상호작용": it["label"].split(" × ")[0],
             "시장 상태": it["label"].split(" × ")[1]}
            for it in v7["interactions"]]), hide_index=True, width="stretch")
        order = [("M1_CTRL", "시장 정보만", COLORS["M1_star"]),
                 ("M2_INT", "+ 사전선언 상호작용 3개", COLORS["M2_star"])]
        fig = go.Figure()
        for m, lab, cl in order:
            v = _v7v("C_D_conditional", m, "mae")
            fig.add_bar(x=[lab], y=[v], marker_color=cl, showlegend=False,
                        text=[f"{v:.2f}"], textposition="outside",
                        textfont=dict(size=13))
        show(finish(
            fig, question="Q. Event 효과가 시장 상황에 따라 달라지는가?",
            title="시장 상황을 함께 보면 Event 가 도움이 되는가?  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "MAE ↓ 낮을수록 정확 · 통제 실험</span>",
            ylab="평균 예측오차 MAE (지수 Point)", xlab="",
            footnote=f"{FOOT_TARGET}  ·  통제 트랙 "
                     f"{v7['n_origins_conditional']}개 시점",
            height=430, legend=False))
        _ic = next(c for c in v7["risk_cards"] if c["role"] == "interaction")
        takeaway(
            f"MAE 가 <b>{_ic['base_value']:.2f} → {_ic['new_value']:.2f}</b> 로 "
            f"낮아졌습니다. <b>V7 에서 유일하게 개선 방향</b>이지만 "
            f"통계적으로 유의하지 않고(p = {_ic['p_value']:.3f}) "
            "<b>보조 가설</b>이며 세 개를 함께 시험했는데 다중비교 보정이 "
            "없습니다. V5 의 공식 결과를 대체하지 않습니다.")
        reading_guide(
            "두 막대는 **같은 통제 조건**에서 상호작용 항만 켜고 끈 결과입니다.",
            "상호작용을 켠 쪽이 조금 낮습니다.",
            "**이 정도 크기는 표본 50개에서 우연히 나올 수 있는 범위 안**입니다. "
            "난수 실험에서 아무 관계 없는 잡음도 내부검증을 중앙값 1.6% "
            "'개선'시켰습니다.")

    # ================= 새로 들어온 Event 정보 ==========================
    else:
        st.markdown("#### 새로 들어온 Event 정보 — 발표창 신규분")
        st.markdown(
            "같은 사건이라도 **\"지금 유지되고 있는 상태\"** 와 "
            "**\"예측 직전 창에 새로 들어온 것\"** 은 다른 정보일 수 있습니다. "
            "두 표현을 같은 조건에서 비교했습니다.")
        order = [("M1_CTRL", "시장 정보만", COLORS["M1_star"]),
                 ("M2_PERSIST", "+ 지속형 Event 표현", COLORS["ME_star"]),
                 ("M2_RW", "+ 발표창 신규 Event", COLORS["M2_star"])]
        fig = go.Figure()
        for m, lab, cl in order:
            v = _v7v("C_D_conditional", m, "mae")
            fig.add_bar(x=[lab], y=[v], marker_color=cl, showlegend=False,
                        text=[f"{v:.2f}"], textposition="outside",
                        textfont=dict(size=13))
        show(finish(
            fig, question="Q. 예측 직전에 새로 들어온 Event 가 더 유용한가?",
            title="새로 들어온 Event 정보는 오히려 정확도를 떨어뜨렸다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "MAE ↓ 낮을수록 정확 · 통제 실험</span>",
            ylab="평균 예측오차 MAE (지수 Point)", xlab="",
            footnote=f"{FOOT_TARGET}  ·  통제 트랙 "
                     f"{v7['n_origins_conditional']}개 시점",
            height=430, legend=False))
        _sc = next(c for c in v7["risk_cards"] if c["role"] == "surprise")
        takeaway(
            f"발표창 신규 Event 만 쓴 모델이 "
            f"<b>{_sc['base_value']:.2f} → {_sc['new_value']:.2f}</b> 로 "
            f"<b>유의하게 더 나빴습니다</b> (p = {_sc['p_value']:.5f}). "
            "실행 전에 적어 둔 예상과 일치합니다 — 월 단위 예측에서 "
            "'발표창 신규분'은 이미 쓰고 있는 전이 신호와 상당 부분 겹치며, "
            "겹치는 만큼 새 정보가 아니라 잡음이 됩니다.")
        reading_guide(
            "세 막대는 **같은 통제 조건**에서 Event 표현만 바꾼 결과입니다.",
            "두 Event 표현 모두 시장 정보만 쓴 모델보다 높습니다(더 부정확).",
            "이것은 **부정적 결과이며 그대로 보고합니다.** 유의하게 나온 방향이 "
            "개선이 아니라 악화라는 점이 중요합니다.")

    st.divider()
    st.error(meta["v7_stop_rule_md"])
    with st.expander("V7 전체 비교표 (여섯 가지 전부)"):
        st.dataframe(pd.DataFrame([
            {"Track": c["track"], "비교": f"{c['base']} → {c['test']}",
             "지표": c["metric"], "차이": f"{c['diff']:+.4f}",
             "p": f"{c['p_value']:.5f}",
             "지위": "PRIMARY" if c["is_primary"] else "보조",
             "비고": c["support"] or "—"} for c in v7["comparisons"]]),
            hide_index=True, width="stretch")
        st.caption(
            "**하나도 숨기지 않았습니다.** 차이의 부호는 지표마다 의미가 다르므로 "
            "카드의 판정을 함께 보십시오.")

    # =======================================================================
    # §PART L — V8: Event 가 기존 모델의 오판을 뒤집을 수 있는가
    #
    # 새 최상위 탭을 만들지 않는다. Event Intelligence 안의 한 섹션이다.
    # 카드의 상태 라벨은 손으로 적지 않는다 — export 의 지표 방향 판정기가 만든다.
    # =======================================================================
    st.divider()
    st.markdown("### Event가 기존 모델의 오판을 뒤집을 수 있는가?")
    st.markdown(meta["v8_intro_md"])

    a8 = v8["alignment"]
    ac = st.columns(4)
    ac[0].metric("정렬 검사", f"{a8['problems']}건 문제",
                 help=f"{a8['n_origins']}개 예측시점 × {a8['checks_per_origin']}가지 검사")
    ac[1].metric("실현된 급변", f"{v8['n_shock']} / {v8['n_origins']}")
    ac[2].metric("게이트가 열린 시점", f"{v8['gate']['n_gate_open']} / {v8['n_origins']}",
                 help="열림 정도 0.5 초과. 한 번도 열리지 않았습니다")
    ac[3].metric("후보 총량", f"{v8['total_candidate_count']}개",
                 help="V5 246 · V6 63 · V7 45 → V8 18")

    vcards = st.columns(4)
    for col, card in zip(vcards, v8["cards"]):
        v = card["verdict"]
        p = card.get("p_value")
        pstr = (f"<br><span style='font-size:11.5px;color:#9CA3AF'>"
                f"{_pfmt(p)}</span>" if p is not None else "")
        ds = card.get("dir_shock")
        dstr = (f"<br><span style='font-size:11.5px;color:#9CA3AF'>"
                f"급변 방향 {ds:.3f}</span>" if ds is not None else "")
        col.markdown(
            f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
            f"border-left:5px solid {VCOLOR[v]};border-radius:8px;padding:14px;"
            f"height:100%'>"
            f"<span style='font-size:12.5px;color:#6B7280'>{card['label']}</span>"
            f"<br><b style='font-size:20px;color:{VCOLOR[v]}'>{v}</b>"
            f"<br><span style='font-size:12.5px;color:#374151'>"
            f"{card['detail']}</span>"
            f"<br><span style='font-size:11.5px;color:#9CA3AF'>"
            f"{card['metric_label']}</span>{pstr}{dstr}</div>",
            unsafe_allow_html=True)
    st.caption(
        "네 카드 모두 **M1\\* 대비 전체 MAE** 로 판정했습니다. 상태 라벨은 지표 "
        "방향 판정기가 만들며 화면에서 손으로 적은 것은 하나도 없습니다. "
        "**MAE 가 낮아진 카드라도 급변 방향 적중률을 함께 보십시오** — 이 연구의 "
        "질문은 평균 오차가 아니라 **급변에서의 판단**입니다.")

    v8_view = st.radio(
        "어떤 관점을 볼까요?",
        ["Shock Audit", "Independent Signals", "Shock Rescue", "DS Challenge"],
        index=0, horizontal=True, key="v8_view")

    v8m = D["v8_metrics"].set_index("model")
    v8rc = D["v8_rescue"].set_index("candidate")
    v8p = D["v8_pred"].copy()
    v8p["month_dt"] = pd.to_datetime(v8p["target_month"] + "-01")
    LB = v8["labels"]

    # ================= Shock Audit =====================================
    if v8_view == "Shock Audit":
        st.markdown("#### 실제 급변 전에 Event 정보가 존재했는가")
        st.markdown(meta["v8_shock_audit_md"])
        cc = v8["case_counts"]
        cl = v8["case_labels"]
        order = ["A", "B", "C", "D"]
        colors = {"A": "#059669", "B": "#DC2626", "C": "#F59E0B", "D": "#9CA3AF"}
        fig = go.Figure()
        for mdl in order:
            fig.add_bar(x=[f"{mdl}"], y=[cc.get(mdl, 0)], name=cl[mdl],
                        marker_color=colors[mdl], text=[cc.get(mdl, 0)],
                        textposition="outside", textfont=dict(size=14))
        show(finish(
            fig, question="Q. 실제 급변 전에 모델이 쓸 수 있는 Event 정보가 있었는가?",
            title="급변 8건 중 6건에는 사전 Event 정보가 있었다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "다만 신호가 뜬 20개월 중 14개월은 아무 일도 없었다</span>",
            ylab="예측시점 수", xlab="사례 구분",
            footnote=f"급변 정의: 학습 구간 분위수 {v8['shock_quantile']:.0%} "
                     f"(결과를 보기 전에 고정)  ·  {FOOT_TARGET}",
            height=440))
        st.dataframe(pd.DataFrame([
            {"사례": mdl, "정의": cl[mdl], "건수": cc.get(mdl, 0)} for mdl in order]),
            hide_index=True, width="stretch")
        takeaway(
            f"급변 {cc['A'] + cc['B']}건 중 <b>{cc['A']}건</b>에는 예측 시점에 이미 "
            "Event 신호가 있었습니다. <b>\"정보가 없었다\"는 변명은 성립하지 "
            "않습니다.</b> 그러나 신호가 뜬 "
            f"{cc['A'] + cc['C']}개월 중 <b>{cc['C']}개월은 아무 일도 "
            "일어나지 않았습니다.")
        reading_guide(
            "A 는 구제 가능성이 있었던 달, B 는 Event 가 쓸 정보가 없었던 달, "
            "C 는 오경보 후보입니다.",
            "A 가 6건으로 B(2건)보다 많습니다 — 정보는 있었습니다.",
            "C 가 14건입니다. **신호가 있다고 급변이 오지는 않습니다** — "
            "신호 대비 적중률은 30%로 기저(16%)의 두 배지만 여전히 낮습니다.")

    # ================= Independent Signals =============================
    elif v8_view == "Independent Signals":
        st.markdown("#### 가격이력 없이 독립적으로 판단할 수 있는가")
        st.caption(
            "아래 세 모델은 **가격이력 블록을 전혀 쓰지 않고** 다음 달 변화량을 "
            "직접 예측합니다. 마지막 가용 관측치는 변화량을 수준으로 되돌리는 "
            "산술 상수일 뿐 모델 입력이 아닙니다.")
        order = ["N0", "M0", "M1_star", "M1_X", "M2_E", "M2_XE"]
        cmap = {"N0": "#9CA3AF", "M0": "#2563EB", "M1_star": "#0D9488",
                "M1_X": "#7C3AED", "M2_E": "#F59E0B", "M2_XE": "#DB2777"}
        fig = go.Figure()
        fig.add_bar(x=[LB[m] for m in order],
                    y=[float(v8m.loc[m, "mae_all"]) for m in order],
                    name="전체 50개월", marker_color=[cmap[m] for m in order],
                    text=[f"{float(v8m.loc[m, 'mae_all']):.1f}" for m in order],
                    textposition="outside", showlegend=False)
        show(finish(
            fig, question="Q. 가격이력 없이 시장·Event 만으로 판단할 수 있는가?",
            title="독립 모델 셋 모두 기존 시장 모델을 넘지 못했다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "MAE ↓ 낮을수록 정확</span>",
            ylab="평균 예측오차 MAE (지수 Point)", xlab="",
            footnote=FOOT_TARGET, height=460, legend=False))

        st.markdown("##### 급변 8개월만 따로 보면 — 여기가 결정적입니다")
        fig2 = go.Figure()
        fig2.add_bar(x=[LB[m] for m in order],
                     y=[float(v8m.loc[m, "direction_accuracy_shock"])
                        for m in order],
                     marker_color=[cmap[m] for m in order],
                     text=[f"{float(v8m.loc[m, 'direction_accuracy_shock']):.3f}"
                           for m in order],
                     textposition="outside", showlegend=False)
        fig2.add_hline(y=0.5, line=dict(color="#9CA3AF", width=1.4, dash="dash"))
        fig2.add_annotation(xref="paper", x=0.99, y=0.5, xanchor="right",
                            text="동전 던지기 0.50", showarrow=False, yshift=11,
                            font=dict(size=11, color="#6B7280"))
        show(finish(
            fig2, question="Q. 급변이 실제로 일어난 달에 방향을 맞혔는가?",
            title="Event 만 쓴 모델은 급변 8개월의 방향을 8번 다 틀렸다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "방향 적중률 ↑ 높을수록 정확</span>",
            ylab="급변월 방향 적중률", xlab="",
            footnote=f"급변 {v8['n_shock']}개월만 대상 — 표본이 작습니다  ·  "
                     f"{FOOT_TARGET}",
            height=440, legend=False))
        takeaway(
            "급변 구간에서 가장 정확한 것은 여전히 <b>과거 PPI 기반 모델</b>이고, "
            "<b>직전 가용치를 그대로 쓰는 것조차 시장 모델을 이깁니다.</b> "
            "Event 만 쓴 모델은 <b>8번 다 틀렸습니다(0/8)</b>.")
        reading_guide(
            "위 그림은 전체 50개월 평균 오차, 아래 그림은 급변 8개월의 방향 "
            "적중률입니다.",
            "독립 모델 셋 다 기존 모델을 넘지 못했고, 급변에서는 더 나빠집니다.",
            "**급변이 8개월뿐입니다.** 이 수치는 몇 건이 바뀌면 크게 흔들리며 "
            "유의성을 주장하지 않습니다.")

    # ================= Shock Rescue (flagship) =========================
    elif v8_view == "Shock Rescue":
        st.markdown("#### Event가 기본 모델의 잘못된 판단을 얼마나 구제했는가")
        st.markdown(meta["v8_rescue_md"])
        cands = ["M1_X", "M2_E", "M2_XE", "M2_Gate"]
        rr = [float(v8rc.loc[c, "rescue_rate"]) for c in cands]
        fo = [float(v8rc.loc[c, "false_override_rate"]) for c in cands]
        fig = go.Figure()
        fig.add_bar(x=[LB[c] for c in cands], y=rr,
                    name="구제 — 기본 모델이 틀렸을 때 바로잡음",
                    marker_color="#059669",
                    text=[f"{v:.3f}" for v in rr], textposition="outside")
        fig.add_bar(x=[LB[c] for c in cands], y=fo,
                    name="잘못된 뒤집기 — 맞은 것을 틀리게 바꿈",
                    marker_color="#DC2626",
                    text=[f"{v:.3f}" for v in fo], textposition="outside")
        fig.update_layout(barmode="group")
        show(finish(
            fig, question="Q. Event가 기본 모델의 잘못된 판단을 얼마나 구제했는가?",
            title="구제한 만큼 잘못 뒤집었다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "초록 ↑ 높을수록 좋음 · 빨강 ↓ 낮을수록 좋음</span>",
            ylab="비율", xlab="",
            footnote=f"기본 모델 = M1*  ·  방향 오답 20건 / 정답 30건  ·  "
                     f"{FOOT_TARGET}",
            height=470))

        st.markdown("##### 실질적으로 이탈했을 때 그 이탈이 도움이 됐는가")
        prec = [(c, v8rc.loc[c, "rescue_precision"],
                 int(v8rc.loc[c, "substantial_departures"])) for c in cands]
        st.dataframe(pd.DataFrame([
            {"후보": LB[c], "이탈 정확도": ("—" if pd.isna(p) else f"{float(p):.3f}"),
             "실질 이탈 건수": n,
             "해석": ("표본 부족" if n < 5 else
                    ("이탈의 절반 이상이 악화" if float(p) < 0.5 else "이탈이 유익"))}
            for c, p, n in prec]), hide_index=True, width="stretch")
        takeaway(
            "구제율이 가장 높은 <b>시장만 독립</b> 모델이 동시에 <b>잘못된 뒤집기도 "
            "가장 많습니다</b>(13건 구제 vs 14건 오작동 — 순효과 음수). "
            "이탈 정확도가 <b>0.385~0.429</b> 라는 것은 기존 모델에서 벗어난 "
            "경우의 <b>60% 이상이 오히려 나빠졌다</b>는 뜻입니다.")

        st.divider()
        st.markdown(meta["v8_gate_md"])
        gcase = ["A", "B", "C", "D"]
        gv = [v8["gate"][f"mean_case_{k}"] for k in gcase]
        fig3 = go.Figure()
        fig3.add_bar(x=[f"{k} — {v8['case_labels'][k]}" for k in gcase], y=gv,
                     marker_color=["#059669", "#DC2626", "#F59E0B", "#9CA3AF"],
                     text=[f"{v:.3f}" for v in gv], textposition="outside",
                     showlegend=False)
        fig3.add_hline(y=0.5, line=dict(color="#DC2626", width=1.4, dash="dash"))
        fig3.add_annotation(xref="paper", x=0.99, y=0.5, xanchor="right",
                            text="게이트가 열리는 문턱 0.50", showarrow=False,
                            yshift=11, font=dict(size=11, color="#DC2626"))
        show(finish(
            fig3, question="Q. 게이트가 진짜 급변에서 더 열렸는가?",
            title="게이트는 진짜 급변에서 오히려 가장 덜 열렸다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "평균 열림 정도 · 0.50 을 넘어야 전문가로 전환된다</span>",
            ylab="평균 열림 정도 (0~1)", xlab="",
            footnote=f"50개 예측시점 전부에서 0.5 미만  ·  {FOOT_EVENT}",
            height=460, legend=False, yrange=[0, 0.6]))
        st.markdown(meta["v8_ensemble_caveat_md"])

    # ================= DS Challenge ====================================
    else:
        st.markdown("#### Data Scientist Challenge")
        ds = v8["ds_challenge"]
        c = st.columns(3)
        c[0].metric("제안", f"{ds['reviewed']}건")
        c[1].metric("QA 승인", f"{ds['approved']}건")
        r8 = ds.get("result") or {}
        c[2].metric("재보정이 선택된 시점",
                    f"{r8.get('n_applied', 0)} / {v8['n_origins']}",
                    help="나머지는 절차가 스스로 기존 모델을 골랐습니다")
        st.dataframe(pd.DataFrame([
            {"제안": x["name"], "슬롯": x["slot"],
             "QA 판정": ("승인" if x["decision"] == "APPROVED" else "기각"),
             "조건": x["n_conditions"] if x["decision"] == "APPROVED" else "—",
             "사유": x["rationale"][:110] + "…"}
            for x in ds["candidates"]]), hide_index=True, width="stretch")
        st.markdown(meta["v8_ds_md"])
        st.caption(
            "기술적 상세는 `연구 과정 (Research Archive)` 탭에 있습니다. "
            "**DS 후보로 기존 M1/M2 를 대체하지 않았습니다** — 나란히 놓고 볼 뿐입니다.")

    # =======================================================================
    # §38 — V9: 더 긴 과거 이력 · 주간 사건 · 전달 진단
    #
    # 새 최상위 탭을 만들지 않는다. Event Intelligence 안의 한 섹션이다.
    # =======================================================================
    st.divider()
    st.markdown("### 모델 대신 데이터를 늘리면 어떻게 되는가? (V9)")
    st.markdown(meta["v9_intro_md"])

    s9 = st.columns(4)
    _ts = v9["training_support"]
    s9[0].metric("추가된 과거 이력",
                 f"+{v9['panel']['WPU1012']['added']}개월",
                 help="예측 대상 계열 기준. 2008-09 까지 거슬러 재구성했습니다")
    s9[1].metric("학습 정보 (첫 예측시점)",
                 f"{_ts['n_train_first_origin']['core_m0_only']}",
                 delta=f"+{_ts['increase_pct_first_origin']:.0f}%",
                 help=f"기존 {_ts['n_train_first_origin']['legacy_frozen']}행")
    s9[2].metric("재구성 교차검증",
                 f"{v9['cross_check']['mismatches']}건 불일치",
                 help=f"{v9['cross_check']['matches']}건 일치 — 같은 문서를 두 방법으로 읽어 대조")
    s9[3].metric("예측 대상 월", f"{v9['n_origins']}개 (동일)",
                 help="V5/V6/V8 과 정확히 같습니다 — 새 검증창이 아닙니다")

    st.info(
        "**예측 대상 50개월은 그대로이고 늘어난 것은 학습 정보뿐입니다.** "
        "그래서 이것은 새로운 검증창이 아니라 **같은 창에서 과거 정보만 늘린 "
        "실험**입니다.")

    v9_view = st.radio(
        "어떤 관점을 볼까요?",
        ["Long-History Validation", "Weekly Event Nowcast",
         "Event Design Diagnostic", "Weekly Event Attribution"],
        index=0, horizontal=True, key="v9_view")

    L9 = {"M0": "과거 PPI 기반 (M0)", "M1_star": "시장·산업 정보 (M1*)",
          "M2_star": "공식 Event 정보 (M2*)", "M2_Gate_v8": "V8 Event 게이트",
          "V9_M0_LH": "과거 PPI 기반 · 장기", "V9_M1_LH": "시장 정보 · 장기",
          "V9_M2_XE": "시장+Event 독립 · 장기", "V9_M2_LH": "Event 게이트 · 장기"}

    # ================= Long-History Validation =========================
    if v9_view == "Long-History Validation":
        st.markdown("#### 같은 50개월, 더 많은 과거 정보")
        st.markdown(meta["v9_headline_md"])
        order = ["M0", "M1_star", "M2_Gate_v8", "V9_M0_LH", "V9_M1_LH",
                 "V9_M2_LH"]
        cmap = {"M0": "#9CA3AF", "M1_star": "#9CA3AF", "M2_Gate_v8": "#9CA3AF",
                "V9_M0_LH": "#059669", "V9_M1_LH": "#0D9488",
                "V9_M2_LH": "#DB2777"}
        vals = [v9["mae"][m] for m in order]
        fig = go.Figure()
        fig.add_bar(x=[L9[m] for m in order], y=vals,
                    marker_color=[cmap[m] for m in order],
                    text=[f"{v:.2f}" for v in vals], textposition="outside",
                    showlegend=False)
        fig.add_hline(y=v9["mae"]["M0"], line=dict(color="#2563EB", width=1.4,
                                                   dash="dash"))
        fig.add_annotation(xref="paper", x=0.01, y=v9["mae"]["M0"],
                           xanchor="left", showarrow=False, yshift=12,
                           text=f"기존 기준선 {v9['mae']['M0']:.1f}",
                           font=dict(size=11.5, color="#2563EB"))
        show(finish(
            fig, question="Q. 과거 정보를 늘리면 예측이 좋아지는가?",
            title="더 많은 데이터가 더 나은 모델을 이겼다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "MAE ↓ 낮을수록 정확 · 회색은 기존 동결 결과</span>",
            ylab="평균 예측오차 MAE (지수 Point)", xlab="",
            footnote=f"{FOOT_TARGET}  ·  같은 50개 예측시점", height=470,
            legend=False))
        takeaway(
            f"과거 PPI 기반 모델이 <b>{v9['mae']['M0']:.2f} → "
            f"{v9['mae']['V9_M0_LH']:.2f}</b> 로 좋아졌습니다 "
            f"(<b>p = 0.045</b>). 알고리즘은 한 글자도 바뀌지 않았습니다 — "
            "<b>더 많은 데이터가 만든 개선</b>입니다.")

        st.markdown(meta["v9_support_md"])
        st.divider()
        st.markdown(meta["v9_negative_md"])
        st.warning(meta["v9_asymmetry_md"])

        with st.expander("전체 비교표"):
            st.dataframe(pd.DataFrame([
                {"질문": c["question"], "기준": L9.get(c["base"], c["base"]),
                 "비교": L9.get(c["test"], c["test"]),
                 "MAE": f"{c['mae_base']:.2f} → {c['mae_test']:.2f}",
                 "상대": f"{c['rel']:+.2f}%",
                 "p": ("—" if c["p_value"] is None else f"{c['p_value']:.3f}")}
                for c in v9["comparisons"]]), hide_index=True, width="stretch")

    # ================= Weekly Event Nowcast ============================
    elif v9_view == "Weekly Event Nowcast":
        st.markdown("#### 월 안에서 사건이 도착하면 예측이 좋아지는가")
        st.markdown(meta["v9_weekly_md"])
        wk = pd.DataFrame(v9["weekly"]["by_week"])
        fig = go.Figure()
        fig.add_bar(x=wk["week"], y=wk["mae"],
                    marker_color=["#0D9488"] + ["#DC2626"] * 4,
                    text=[f"{v:.1f}" for v in wk["mae"]],
                    textposition="outside", showlegend=False)
        show(finish(
            fig, question="Q. 월 안에서 사건 정보가 도착하면 예측이 좋아지는가?",
            title="사건 정보가 도착할수록 예측이 나빠졌다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "MAE ↓ 낮을수록 정확 · 시장 정보는 월초에 고정</span>",
            ylab="평균 예측오차 MAE (지수 Point)",
            xlab="정보 절단 시점 (W0 월초 → W4 월말)",
            footnote=f"{FOOT_TARGET}  ·  통계 단위는 대상월 — 250개 독립 관측이 아닙니다",
            height=450, legend=False))
        c = st.columns(4)
        rq = v9["weekly"]["revision_quality"]
        c[0].metric("유익한 수정", f"{rq['beneficial_revision_rate']:.0%}")
        c[1].metric("유해한 수정", f"{rq['harmful_revision_rate']:.0%}")
        c[2].metric("주간 구제", f"{rq['weekly_rescue_rate']:.1%}",
                    help=f"월초 방향이 틀렸던 {rq['n_w0_wrong']}건 중")
        c[3].metric("잘못된 뒤집기", f"{rq['false_weekly_override_rate']:.1%}",
                    help=f"월초 방향이 맞았던 {rq['n_w0_right']}건 중")
        takeaway(
            "사건 정보로 예측을 고쳤을 때 <b>70%가 오히려 나빠졌습니다.</b> "
            "방향 정확도도 0.620 에서 0.500 으로 단조 하락합니다.")
        reading_guide(
            "막대가 낮을수록 정확합니다. W0 은 월초 시점, W4 는 월말까지 사건을 "
            "반영한 결과입니다.",
            "왼쪽에서 오른쪽으로 갈수록 **나빠집니다.**",
            "실제값은 **사후 채점용**이며 nowcast 시점에 알 수 있던 정보가 "
            "아닙니다. 그리고 비자명한 수정이 10건뿐이라 표본이 작습니다.")

    # ================= Event Design Diagnostic =========================
    elif v9_view == "Event Design Diagnostic":
        st.markdown("#### Event는 잘 잡고 있지만, 가격에 영향을 주는 Event를 "
                    "정확히 가려내고 있는가?")
        st.markdown(meta["v9_diagnostic_md"])
        d9 = v9["diagnostic"]["detection"]
        t9 = v9["diagnostic"]["transmission"]
        fig = go.Figure()
        fig.add_bar(x=["탐지 (Recall)", "정밀도 (Precision)",
                       "급변+신호에서 방향"],
                    y=[d9["recall"], d9["precision"],
                       t9["direction_M2XE_caseA"]],
                    marker_color=["#059669", "#F59E0B", "#DC2626"],
                    text=[f"{d9['recall']:.2f}", f"{d9['precision']:.2f}",
                          f"{t9['direction_M2XE_caseA']:.3f}"],
                    textposition="outside", showlegend=False)
        fig.add_hline(y=0.5, line=dict(color="#9CA3AF", width=1.4, dash="dash"))
        fig.add_annotation(xref="paper", x=0.99, y=0.5, xanchor="right",
                           text="동전 던지기 0.50", showarrow=False, yshift=11,
                           font=dict(size=11, color="#6B7280"))
        show(finish(
            fig, question="Q. Event를 잘 잡는가, 아니면 가격으로 잘 옮기는가?",
            title="탐지는 되는데 전달이 안 된다  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "↑ 높을수록 좋음</span>",
            ylab="비율", xlab="",
            footnote=f"급변 {d9['n_shock']}건 · 신호 {d9['n_signal']}개월  ·  "
                     f"{FOOT_EVENT}",
            height=450, legend=False, yrange=[0, 1.0]))
        with st.expander("채널별 진단 (제거·재가중하지 않습니다)"):
            ch = pd.DataFrame(v9["diagnostic"]["channels"])
            st.dataframe(
                ch[["label", "n_signal_months", "n_preceding_shock",
                    "precision", "beneficial_revision_rate"]]
                .rename(columns={"label": "채널", "n_signal_months": "신호월",
                                 "n_preceding_shock": "급변 선행",
                                 "precision": "정밀도",
                                 "beneficial_revision_rate": "유익한 수정률"}),
                hide_index=True, width="stretch")
        with st.expander("전달 시차 진단 (최적 시차를 모델에 넣지 않습니다)"):
            lg = pd.DataFrame(v9["diagnostic"]["lags"])
            st.dataframe(
                lg[["signal", "lag_months", "n_high", "shock_rate_when_high",
                    "shock_rate_when_low"]]
                .rename(columns={"signal": "신호", "lag_months": "시차(개월)",
                                 "n_high": "상위 20% 월수",
                                 "shock_rate_when_high": "그때 급변률",
                                 "shock_rate_when_low": "나머지 급변률"}),
                hide_index=True, width="stretch")

    # ================= Weekly Event Attribution ========================
    else:
        st.markdown("#### 어떤 사건이 언제 도착해 예측을 얼마나 바꿨나")
        wm = D["v9_weekly_month"].copy()
        at = D["v9_weekly_attr"].copy()
        has_ev = sorted(at.loc[at["n_new_events"] > 0, "target_month"].unique())
        if not has_ev:
            st.info("새 사건이 도착한 대상월이 없습니다.")
        else:
            tm = st.selectbox("대상월", has_ev, key="v9_attr_month")
            row = wm[wm["target_month"] == tm].iloc[0]
            sub = at[at["target_month"] == tm].sort_values("cut_date")
            wks = ["W0", "W1", "W2", "W3", "W4"]
            fig = go.Figure()
            fig.add_scatter(x=wks, y=[float(row[w]) for w in wks],
                            name="사건 반영 예측",
                            line=dict(color="#DB2777", width=2.6),
                            mode="lines+markers")
            fig.add_hline(y=float(row["W0"]),
                          line=dict(color="#0D9488", width=1.6, dash="dot"))
            fig.add_annotation(xref="paper", x=0.01, y=float(row["W0"]),
                               xanchor="left", showarrow=False, yshift=12,
                               text=f"월초 고정 baseline {float(row['W0']):.1f}",
                               font=dict(size=11.5, color="#0D9488"))
            fig.add_hline(y=float(row["y_true"]),
                          line=dict(color="#111827", width=1.6))
            fig.add_annotation(xref="paper", x=0.99, y=float(row["y_true"]),
                               xanchor="right", showarrow=False, yshift=12,
                               text=f"실제 {float(row['y_true']):.1f} (사후 채점)",
                               font=dict(size=11.5, color="#111827"))
            show(finish(
                fig, question="Q. 사건이 도착할 때 예측이 어디로 움직였는가?",
                title=f"{tm} — 사건 도착에 따른 월간 예측 수정  "
                      "<span style='font-size:13px;color:#6B7280'>"
                      "시장 정보는 월초에 고정</span>",
                ylab="철·강 스크랩 PPI 예측", xlab="정보 절단 시점",
                footnote="실제값은 **사후 채점용**이며 nowcast 시점에 알 수 "
                         f"없었습니다  ·  {FOOT_TARGET}",
                height=440, legend=False))
            st.dataframe(
                sub[["week", "cut_date", "n_new_events", "pep_increment",
                     "nep_increment", "channels"]]
                .rename(columns={"week": "주", "cut_date": "정보 절단일",
                                 "n_new_events": "새 사건 수",
                                 "pep_increment": "상방 압력 증가",
                                 "nep_increment": "하방 압력 증가",
                                 "channels": "채널"}),
                hide_index=True, width="stretch")
            st.caption(
                f"누적 사건 수정폭 **{float(row['cumulative_event_adjustment']):+.2f}** "
                "지수 Point. 새 사건이 하나도 없는 주는 수정폭이 정확히 0 입니다 — "
                "**사건만 예측을 움직이도록** 만들었기 때문입니다.")

    st.divider()
    st.error(meta["v9_promotion_md"])


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


    # =======================================================================
    # V10 — Event 이력 확장 · 전달 모델 · 교차 target · 주간 nowcast
    # =======================================================================
    st.divider()
    st.subheader("V10 — Event 이력을 2009년까지 늘리고, 전달 구조를 다시 설계했다")
    st.markdown(
        "V9 는 Event 실패의 **위치**를 특정했습니다 — 탐지도 타이밍도 표본도 아니고 "
        "**관련성 정밀도와 전달 특정성**이었습니다. V10 은 그 둘을 정면으로 다룹니다.")

    v10_view = st.radio(
        "어떤 관점을 볼까요?",
        ["Event History Expansion", "Transmission Model",
         "Cross-Target Matched History", "Cross-Target Maximum History",
         "Full Weekly Rolling Nowcast"],
        index=0, horizontal=True, key="v10_view")

    CT = V10["cross_target"]
    TL = CT["labels"]

    # ================= 1. Event History Expansion ======================
    if v10_view == "Event History Expansion":
        eh = V10["event_history"]
        st.markdown("#### 사람이 사건을 고르지 않았습니다")
        st.info(
            "V3 방식(사람이 공식 문서를 읽고 선정)은 2015-06 이전으로 확장할 때 "
            "**hindsight 를 배제했다고 증명할 수가 없습니다** — 과거 사건은 이미 결과가 "
            "알려져 있어서, 선의로 골라도 유명한 사건 쪽으로 기웁니다.  \n\n"
            "V10 은 방식을 바꿨습니다. **동결된 질의군으로 전수 취득 → 제목에 대한 "
            "결정적 함수로 편입.** 고르는 행위 자체가 없으므로 "
            "‘가격이 움직여서 골랐다’가 성립할 수 없습니다.")

        c = st.columns(4)
        c[0].metric("최초 Event 시점", eh["earliest_known_at"][:7],
                    delta=f"V9 {eh['v9_earliest_known_at'][:7]}", delta_color="off")
        c[1].metric("취득 문서", f"{eh['documents_fetched']:,}")
        c[2].metric("편입 레코드", f"{eh['records']:,}")
        c[3].metric("커버 개월", f"{eh['months_covered']} / 204",
                    delta="결측 연도 0", delta_color="off")

        by_year = D10["event_year"]
        fig = go.Figure()
        fig.add_bar(x=by_year["year"].astype(str), y=by_year["records"],
                    marker_color=["#94A3B8" if int(y) < 2015 else "#2563EB"
                                  for y in by_year["year"]],
                    text=by_year["records"], textposition="outside",
                    showlegend=False)
        fig.add_vline(x=5.5, line=dict(color="#DC2626", width=1.6, dash="dash"))
        fig.add_annotation(x=5.5, y=1.0, yref="paper", text="V9 의 Event 하한 (2015-06)",
                           showarrow=False, xanchor="left", xshift=6,
                           font=dict(size=11.5, color="#DC2626"))
        show(finish(
            fig, question="Q. Event 이력이 실제로 얼마나 늘었는가?",
            title="연도별 Event 레코드 수  "
                  "<span style='font-size:13px;color:#6B7280'>회색 = V9 가 "
                  "가지지 못했던 구간</span>",
            ylab="레코드 수", xlab="", height=420, legend=False))

        st.markdown("#### 구성")
        comp = D10["event_comp"]
        cc = st.columns(2)
        for col, dim, ko in ((cc[0], "family", "발행 기관·문서 유형"),
                             (cc[1], "channel", "전달 채널")):
            sub = comp[comp["dimension"] == dim]
            with col:
                fig = go.Figure()
                fig.add_bar(x=sub["records"], y=sub["value"], orientation="h",
                            marker_color="#0D9488",
                            text=sub["records"], textposition="outside",
                            showlegend=False)
                fig.update_yaxes(autorange="reversed")
                show(finish(fig, title=ko, ylab="", xlab="레코드 수",
                            height=360, legend=False))

        cc = st.columns(2)
        for col, dim, ko in ((cc[0], "stage", "조치 단계"),
                             (cc[1], "direction", "가격 압력 방향")):
            sub = comp[comp["dimension"] == dim]
            with col:
                fig = go.Figure()
                fig.add_bar(x=sub["records"], y=sub["value"], orientation="h",
                            marker_color="#7C3AED",
                            text=sub["records"], textposition="outside",
                            showlegend=False)
                fig.update_yaxes(autorange="reversed")
                show(finish(fig, title=ko, ylab="", xlab="레코드 수",
                            height=360, legend=False))

        st.markdown("#### 이 방식이 못 하는 것 — 미리 적어 둡니다")
        st.warning(
            f"**국가명으로 편입한 레코드가 {eh['producer_only_records']:,}건 있습니다.** "
            "제재 문서 제목에는 상품명이 없는 경우가 많아 국가명을 편입 어휘에 넣었는데, "
            "같은 국가명이 철강과 무관한 품목의 반덤핑 사건 제목에도 들어 있습니다 "
            "(새우·마늘·클립 등).  \n\n"
            "**여기서 규칙을 고치지 않았습니다.** 편입 규칙은 이미 동결됐고, 지금 손대면 "
            "‘결과를 보고 데이터를 고른 것’과 구별할 수 없습니다. 대신 다음 단계의 "
            "**target 별 관련성**이 이 문제를 처리합니다 — 국가 단위 제재는 그 나라의 "
            "상품 공급 전체에 작용하지만, 품목별 무역구제는 제목에 품목이 이미 적혀 "
            "있으므로 우리 사슬 밖이면 전달 경로가 없습니다.")

        st.markdown("#### hindsight 안전장치")
        st.dataframe(pd.DataFrame([
            {"안전장치": "프로토콜 동결이 취득보다 먼저",
             "확인": "git 커밋 순서로 강제 (테스트)"},
            {"안전장치": "사람이 개별 사건을 고르지 않음",
             "확인": "편입은 제목에 대한 결정적 함수"},
            {"안전장치": "구축 중 가격을 보지 않음",
             "확인": "구축 코드가 가격 모듈을 import 하지 않음 (AST 검사)"},
            {"안전장치": "표본추출 없음", "확인": "연도별 전수 취득, 상한 도달 시 중단"},
            {"안전장치": "known_at = 관보 게재일",
             "확인": "서명일이 게재일보다 뒤인 레코드 0건"},
            {"안전장치": "문서 본문 미저장", "확인": "메타데이터 필드만 보관"},
        ]), hide_index=True, width="stretch")

    # ================= 2. Transmission Model ===========================
    elif v10_view == "Transmission Model":
        tr = V10["transmission"]
        st.markdown("#### Event 하나가 예측에 닿기까지")
        st.markdown(
            "<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
            "border-radius:8px;padding:16px;font-size:14px;line-height:2.0'>"
            "<b>공식 문서</b> → <b>target 별 관련성</b> → <b>경제적 노출</b> → "
            "<b>신규성</b> → <b>전달 채널</b> → <b>기대 시차</b> → "
            "<b>방향 · 신뢰도</b> → <b>월별 압력</b></div>",
            unsafe_allow_html=True)
        st.caption("일곱 단계 전부 **성능을 보기 전에** 경제 논리로만 고정했습니다.")

        st.markdown("##### 1) target 별 관련성 — 여기가 V9 가 못 푼 지점입니다")
        rel = pd.DataFrame(tr["relevance"]).T
        rel.index = [TL.get(i, i) for i in rel.index]
        rel.columns = ["철강 사슬", "구리 사슬", "석유 사슬"]
        heat_table(rel, title="target 별 Event 관련성  "
                             "<span style='font-size:13px;color:#6B7280'>"
                             "1.00 = 그 상품 자체 · 0 = 전달 경로 없음</span>",
                   zmax=1.0, height=320)
        st.markdown(
            f"- 광역 거시 조치: **{tr['macro_wide']}** "
            "(단, `…Day/Week/Month, 20xx` 형태의 의례적 포고는 **0**)\n"
            f"- 국가명만 매치: **{tr['producer_country_level']}** — "
            "**국가 단위 수단일 때만** "
            f"({', '.join(x.replace('FR_', '') for x in tr['country_level_families'])})")

        st.markdown("##### 2) 기대 시차 — 성능이 좋은 lag 를 고르지 않았습니다")
        lag = pd.DataFrame(tr["expected_lag"]).T
        lag.index = [TL.get(i, i) for i in lag.index]
        lag.columns = ["무역정책", "지정학·공급", "수요·거시"]
        safe_table(lag.style.format("{:.0f}개월"), width="stretch")
        st.info(
            "원유는 연속 현물시장에서 세계적으로 **즉시** 재가격되므로 공급·지정학 "
            "충격이 당월에 도달합니다. 금속 원료는 물리적 계약·재고를 거쳐 한 달 "
            "정도 늦습니다.  \n\n"
            "V9 은 ‘lag 0~1 에서 lift 가 가장 크다’를 관측했지만 **그 사실을 이 표에 "
            "반영하지 않았습니다.** 반영했다면 그것이 성능 되먹임입니다.")

        st.markdown("##### 3) 노출 · 확실성 · 신규성")
        cc = st.columns(3)
        with cc[0]:
            st.markdown("**노출 — 수단의 제도적 폭**")
            st.dataframe(pd.DataFrame(
                [{"수단": k.replace("FR_", ""), "노출": v}
                 for k, v in tr["exposure_by_family"].items()]),
                hide_index=True, width="stretch")
        with cc[1]:
            st.markdown("**확실성 — 조치 단계**")
            st.dataframe(pd.DataFrame(
                [{"단계": k, "확실성": v} for k, v in tr["certainty_by_stage"].items()]),
                hide_index=True, width="stretch")
        with cc[2]:
            st.markdown("**신규성 배수**")
            st.dataframe(pd.DataFrame(
                [{"신규성": k, "배수": v} for k, v in tr["surprise_multiplier"].items()]),
                hide_index=True, width="stretch")
        st.caption(
            "관세율·교역액 같은 **수치 노출은 쓰지 않았습니다** — 과거 시점 기준으로 "
            "안전하게 재구성할 수 없기 때문입니다. 재구성 못 하는 값을 만들어 내지 "
            "않습니다.")

        st.markdown("#### 진단 — 기제는 살아났는데, 도움이 안 됩니다")
        dg = V10["scrap"]["diagnostics"]
        eb, rv = dg["event_block"], dg["revisions_m2_vs_m1"]
        c = st.columns(4)
        c[0].metric("Event 신호의 서로 다른 값",
                    f"{eb['ev_net_distinct_values']} / 50",
                    delta="V9 게이트는 사실상 상수였음", delta_color="off")
        c[1].metric("예측을 실제로 움직인 달", f"{rv['n_moved']} / 50")
        c[2].metric("평균 수정폭", f"{rv['mean_abs_revision']:.2f}")
        c[3].metric("유익한 수정률", f"{rv['beneficial_rate']:.2f}",
                    delta=f"유해 {rv['harmful_rate']:.2f}", delta_color="off")
        st.error(
            "**V9 과 결정적으로 다른 지점입니다.** V9 은 Event 게이트가 한 번도 열리지 "
            "않아서 ‘기제가 죽어 있다’로 설명할 수 있었습니다. V10 은 기제가 "
            f"**살아 있습니다** — 신호가 50개 시점에서 50개 서로 다른 값을 갖고, "
            f"50개 시점 **모두**에서 예측을 평균 {rv['mean_abs_revision']:.1f} 지수 "
            f"포인트만큼 움직입니다.  \n\n"
            f"그런데 그 움직임이 유익 {rv['beneficial_rate']:.2f} / "
            f"유해 {rv['harmful_rate']:.2f} 로 **동전 던지기와 구분되지 않습니다.**")

        st.markdown("#### 동결된 신호 정의가 퇴화했습니다 — 고치지 않고 보고합니다")
        sig = dg["v10_signal"]
        st.warning(
            f"성능을 보기 전에 ‘`ev_new > 0` 인 달을 Event 신호월로 본다’고 정의했는데, "
            f"레코드가 11,293건이라 **50개월 전부가 신호월**이 됐습니다 "
            f"(precision {sig['precision']} = 기저율 {sig['base_rate']}, "
            f"lift {sig['lift']}).  \n\n"
            "이 퇴화 자체가 결과이므로 **정의를 사후에 바꾸지 않았습니다.** "
            "퇴화를 설명하는 서술 진단은 별도로 기록했고 어떤 주장에도 쓰지 않습니다.")

    # ================= 3. Cross-Target Matched History =================
    elif v10_view == "Cross-Target Matched History":
        st.markdown("#### 1차 공정 비교 — 같은 창, 같은 학습행, 같은 예측시점")
        st.info(
            f"공통 학습 시작 **{CT['matched_train_start']}**, 예측시점 "
            f"**{CT['n_origins']}개**. 첫 시점에서 네 대상의 학습행이 "
            "**정확히 같습니다**. 절대 MAE 로 상품 간 순위를 매기지 않고 "
            "**상품 안에서의 상대 개선률**만 비교합니다 — 지수 단위·수준·변동성이 "
            "다르기 때문입니다.")

        rows = [r for r in CT["rows"] if r["mode"] == "MATCHED"]
        fig = go.Figure()
        fig.add_bar(x=[r["label"] for r in rows],
                    y=[r["history_to_market"] for r in rows],
                    name="시장정보 효과 (M0→M1)", marker_color="#0D9488",
                    text=[f"{r['history_to_market']:+.1f}%" for r in rows],
                    textposition="outside")
        fig.add_bar(x=[r["label"] for r in rows],
                    y=[r["event_incremental"] for r in rows],
                    name="Event 증분 효과 (M1→M2)", marker_color="#DB2777",
                    text=[f"{r['event_incremental']:+.1f}%" for r in rows],
                    textposition="outside")
        fig.add_hline(y=0, line=dict(color="#374151", width=1.2))
        fig.add_hline(y=3, line=dict(color="#DC2626", width=1.4, dash="dash"))
        fig.add_annotation(xref="paper", x=0.99, y=3, xanchor="right",
                           text="Event 성공 판정 임계 +3%", showarrow=False,
                           yshift=12, font=dict(size=11.5, color="#DC2626"))
        show(finish(
            fig, question="Q. Event 는 어떤 상품에서 통하는가?",
            title="같은 이력 조건에서의 상대 개선률  "
                  "<span style='font-size:13px;color:#6B7280'>양수 = 정보를 "
                  "더해서 좋아짐</span>",
            ylab="상대 개선률 (%)", xlab="", height=440))

        safe_table(pd.DataFrame([
            {"대상": r["label"], "M0": r["mae_M0"], "M1": r["mae_M1"],
             "M2": r["mae_M2"],
             "시장정보 효과 %": r["history_to_market"],
             "Event 증분 %": r["event_incremental"], "Event p": r["ev_p"],
             "방향 M1": r["direction_M1"], "방향 M2": r["direction_M2"],
             "유익한 수정률": r["beneficial"],
             "LOO 음수 개수": r["loo_below_zero"]}
            for r in rows]).style.format(
                {"M0": "{:.2f}", "M1": "{:.2f}", "M2": "{:.2f}",
                 "시장정보 효과 %": "{:+.2f}", "Event 증분 %": "{:+.2f}",
                 "Event p": "{:.3f}", "방향 M1": "{:.2f}", "방향 M2": "{:.2f}",
                 "유익한 수정률": "{:.2f}"}),
            hide_index=True, width="stretch")
        st.caption("M0/M1/M2 의 MAE 는 **같은 상품 안에서만** 비교하십시오. "
                   "네 지수는 단위가 다릅니다.")

        best = V10["success_criteria"]["best_cell"]
        st.error(
            f"**동결된 8조건을 통과한 대상이 하나도 없습니다.** 가장 좋았던 것은 "
            f"**{best['label']}**({best['mode']})의 "
            f"**{best['event_incremental']:+.2f}%** 인데, 동결 임계 **3%** 에 미달하고 "
            f"p = {best['p_value']} 로 사전 동결 추론도 지지하지 않습니다.  \n\n"
            "즉 **스크랩만 어려운 것이 아닙니다.** 이력 지지를 통제하면 Event 전달 "
            "표현은 네 상품 어디에서도 신뢰할 만한 증분을 내지 못합니다.")

    # ================= 4. Cross-Target Maximum History =================
    elif v10_view == "Cross-Target Maximum History":
        st.markdown("#### 2차 · 강건성 — 각 대상이 자기 최대 이력을 다 쓰면?")
        st.warning(
            "**이것은 1차 공정 비교가 아닙니다.** 대상마다 학습 이력의 길이가 다르므로 "
            "상품 간 우열의 근거로 쓰지 않고, **matched 결론이 뒤집히는지**만 봅니다.")

        pairs = []
        for t in CT["targets"]:
            m = next(r for r in CT["rows"] if r["target_id"] == t and r["mode"] == "MATCHED")
            x = next(r for r in CT["rows"] if r["target_id"] == t and r["mode"] == "MAXIMUM")
            pairs.append((m, x))
        fig = go.Figure()
        fig.add_bar(x=[p[0]["label"] for p in pairs],
                    y=[p[0]["event_incremental"] for p in pairs],
                    name="matched (1차)", marker_color="#2563EB",
                    text=[f"{p[0]['event_incremental']:+.1f}%" for p in pairs],
                    textposition="outside")
        fig.add_bar(x=[p[1]["label"] for p in pairs],
                    y=[p[1]["event_incremental"] for p in pairs],
                    name="maximum (2차)", marker_color="#94A3B8",
                    text=[f"{p[1]['event_incremental']:+.1f}%" for p in pairs],
                    textposition="outside")
        fig.add_hline(y=0, line=dict(color="#374151", width=1.2))
        show(finish(
            fig, question="Q. 이력을 더 주면 Event 가 살아나는가?",
            title="Event 증분 효과 — 이력 조건별  "
                  "<span style='font-size:13px;color:#6B7280'>양수 = Event 가 "
                  "도움</span>",
            ylab="Event 증분 개선률 (%)", xlab="", height=430))

        safe_table(pd.DataFrame([
            {"대상": p[0]["label"],
             "matched 학습행": p[0]["n_train_first"],
             "maximum 학습행": p[1]["n_train_first"],
             "maximum 학습시작": p[1]["first_train_month"],
             "M1 matched": p[0]["mae_M1"], "M1 maximum": p[1]["mae_M1"],
             "Event matched %": p[0]["event_incremental"],
             "Event maximum %": p[1]["event_incremental"]}
            for p in pairs]).style.format(
                {"M1 matched": "{:.2f}", "M1 maximum": "{:.2f}",
                 "Event matched %": "{:+.2f}", "Event maximum %": "{:+.2f}"}),
            hide_index=True, width="stretch")

        st.error(
            "**이력을 늘리면 Event 는 좋아지는 것이 아니라 나빠집니다.**  \n\n"
            "원유가 가장 선명합니다 — 학습행이 86 → 144 로 늘자 시장 모델(M1)이 "
            "**19% 좋아졌고**, 그와 함께 Event 의 +2.34% 가 −2.22% 로 뒤집혔습니다.  \n\n"
            "Event 가 하던 일은 ‘새 정보를 더하는 것’이 아니라 **약한 기준선의 빈틈을 "
            "메우는 것**이었다고 읽는 편이 자료와 더 잘 맞습니다. 기준선이 스스로 그 "
            "빈틈을 메우면 Event 는 남길 것이 없습니다.")

    # ================= 5. Full Weekly Rolling Nowcast ==================
    else:
        wk = V10["weekly"]
        if not wk.get("available"):
            st.info("주간 nowcast 산출물이 아직 없습니다.")
        else:
            st.markdown("#### 매주, 그 시점에 실제로 알려진 모든 정보로 다시 예측")
            st.info(
                "**V9 주간과 다릅니다.** V9 은 시장 baseline 을 W0 에 고정하고 "
                "**Event 만** 예측을 고치게 했습니다. V10 은 매주 M0·M1·M2 를 "
                "**전부 다시 적합**합니다.  \n\n"
                "주간 시장 계열은 쓰지 않았습니다(과거 시점 재구성이 불가능해 "
                "REJECT). 대신 **전월 PPI 가 대상월 중순에 발표**되므로 W2 부터 "
                "정보가 실제로 한 달 더 신선해집니다.")

            cc = st.columns(3)
            wt = cc[0].selectbox("대상", CT["targets"],
                                 format_func=lambda t: TL[t], key="v10_wk_t")
            wm = cc[1].selectbox("이력 조건", wk["modes"], key="v10_wk_m",
                                 format_func=lambda m: (
                                     "matched (1차 공정비교)" if m == "MATCHED"
                                     else "maximum (2차 강건성)"))
            wmod = cc[2].multiselect("표시할 모델", ["M0", "M1", "M2"],
                                     default=["M1", "M2"], key="v10_wk_mods")

            rows = [r for r in wk["metrics"]
                    if r["target_id"] == wt and r["mode"] == wm]
            colr = {"M0": "#2563EB", "M1": "#0D9488", "M2": "#DB2777"}
            name = {"M0": "과거 이력만 (M0)", "M1": "+ 시장정보 (M1)",
                    "M2": "+ Event (M2)"}
            fig = go.Figure()
            for mdl in ["M0", "M1", "M2"]:
                if mdl not in wmod:
                    continue
                sub = sorted([r for r in rows if r["model"] == mdl],
                             key=lambda r: r["stage"])
                fig.add_scatter(x=[r["stage"] for r in sub],
                                y=[r["mae"] for r in sub], mode="lines+markers+text",
                                name=name[mdl], line=dict(color=colr[mdl], width=2.6),
                                marker=dict(size=9),
                                text=[f"{r['mae']:.1f}" for r in sub],
                                textposition="top center")
            show(finish(
                fig, question="Q. 월이 흘러갈수록 예측이 좋아지는가?",
                title=f"{TL[wt]} — 주간 nowcast 궤적  "
                      "<span style='font-size:13px;color:#6B7280'>MAE ↓ "
                      "낮을수록 정확</span>",
                ylab="평균 예측오차 MAE (지수 Point)",
                xlab="대상월 안에서의 시점", height=440))

            m1 = [r for r in rows if r["model"] == "M1"]
            w0 = next((r["mae"] for r in m1 if r["stage"] == "W0"), None)
            w4 = next((r["mae"] for r in m1 if r["stage"] == "W4"), None)
            if w0 and w4:
                c = st.columns(3)
                c[0].metric("M1 · W0 (월 시작)", f"{w0:.2f}")
                c[1].metric("M1 · W4 (월 말)", f"{w4:.2f}",
                            delta=f"{100 * (w4 / w0 - 1):+.1f}%",
                            delta_color="inverse")
                ev = [r for r in wk["trajectory"]
                      if r["target_id"] == wt and r["mode"] == wm
                      and r["model"] == "EVENT_INCREMENT_W4"]
                if ev:
                    c[2].metric("W4 에서 Event 증분",
                                f"{ev[0]['event_incremental']:+.2f}%",
                                help="양수면 Event 가 그 시점에 도움이 됐다는 뜻")

            st.markdown("#### 주간 수정의 질")
            tr = [r for r in wk["trajectory"]
                  if r["target_id"] == wt and r["mode"] == wm
                  and r["model"] in ("M0", "M1", "M2")]
            safe_table(pd.DataFrame([
                {"모델": name[r["model"]], "W0 MAE": r["mae_W0"],
                 "W4 MAE": r["mae_W4"], "변화": r["change"],
                 "수정된 달": r["months_revised"],
                 "유익한 수정률": r["beneficial"], "유해한 수정률": r["harmful"],
                 "주간 구제율": r["rescue"], "잘못된 뒤집기": r["false_override"],
                 "방향이 처음 맞은 단계": r["first_correct_stage"]}
                for r in tr]).style.format(
                    {"W0 MAE": "{:.2f}", "W4 MAE": "{:.2f}", "변화": "{:+.2f}"},
                    na_rep="—"),
                hide_index=True, width="stretch")

            st.markdown("#### 네 대상을 한눈에 — W0 → W4 정확도 변화")
            fig = go.Figure()
            for mdl in ("M0", "M1", "M2"):
                ys = []
                for t in CT["targets"]:
                    r = next((x for x in wk["trajectory"]
                              if x["target_id"] == t and x["mode"] == wm
                              and x["model"] == mdl), None)
                    ys.append(100.0 * (r["mae_W4"] / r["mae_W0"] - 1.0)
                              if r and r["mae_W0"] else None)
                fig.add_bar(x=[TL[t] for t in CT["targets"]], y=ys, name=name[mdl],
                            marker_color=colr[mdl],
                            text=[f"{v:+.0f}%" if v is not None else "" for v in ys],
                            textposition="outside")
            fig.add_hline(y=0, line=dict(color="#374151", width=1.2))
            show(finish(
                fig, question="Q. 정보가 갱신되면 어떤 모델이 더 빨리 좋아지는가?",
                title="W0 → W4 오차 변화율  "
                      "<span style='font-size:13px;color:#6B7280'>음수 = "
                      "월이 흐르며 정확해짐</span>",
                ylab="MAE 변화율 (%)", xlab="", height=430))
            st.success(
                "**주간 nowcast 자체는 작동합니다.** 월 중순에 전월 PPI 가 발표되면 "
                "정보가 실제로 갱신되고 예측이 뚜렷하게 좋아집니다. 다만 그 이득은 "
                "**정보 갱신과 시장정보(M1)에서 오지, Event(M2)에서 오지 않습니다.**")

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
            "B. Event 연구 발전 과정 (V1 → V9)",
            "C. V5 통제 실험 (2×2)",
            "D. 진단 결과",
            "E. V7 위험·조건부 가치 실험 (전체 비교)",
            "F. V8 독립 신호 · 충격 구제 (전체 비교)",
            "G. V8 데이터 확장 타당성",
            "H. V9 장기 이력 · 주간 사건 (전체 비교)",
            "I. V10 Event 이력 확장 · 전달 모델 · 교차 대상 · 주간 nowcast",
            "J. 전체 Metrics Table",
            "K. 방법론 · 산출물",
        ])

    if section.startswith("A"):
        st.markdown("결과를 보기 **전에** 규칙을 고정한 실험의 원본 결과입니다. "
                    "이후 어떤 Demo 도 이 결과를 대체하지 않습니다.")
        om = D["official_metrics"]
        safe_table(
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
                    marker_color=[["#9CA3AF", "#D97706", "#BE185D", "#7C3AED",
                                   "#DB2777", "#0D9488", "#B45309"][i % 7]
                                  for i in range(len(ev))],
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
        st.markdown(
            "**V7 은 정확도가 아니라 위험을 물었습니다** — 예측 불확실성 구간, "
            "급등·급락 위험, 시장 상황별 조건부 효과, 발표창 신규 Event. "
            "여섯 가지 비교를 **하나도 빠짐없이** 싣습니다.")
        st.dataframe(pd.DataFrame([
            {"Track": c["track"], "비교": f"{c['base']} → {c['test']}",
             "지표": c["metric"], "차이": f"{c['diff']:+.4f}",
             "p": f"{c['p_value']:.5f}",
             "지위": "PRIMARY" if c["is_primary"] else "보조",
             "비고": c["support"] or "—"} for c in v7["comparisons"]]),
            hide_index=True, width="stretch")
        st.dataframe(
            D["v7_metrics"][["track", "model", "n", "interval_score",
                             "coverage", "average_width", "brier", "pr_auc",
                             "mae", "support"]]
            .rename(columns={"track": "Track", "model": "모델",
                             "n": "시점 수",
                             "interval_score": "Interval Score ↓",
                             "coverage": "커버리지", "average_width": "평균 폭",
                             "brier": "Brier ↓", "pr_auc": "PR-AUC ↑",
                             "mae": "MAE ↓", "support": "비고"}),
            hide_index=True, width="stretch")
        st.markdown(meta["v7_stop_rule_md"])
        st.download_button(
            "V7 시점별 원자료 CSV 내려받기",
            D["v7_risk"].to_csv(index=False).encode("utf-8-sig"),
            "steel_scrap_v7_risk_by_origin.csv", "text/csv")

    elif section.startswith("F"):
        st.markdown(
            "**V8 은 정확도가 아니라 구조를 물었습니다** — 가격이력에 종속되지 않은 "
            "독립 판단, 그리고 Event 가 기존 모델의 오판을 뒤집을 수 있는가. "
            "모든 모델과 모든 비교를 **하나도 빠짐없이** 싣습니다.")
        vm8 = D["v8_metrics"].copy()
        vm8["모델"] = vm8["model"].map(lambda m: v8["labels"].get(m, m))
        safe_table(
            vm8[["모델", "n", "mae_all", "mae_shock", "mae_normal",
                 "n_shock", "direction_accuracy", "direction_accuracy_shock"]]
            .rename(columns={"n": "시점 수", "mae_all": "MAE 전체 ↓",
                             "mae_shock": "MAE 급변 ↓",
                             "mae_normal": "MAE 평상 ↓", "n_shock": "급변 수",
                             "direction_accuracy": "방향 ↑",
                             "direction_accuracy_shock": "급변 방향 ↑"})
            .style.format({"MAE 전체 ↓": "{:.2f}", "MAE 급변 ↓": "{:.2f}",
                           "MAE 평상 ↓": "{:.2f}", "방향 ↑": "{:.3f}",
                           "급변 방향 ↑": "{:.3f}"}),
            hide_index=True, width="stretch")

        st.markdown("##### 구제 지표 전체")
        vr8 = D["v8_rescue"].copy()
        vr8["후보"] = vr8["candidate"].map(lambda m: v8["labels"].get(m, m))
        st.dataframe(
            vr8[["후보", "rescue_rate", "rescues", "base_wrong_cases",
                 "false_override_rate", "false_overrides", "base_correct_cases",
                 "rescue_precision", "substantial_departures"]]
            .rename(columns={"rescue_rate": "구제율 ↑", "rescues": "구제",
                             "base_wrong_cases": "기본 오답",
                             "false_override_rate": "잘못된 뒤집기 ↓",
                             "false_overrides": "오작동",
                             "base_correct_cases": "기본 정답",
                             "rescue_precision": "이탈 정확도 ↑",
                             "substantial_departures": "실질 이탈"}),
            hide_index=True, width="stretch")

        st.markdown("##### 유의성 — 급변 구간은 계산하지 않습니다")
        vc8 = D["v8_cmp"].copy()
        vc8["비교"] = vc8["test"].map(lambda m: v8["labels"].get(m, m))
        st.dataframe(
            vc8[["비교", "scope", "diff", "p_value", "inference", "support"]]
            .rename(columns={"scope": "범위", "diff": "MAE 차이",
                             "p_value": "p", "inference": "추론 상태",
                             "support": "비고"}),
            hide_index=True, width="stretch")
        st.warning(
            "급변이 **8개월**뿐이라 사용하는 통계 절차(블록 길이 12)가 "
            "**퇴화합니다** — 모든 재표본이 원본과 같아져 p 값이 0 또는 1 로 "
            "붕괴합니다. 그것은 유의성이 아니라 계산 붕괴이므로 "
            "`INVALID_MBB_DEGENERATE` 로 표시하고 수치를 내지 않습니다. "
            "**블록 길이를 줄여 \"돌아가게\" 만들지 않았습니다** — 그것은 결과를 "
            "본 뒤의 조정입니다.")
        st.download_button(
            "V8 시점별 원자료 CSV 내려받기",
            D["v8_pred"].to_csv(index=False).encode("utf-8-sig"),
            "steel_scrap_v8_by_origin.csv", "text/csv")

    elif section.startswith("G"):
        st.markdown("#### 표본을 늘릴 수 있는가 (V8 데이터 확장 타당성)")
        st.info(
            "**새 데이터는 V8 성능에 전혀 사용하지 않았습니다.** 이 절은 "
            "\"표본을 늘릴 수 있는가\"에 대한 조사 결과일 뿐입니다.")

        dr = v8["data_rights"]
        c = st.columns(4)
        c[0].metric("판정한 소스", f"{dr['total']}개")
        c[1].metric("통과 (PASS)", f"{dr['pass']}개")
        c[2].metric("보류 (REVIEW)", f"{dr['review']}개",
                    help="모델링 목적에서 배제와 동일하게 취급합니다")
        c[3].metric("배제 (REJECT)", f"{dr['reject']}개")
        st.caption(
            f"**V8 모델링에 쓴 {dr['used_in_modeling']}종은 전부 통과 등급이며, "
            "새로 들어간 소스는 0건입니다.** 재사용 권리가 불분명하면 쓰지 "
            "않습니다 — 성능이 이 규칙을 뒤집지 못합니다.")

        st.markdown("##### 시장 변수를 버려서 창을 늘릴 수 있을까")
        st.markdown(meta["v8_expansion_md"])
        cc = pd.DataFrame(v8["expansion"]["core_comparison"])
        cc["구성"] = cc["core"].map({
            "CURRENT_CORE": "현행 (시장 변수 6)",
            "DROP_BLS_PPI_X": "BLS PPI 계열 제외 (4)",
            "FED_G17_ONLY": "연준 계열만 (3)",
            "LONGEST_SINGLE_X": "가장 긴 변수 1개만"})
        st.dataframe(
            cc[["구성", "n_x", "x_start", "common_start", "gain_months"]]
            .rename(columns={"n_x": "시장 변수 수", "x_start": "시장 공통 시작",
                             "common_start": "전체 공통 시작",
                             "gain_months": "이득(개월)"}),
            hide_index=True, width="stretch")

        st.markdown("##### 늘렸다면 얼마나 좋아졌을까 (계획값 — 실측 아님)")
        pj = pd.DataFrame(v8["expansion"]["projection"])
        fig = go.Figure()
        fig.add_bar(x=pj["shift"], y=pj["origins"], name="예측시점",
                    marker_color="#0D9488",
                    text=pj["origins"], textposition="outside")
        fig.add_bar(x=pj["shift"], y=pj["shocks"], name="급변 사례",
                    marker_color="#DC2626",
                    text=pj["shocks"], textposition="outside")
        fig.update_layout(barmode="group")
        show(finish(
            fig, question="Q. 과거 이력을 늘리면 표본이 얼마나 늘어나는가?",
            title="3년을 늘려도 급변은 14개월  "
                  "<span style='font-size:13px;color:#6B7280'>"
                  "취득 가능성을 확인하기 전에는 계획값입니다</span>",
            ylab="개수", xlab="예측 대상 시작을 앞당기는 정도",
            footnote="규칙 산술로 계산한 계획값 — 실측이 아닙니다  ·  "
                     + FOOT_TARGET,
            height=430))
        takeaway(
            "V8 의 핵심 질문이 <b>급변 8개월</b>에 걸려 있습니다. 3년을 늘려도 "
            "14개월입니다 — 이 트랙이 왜 중요한지, 그리고 왜 3년으로도 충분하지 "
            "않을지를 동시에 보여 줍니다.")

        with st.expander("계열별 확장 판정"):
            fe = pd.DataFrame(v8["expansion"]["feasibility"])
            st.dataframe(
                fe.rename(columns={"series": "계열", "role": "역할",
                                   "org": "원기관", "start": "관측 시작",
                                   "months": "개월", "verdict": "판정"}),
                hide_index=True, width="stretch")

        with st.expander("주간 데이터로 표본을 4배 만들 수 있을까"):
            st.markdown(meta["v8_weekly_md"])
            st.code(
                "        예측 대상: 월 T 의 철·강 스크랩 PPI" + NL +
                "                          ↑" + NL +
                "        ┌─────────┬─────────┬─────────┬─────────┐" + NL +
                "      4주 전    3주 전    2주 전    1주 전" + NL +
                "       최초      갱신      갱신      갱신",
                language=None)

        with st.expander("데이터 권리 판정 전체"):
            st.dataframe(
                pd.DataFrame(dr["rows"]).rename(
                    columns={"name": "데이터셋", "org": "기관",
                             "status": "판정", "used": "V8 사용",
                             "free": "무료", "checked": "확인일"}),
                hide_index=True, width="stretch")

    elif section.startswith("H"):
        st.markdown(
            "**V9 는 모델이 아니라 데이터를 바꿨습니다** — 예측 대상 50개월을 그대로 "
            "두고 과거 학습정보만 늘렸습니다. 모든 모델과 비교를 하나도 빠짐없이 "
            "싣습니다.")
        safe_table(
            D["v9_metrics"][["model", "n", "mae", "rmse", "mae_shock",
                             "mae_normal", "direction_accuracy",
                             "is_legacy_frozen"]]
            .rename(columns={"model": "모델", "n": "시점 수", "mae": "MAE ↓",
                             "rmse": "RMSE ↓", "mae_shock": "MAE 급변 ↓",
                             "mae_normal": "MAE 평상 ↓",
                             "direction_accuracy": "방향 ↑",
                             "is_legacy_frozen": "동결본"})
            .style.format({"MAE ↓": "{:.2f}", "RMSE ↓": "{:.2f}",
                           "MAE 급변 ↓": "{:.2f}", "MAE 평상 ↓": "{:.2f}",
                           "방향 ↑": "{:.3f}"}),
            hide_index=True, width="stretch")

        st.markdown("##### 사전 선언된 비교")
        st.dataframe(
            D["v9_cmp"][["question", "base", "test", "mae_base", "mae_test",
                         "rel_improvement_pct", "p_value", "ci_low", "ci_high",
                         "inference"]]
            .rename(columns={"question": "질문", "base": "기준", "test": "비교",
                             "mae_base": "MAE 기준", "mae_test": "MAE 비교",
                             "rel_improvement_pct": "상대(%)", "p_value": "p",
                             "ci_low": "CI 하한", "ci_high": "CI 상한",
                             "inference": "추론"}),
            hide_index=True, width="stretch")
        st.caption(
            "**p 와 신뢰구간은 서로 다른 절차입니다.** p 는 재표본 평균분포를 "
            "관측평균에 중심화한 귀무분포에서 나오고, 구간은 중심화하지 않은 "
            "백분위 구간이라 검정의 역산이 아닙니다. 분포가 비대칭이면 둘이 "
            "어긋날 수 있고, 그때는 **보수적인 쪽(검정)을 따릅니다.**")

        st.markdown("##### 주간 사건 nowcast")
        st.dataframe(
            pd.DataFrame(v9["weekly"]["by_week"])
            .rename(columns={"week": "주", "mae": "MAE ↓", "rmse": "RMSE ↓",
                             "direction_accuracy": "방향 ↑",
                             "median_abs_revision": "median |수정|",
                             "n_nontrivial_revisions": "비자명 수정"}),
            hide_index=True, width="stretch")
        st.download_button(
            "V9 시점별 원자료 CSV 내려받기",
            D["v9_pred"].to_csv(index=False).encode("utf-8-sig"),
            "steel_scrap_v9_by_origin.csv", "text/csv")

    elif section.startswith("I"):
        st.markdown("#### V10 — 다섯 갈래를 한 번에 물었습니다")
        st.markdown(
            "V10 은 하나의 성공/실패 라벨로 뭉치지 않습니다. 각 갈래를 따로 보고합니다.")
        eh = V10["event_history"]
        st.dataframe(pd.DataFrame([
            {"갈래": "A. Event 이력 확장", "무엇을 했나":
                f"Federal Register 공개 API 로 2009-01 까지 소급 "
                f"({eh['v9_records']}건 → {eh['records']:,}건)",
             "결과": "이력은 늘었으나 M2 는 사실상 무변화 "
                     f"({V10['scrap']['event_history_expansion_effect_pct']:+.2f}%)"},
            {"갈래": "B. Event 전달 표현", "무엇을 했나":
                "관련성·노출·신규성·채널·시차·방향·신뢰도 7단계 온톨로지",
             "결과": "기제는 살아났지만(신호 50개 서로 다른 값) 수정이 무익 "
                     "(유익 0.48 / 유해 0.52)"},
            {"갈래": "C. Target-Specific X", "무엇을 했나":
                "대상마다 ‘같은 사슬의 전방 제품 + 공통 에너지’ 설계",
             "결과": "구리에서 +22%, 철광석 maximum 에서 −19% — 상품마다 크게 다름"},
            {"갈래": "D. 교차 대상 검증", "무엇을 했나":
                "matched(1차) + maximum(2차), 네 대상 같은 50개월",
             "결과": "동결 8조건을 통과한 대상 0 — 스크랩만의 문제가 아님"},
            {"갈래": "E. 완전 주간 nowcast", "무엇을 했나":
                "매주 M0/M1/M2 전부 재적합 (2,000행)",
             "결과": "**작동한다** — 월중 오차가 26~48% 감소. 다만 이득은 정보 갱신에서"},
        ]), hide_index=True, width="stretch")

        st.markdown("#### 스크랩 결과 계층 — 낡은 기준선을 이겼다고 성공이라 하지 않습니다")
        mae = V10["scrap"]["mae"]
        order = [("FROZEN_M0", "낡은 이력 기준선 (M0)"),
                 ("FROZEN_M2_Gate_v8", "V8 Event 게이트"),
                 ("M0_MAX", "V10 장기 이력 (M0)"),
                 ("M1_MAX", "+ 시장정보 (M1)"),
                 ("M2_LEGACYWIN_MAX", "+ Event · 2015년 이후 이력"),
                 ("M2_MAX", "+ Event · 2009년 이후 이력")]
        vals = [mae[k] for k, _ in order]
        fig = go.Figure()
        fig.add_bar(x=[lab for _, lab in order], y=vals,
                    marker_color=["#9CA3AF", "#9CA3AF", "#059669", "#0D9488",
                                  "#F59E0B", "#DB2777"],
                    text=[f"{v:.2f}" for v in vals], textposition="outside",
                    showlegend=False)
        fig.add_hline(y=mae["M0_MAX"], line=dict(color="#059669", width=1.6,
                                                 dash="dash"))
        show(finish(
            fig, question="Q. Event 를 더한 모델이 최강 비-Event 기준선을 이겼는가?",
            title="같은 50개월 · 스크랩  "
                  "<span style='font-size:13px;color:#6B7280'>MAE ↓ 낮을수록 정확</span>",
            ylab="평균 예측오차 MAE (지수 Point)", xlab="",
            footnote=FOOT_TARGET, height=430, legend=False))
        st.error(
            "**Event 이력을 2015년 이후에서 2009년 이후로 늘려도 결과가 거의 그대로입니다"
            f"({V10['scrap']['event_history_expansion_effect_pct']:+.2f}%).** "
            "V9 이 남긴 ‘Event 이력이 부족해서 실패한 것 아닌가’라는 물음에 대한 답은 "
            "**아니오** 입니다.")

        st.markdown("#### 사전 동결한 8조건 — 적용 결과")
        sc = V10["success_criteria"]
        st.dataframe(pd.DataFrame([
            {"#": k, "조건": v,
             "결과": "✗ 실패" if k in sc["failed_conditions"] else "✓"}
            for k, v in sc["conditions"].items()]),
            hide_index=True, width="stretch")
        st.warning(f"**승격하지 않습니다.** {sc['reason']}")
        st.download_button(
            "V10 교차 대상 상대 skill CSV 내려받기",
            D10["cross_skills"].to_csv(index=False).encode("utf-8-sig"),
            "steel_scrap_v10_cross_target_skills.csv", "text/csv")

    elif section.startswith("J"):
        st.markdown("모든 실험의 전체 지표입니다. **하나도 삭제되지 않았습니다.**")
        vm = D["v5_metrics"].copy()
        vm["모델"] = vm["model"].map(lambda m: LABEL.get(m, m))
        vm["지위"] = vm["status"].map(
            {"OFFICIAL_PREREGISTERED": "공식 사전등록", "EXPLORATORY": "탐색적 확장"})
        safe_table(
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
            f"- V7 방법론 동결본: `{v7['freeze_version']}` "
            "(예측 결과를 보기 **전에** 커밋)\n"
            f"- V7 점 예측 재설계: "
            f"**{'아니오' if v7['point_forecast_frozen_from_v5'] else '예'}** "
            "(V5 의 M1* 를 그대로 사용)\n"
            f"- V7 새 사건 기록 추가: "
            f"**{'예' if v7['new_event_records_added'] else '아니오'}**\n"
            f"- V7 중단 규칙 발동: "
            f"**{'예' if v7['stop_rule_triggered'] else '아니오'}**\n"
            f"- V8 방법론 동결본: `{v8['freeze_version']}` "
            "(예측 결과를 보기 **전에** 커밋)\n"
            f"- V8 연구 지위: **탐색적 구조 연구** "
            "(이미 관측된 구간에서 동기를 얻었으므로 확증 근거가 아님)\n"
            f"- V8 확장 데이터 성능 사용: "
            f"**{'예' if v8['expanded_pit_data_used'] else '아니오'}**\n"
            f"- V8 주간 데이터 성능 사용: "
            f"**{'예' if v8['weekly_data_used'] else '아니오'}**\n"
            f"- V9 방법론 동결본: `{v9['freeze_version']}` "
            "(예측 결과를 보기 **전에** 커밋)\n"
            f"- V9 예측 대상 월 변경: "
            f"**{'아니오' if v9['test_window_unchanged'] else '예'}** "
            "(V5/V6/V8 과 동일한 50개월)\n"
            f"- V9 공식 사건 기록 확장: "
            f"**{'예' if v9['event_history_expanded'] else '아니오'}**\n"
            f"- V9 기본 화면 승격: "
            f"**{'예' if v9['promotion']['promoted'] else '아니오'}** "
            "(동결 규칙 조건 5 실패)\n"
            f"- 새 외부 데이터 추가: **{'예' if v5['new_raw_x_added'] else '아니오'}**\n"
            f"- 공식 사건 기록 변경: "
            f"**{'예' if v5['event_registry_changed'] else '아니오'}**\n"
            f"- Event 신뢰도 문턱: **{v5['selection_margin']:.0%}** "
            "(난수 실험으로 보정)\n"
            f"- 자동 테스트: **{k['n_tests']}개**")
        st.markdown("#### 동봉 문서")
        for label, path in (("경영진 요약", "docs/executive_summary.md"),
                            ("방법론 요약", "docs/methodology_summary.md"),
                            ("V9 결과와 해석", "docs/findings_v9.md"),
                            ("V8 결과와 해석", "docs/findings_v8.md"),
                            ("V8 데이터 확장 타당성", "docs/data_expansion_v8.md"),
                            ("V7 결과와 해석", "docs/findings_v7.md"),
                            ("다음 단계 계획", "docs/next_phase_plan.md"),
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
    f"V5 동결 `{v5['freeze_version']}` · V7 동결 `{v7['freeze_version']}` · "
    f"V8 동결 `{v8['freeze_version']}` · V9 동결 `{v9['freeze_version']}` · "
    f"생성 {meta['exported_at']}"
)
