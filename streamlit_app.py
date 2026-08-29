"""Commodity Intelligence — 공식 데이터 공개 시점 기반 Rolling Nowcast.

Streamlit 2.0 (Demo V11). 5개 상위 페이지:

    개요 · Rolling Nowcast · 리서치 분석 · 데이터 & 방법 · 연구 여정

## 왜 구조를 바꿨나

V1~V10 의 화면은 "Event Intelligence" 를 중심으로 쌓여 왔다. V10 이 그 축을 끝냈다 —
Event 는 네 상품 어디에서도 신뢰할 만한 증분을 내지 못했고, 대신 **정보가 도착하는
구조**가 예측을 크게 개선했다. 화면은 현재 연구를 비춰야 하므로 중심을 옮긴다.

**과학적 이력은 그대로 보존된다** — Git · 동결본 · 산출물 · 문서 · 연구 여정 페이지.
바뀐 것은 내비게이션이지 결과가 아니다.

## Cloud 안전 규약

- 선택적 스타일 의존성(matplotlib 등)을 쓰지 않는다.
- 표 하나의 실패가 페이지를 죽이지 못한다(`safe_table`).
- 모든 선택 경로를 AppTest 로 점검한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
ASSETS = Path(__file__).parent / "assets"

MODEL_COLOR = {"M0": "#2563EB", "M1": "#0D9488", "M2": "#DB2777"}
MODEL_NAME = {"M0": "과거 이력만 (M0)", "M1": "+ 시장·산업 (M1)",
              "M2": "+ Material Event (M2)"}
ACTUAL_COLOR = "#111827"
STAGES = ["W0", "W1", "W2", "W3", "W4"]
STAGE_HELP = {"W0": "대상월 전월 말일", "W1": "대상월 7일", "W2": "대상월 14일",
              "W3": "대상월 21일", "W4": "대상월 말일"}
MODE_LABEL = {"MATCHED": "공통 이력 (1차 비교)", "MAXIMUM": "최대 이력 (2차 강건성)"}

FOOT_SOURCE = ("출처: U.S. Bureau of Labor Statistics · Producer Price Index "
               "(public domain) · Federal Register API (public domain)")
FOOT_PIT = ("각 시점에서 그때 실제로 공개돼 있던 값만 사용(true Point-in-Time). "
            "지수는 $/ton 거래가격이 아니라 생산자물가지수입니다.")

st.set_page_config(page_title="Commodity Intelligence", page_icon="📦",
                   layout="wide")


# ---------------------------------------------------------------------------
# 데이터
# ---------------------------------------------------------------------------

@st.cache_data
def load() -> dict:
    d: dict = {}
    for key, name in (
        ("stage", "demo_v11_stage_metrics.csv"),
        ("traj", "demo_v11_trajectory_metrics.csv"),
        ("release", "demo_v11_release_effect.csv"),
        ("vintage", "demo_v11_forecast_vintage.csv"),
        ("arrivals", "demo_v11_release_arrivals.csv"),
        ("targets", "demo_v11_targets.csv"),
        ("rights", "demo_v11_rights.csv"),
        ("material", "demo_v11_material_events.csv"),
    ):
        d[key] = pd.read_csv(DATA / name)
    d["meta"] = json.loads((DATA / "v11_metadata.json").read_text(encoding="utf-8"))
    p = DATA / "run_metadata.json"          # Agent Team 등 이전 세대 자산
    d["legacy"] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return d


D = load()
M = D["meta"]
TL = M["targets"]["labels"]
PRIMARY = M["targets"]["primary"]


# ---------------------------------------------------------------------------
# 렌더 헬퍼
# ---------------------------------------------------------------------------

def finish(fig: go.Figure, *, title: str, question: str | None = None,
           ylab: str = "", xlab: str = "", footnote: str | None = None,
           height: int = 430, legend: bool = True) -> go.Figure:
    head = f"<b>{title}</b>"
    if question:
        head = (f"<span style='font-size:13.5px;color:#6B7280'>{question}</span>"
                f"<br>{head}")
    fig.update_layout(
        title=dict(text=head, x=0.0, xanchor="left", font=dict(size=17)),
        margin=dict(t=88, b=54, l=64, r=24), height=height,
        plot_bgcolor="white", paper_bgcolor="white", showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        font=dict(size=13))
    fig.update_xaxes(title_text=xlab, showgrid=False, linecolor="#D1D5DB")
    fig.update_yaxes(title_text=ylab, gridcolor="#F1F5F9", linecolor="#D1D5DB")
    if footnote:
        fig.add_annotation(xref="paper", yref="paper", x=0, y=-0.21,
                           text=f"<span style='font-size:11.5px;color:#6B7280'>"
                                f"{footnote}</span>",
                           showarrow=False, xanchor="left")
    return fig


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def safe_table(obj, **kw) -> None:  # noqa: ANN001
    """표 하나의 스타일링 실패가 페이지 전체를 죽이지 못하게 한다.

    Streamlit Cloud 는 requirements.txt 에 적힌 것만 설치한다. pandas Styler 의 일부
    기능은 별도 패키지를 요구하는데 로컬에는 딸려 들어와 있어 로컬만 통과하고 Cloud
    에서 오류 상자가 뜬다(V10 에서 실제로 발생). 실패하면 원본 표로 강등한다.
    """
    try:
        st.dataframe(obj, **kw)
        return
    except Exception:                                   # noqa: BLE001
        pass
    try:
        st.dataframe(obj.data if hasattr(obj, "data") else obj, **kw)
        st.caption("표 서식을 적용하지 못해 원본 값으로 표시합니다.")
    except Exception:                                   # noqa: BLE001
        st.warning("이 표를 표시하지 못했습니다. 다른 내용은 정상입니다.")


def reading_guide(how: str, now: str, caution: str) -> None:
    a, b, c = st.columns(3)
    a.markdown(f"**이 그래프를 보는 법**  \n{how}")
    b.markdown(f"**지금의 발견**  \n{now}")
    c.markdown(f"**주의**  \n{caution}")


def traj_row(target: str, mode: str, model: str):  # noqa: ANN201
    t = D["traj"]
    r = t[(t.target_id == target) & (t.history_mode == mode) & (t.model == model)]
    return r.iloc[0] if len(r) else None


def skill_rows(target: str, mode: str) -> pd.DataFrame:
    s = D["stage"]
    r = s[(s.target_id == target) & (s.history_mode == mode) & (s.model == "SKILL")]
    return r.set_index("stage").reindex(STAGES).reset_index()


# ---------------------------------------------------------------------------
# 머리말
# ---------------------------------------------------------------------------
st.title(M["title"])
st.markdown(f"### {M['subtitle']}")
st.caption(M["technical_subtitle"])
st.markdown(f"> {M['origin_note']}  \n"
            "> 연구 데모입니다. 상용 제품이나 투자 판단 도구가 아닙니다.")

tabs = st.tabs(["📌 개요", "🔄 Rolling Nowcast", "🔬 리서치 분석",
                "🧾 데이터 & 방법", "🗂️ 연구 여정"])

# ===========================================================================
# 1. 개요
# ===========================================================================
with tabs[0]:
    st.subheader("지금까지 확인된 것")
    sc = M["rolling"]["skill"]
    scrap = sc.get("SCRAP|MATCHED", {})

    c = st.columns(4)
    c[0].metric("더 긴 과거 정보의 효과", "+7.4%", delta="V9 · p=0.045",
                delta_color="off",
                help="과거 이력 69개월 확장으로 과거이력 모델 MAE 49.19 → 45.57")
    c[1].metric("공식 사건 정보 확장 효과", "≈ 0%", delta="V10 · 51건 → 11,293건",
                delta_color="off", help="사건 기록을 220배로 늘려도 예측이 사실상 불변")
    c[2].metric("월중 정보 갱신 효과",
                f"+{scrap.get('rolling_skill_W4_pct', 0):.0f}%",
                delta="V11 · 스크랩 W0→W4", delta_color="off",
                help="같은 달 안에서 공식 정보가 도착할수록 예측이 좋아지는 정도")
    c[3].metric("사용한 유료 데이터", f"{M['rights']['paid_sources_used']}건",
                delta=f"공식 기관 {len(M['rights']['organizations'])}곳",
                delta_color="off")

    st.divider()
    a, b = st.columns(2)
    with a:
        st.markdown("#### ① 더 긴 과거 정보는 확실히 도움이 됐다")
        st.markdown(
            "BLS 공식 문서만으로 과거 이력을 **69개월** 되살리자 과거이력 모델의 오차가 "
            "**49.19 → 45.57 (p=0.045)** 로 줄었습니다. 이 프로젝트 최초의 유의한 "
            "개선이었고, **더 나은 모델이 아니라 더 많은 데이터**에서 왔습니다.")
        st.markdown("#### ② 공식 사건 정보는 늘려도 도움이 되지 않았다")
        st.markdown(
            f"관보에서 사건 기록을 **{M['event']['broad_documents']:,}건**까지 늘리고 "
            "전달 구조를 다시 설계했지만 개선이 없었습니다. 기제가 죽어서가 아닙니다 — "
            "**신호가 매달 움직이는데도** 그 움직임이 동전 던지기와 구분되지 않았습니다.")
    with b:
        st.markdown("#### ③ 정보가 **언제** 도착하는지가 컸다")
        st.markdown(
            "월 중순에 전월 공식 지수가 발표되면 예측 오차가 크게 줄었습니다. "
            "모델을 바꾼 것이 아니라 **그 시점에 알려진 정보로 다시 계산**했을 뿐입니다.")
        st.markdown("#### ④ 그래서 V11 이 묻는 것")
        st.markdown(
            "> 공식 정보가 시간에 따라 도착할 때 **무엇이 실제로 예측을 개선하는가**, "
            "그리고 경제적으로 **material 한 희소 사건**은 그 위에 무언가를 더하는가?")

    st.divider()
    st.markdown("#### 대표 그림 — 같은 달 안에서 예측이 어떻게 좋아지는가")
    fig = go.Figure()
    for t in PRIMARY:
        r = traj_row(t, "MATCHED", "M1")
        if r is None:
            continue
        base = float(r["mae_W0"])
        ys = [100.0 * (float(r[f"mae_{s}"]) / base - 1.0) for s in STAGES]
        fig.add_scatter(x=STAGES, y=ys, mode="lines+markers+text", name=TL[t],
                        line=dict(width=3), marker=dict(size=10),
                        text=[f"{v:+.0f}%" for v in ys], textposition="bottom center")
    fig.add_hline(y=0, line=dict(color="#374151", width=1.2))
    show(finish(fig, question="Q. 월이 흘러 공식 정보가 도착하면 예측이 좋아지는가?",
                title="세 상품 모두 같은 달 안에서 예측이 개선된다  "
                      "<span style='font-size:13px;color:#6B7280'>W0 대비 오차 변화 · "
                      "시장·산업 정보 모델</span>",
                ylab="W0 대비 오차 변화 (%)",
                xlab="예측 시점 (W0=전월 말일 · W4=대상월 말일)",
                footnote=FOOT_SOURCE, height=450))
    reading_guide(
        how="가로축은 **같은 달을 예측한 다섯 시점**입니다. 아래로 내려갈수록 정확합니다.",
        now="W0·W1 은 **정확히 같고 W2 에서 크게 떨어집니다** — 전월 공식 지수가 그때 발표됩니다.",
        caution="**50개월 다년 과거 아웃오브샘플 평가창**이며, 같은 50개월을 V5~V11 에 "
                "걸쳐 반복 관측했습니다. 한 번도 보지 않은 외부 검증창은 아닙니다.")

    st.info(
        "**50개월 전체를 예측 대 실제로 보려면** → `🔄 Rolling Nowcast` 탭 첫 화면. "
        "**한 번도 보지 않은 관측을 어떻게 쌓는지** → `🧾 데이터 & 방법` 탭의 전향 검증.")

# ===========================================================================
# 2. ROLLING NOWCAST
# ===========================================================================
with tabs[1]:
    st.subheader("Rolling Nowcast — 매주 다시 계산하는 월간 예측")
    st.markdown(
        "대상월 하나를 **다섯 시점**에서 예측합니다. 각 시점에서 그때 실제로 공개돼 "
        "있던 정보만 씁니다. **예측 대상은 그대로이고 정보만 늘어납니다.**")

    # -- 50개월 아웃오브샘플 검증 -------------------------------------------
    st.markdown("#### 50개월 아웃오브샘플 검증 — 예측과 실제값을 나란히")
    st.markdown(
        "한 달만 보면 운이 좋았는지 알 수 없습니다. 아래는 **평가창 전체**입니다 — "
        "매달 그 시점에 알려진 정보만으로 다시 예측했고, 실제값은 나중에 확정된 값입니다.")

    o = st.columns([1.1, 1.1, 1.1, 1.6])
    o_t = o[0].selectbox("상품", PRIMARY, format_func=lambda t: TL[t], key="oos_t")
    o_m = o[1].selectbox("이력 조건", ["MATCHED", "MAXIMUM"], key="oos_m",
                         format_func=lambda m: MODE_LABEL[m])
    o_mdl = o[2].selectbox("모델", ["M0", "M1", "M2"], index=1, key="oos_mdl",
                           format_func=lambda m: MODEL_NAME[m])
    o_st = o[3].multiselect("표시할 예측 시점", STAGES, default=["W0", "W4"],
                            key="oos_stages",
                            format_func=lambda s: f"{s} · {STAGE_HELP[s]}")

    ov = D["vintage"]
    ov = ov[(ov.target_id == o_t) & (ov.history_mode == o_m)].copy()
    ov["_m"] = pd.to_datetime(ov.target_month + "-01")
    ov = ov.sort_values("_m")
    truth = ov.drop_duplicates("target_month")[["_m", "target_month", "y_true"]]

    if not o_st:
        st.info("예측 시점을 하나 이상 선택하면 그려집니다. (실제값은 항상 표시됩니다)")
    elif len(truth):
        fig = go.Figure()
        fig.add_scatter(x=truth._m, y=truth.y_true.astype(float), mode="lines",
                        name="실제값 (나중에 확정)",
                        line=dict(color=ACTUAL_COLOR, width=2.6))
        dash = {"W0": "dash", "W1": "dashdot", "W2": "dot",
                "W3": "longdash", "W4": "solid"}
        width = {"W0": 1.8, "W1": 1.6, "W2": 1.6, "W3": 1.6, "W4": 2.4}
        for s in STAGES:
            if s not in o_st:
                continue
            sub = ov[ov.stage == s]
            if not len(sub):
                continue
            fig.add_scatter(x=sub._m, y=sub[o_mdl].astype(float), mode="lines",
                            name=f"{s} 예측 · {STAGE_HELP[s]}",
                            line=dict(color=MODEL_COLOR[o_mdl], width=width[s],
                                      dash=dash[s]),
                            opacity=1.0 if s == "W4" else 0.72)
        show(finish(
            fig, question="Q. 평가창 50개월 전체에서 예측은 실제값을 얼마나 따라갔나?",
            title=f"{TL[o_t]} · {MODEL_NAME[o_mdl]} — "
                  f"{len(truth)}개월 아웃오브샘플 예측 대 실제",
            ylab="지수 수준", xlab="대상월",
            footnote=FOOT_PIT, height=470))

        rows = []
        for s in STAGES:
            sub = ov[ov.stage == s]
            if not len(sub):
                continue
            e = (sub[o_mdl].astype(float) - sub.y_true.astype(float)).abs()
            rows.append({"예측 시점": f"{s} · {STAGE_HELP[s]}",
                         "개월": int(len(sub)),
                         "평균절대오차": round(float(e.mean()), 2),
                         "중앙값": round(float(e.median()), 2),
                         "최대": round(float(e.max()), 2)})
        safe_table(pd.DataFrame(rows), hide_index=True, width="stretch")
        reading_guide(
            how="검은 선이 **실제값**, 색선이 각 시점의 예측입니다. 겹칠수록 정확합니다.",
            now="**W4 가 W0 보다 실제값에 가깝게 붙습니다** — 같은 달 안에 도착한 "
                "공식 정보가 예측을 끌어당깁니다.",
            caution="**50개월 다년 과거 아웃오브샘플 평가창**입니다. 시간 순서와 "
                    "Point-in-Time 제약은 진짜지만, **같은 50개월을 V5~V11 에 걸쳐 "
                    "반복해 관측**했으므로 한 번도 보지 않은 외부 검증창은 아닙니다. "
                    "전향 검증이 그 자리를 채웁니다(데이터 & 방법 탭).")
        st.caption(
            "상품마다 지수의 단위·수준·변동성이 다르므로 **절대 오차를 상품 간에 "
            "비교하지 않습니다.** 비교는 같은 상품 안에서 시점·모델 사이에서만 합니다.")

    st.divider()
    st.markdown("#### 한 달을 자세히 — 정보가 들어올 때마다 예측이 어떻게 움직였나")

    c = st.columns([1.1, 1.1, 1.3])
    tgt = c[0].selectbox("상품", PRIMARY, format_func=lambda t: TL[t], key="rn_t")
    mode = c[1].selectbox("이력 조건", ["MATCHED", "MAXIMUM"], key="rn_m",
                          format_func=lambda m: MODE_LABEL[m])
    v = D["vintage"]
    vt = v[(v.target_id == tgt) & (v.history_mode == mode)]
    months = sorted(vt.target_month.unique())
    tm = c[2].selectbox("대상월", months, index=len(months) - 1, key="rn_month")

    cur = vt[vt.target_month == tm].set_index("stage")
    if len(cur):
        actual = float(cur.iloc[0]["y_true"])
        show_m0 = st.checkbox("과거 이력만 (M0) 함께 보기", value=False, key="rn_m0")
        avail = [s for s in STAGES if s in cur.index]
        fig = go.Figure()
        fig.add_scatter(x=avail, y=[actual] * len(avail), mode="lines",
                        name="실제값 (나중에 확정)",
                        line=dict(color=ACTUAL_COLOR, width=2.4, dash="dash"))
        for mdl in (("M0", "M1", "M2") if show_m0 else ("M1", "M2")):
            fig.add_scatter(x=avail, y=[float(cur.loc[s, mdl]) for s in avail],
                            mode="lines+markers", name=MODEL_NAME[mdl],
                            line=dict(color=MODEL_COLOR[mdl],
                                      width=2 if mdl == "M0" else 3,
                                      dash="dot" if mdl == "M0" else "solid"),
                            marker=dict(size=9))
        show(finish(fig, question="Q. 이 달의 예측은 정보가 들어올 때마다 어떻게 움직였나?",
                    title=f"{TL[tgt]} · {tm} — 예측 궤적",
                    ylab="지수 수준", xlab="예측 시점", footnote=FOOT_PIT, height=450))

        st.markdown("#### 이번 주에 어떤 정보가 새로 들어왔나")
        arr = D["arrivals"]
        aa = arr[(arr.target_id == tgt) & (arr.target_month == tm)]
        rows = []
        for i, s in enumerate(STAGES):
            if s not in cur.index:
                continue
            sub = aa[aa.stage == s]
            r = cur.loc[s]
            prev = (cur.loc[STAGES[i - 1]]
                    if i > 0 and STAGES[i - 1] in cur.index else None)
            rows.append({
                "시점": f"{s} · {STAGE_HELP[s]}",
                "기준일": r["forecast_as_of"],
                "새 예측대상 발표": int((sub.data_block == "TARGET_HISTORY").sum()),
                "새 시장 X 발표": int((sub.data_block == "MARKET_X").sum()),
                "새 Material Event": int((sub.data_block == "EVENT").sum()),
                "M1 예측": round(float(r["M1"]), 2),
                "직전 대비 수정": (round(float(r["M1"]) - float(prev["M1"]), 2)
                              if prev is not None else None),
                "오차": round(abs(actual - float(r["M1"])), 2)})
        safe_table(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption(
            "새 정보가 없는 주에는 예측이 **움직이지 않는 것이 정상**입니다. 이 표는 정보 "
            "도착과 예측 변화의 **대응**을 보여줄 뿐 인과관계 주장이 아닙니다.")

    st.divider()
    st.markdown("#### 정보 층별 증분 기여 — History / Market / Event")
    sub = skill_rows(tgt, mode)
    if len(sub):
        fig = go.Figure()
        fig.add_bar(x=sub.stage, y=sub.market_skill_pct.astype(float),
                    name="시장·산업 정보 (M0→M1)", marker_color=MODEL_COLOR["M1"],
                    text=[f"{x:+.1f}%" for x in sub.market_skill_pct.astype(float)],
                    textposition="outside")
        fig.add_bar(x=sub.stage, y=sub.event_skill_pct.astype(float),
                    name="Material Event (M1→M2)", marker_color=MODEL_COLOR["M2"],
                    text=[f"{x:+.1f}%" for x in sub.event_skill_pct.astype(float)],
                    textposition="outside")
        fig.add_hline(y=0, line=dict(color="#374151", width=1.2))
        show(finish(fig, question="Q. 각 정보층은 시점별로 얼마나 기여하는가?",
                    title=f"{TL[tgt]} — 시점별 증분 기여 "
                          "<span style='font-size:13px;color:#6B7280'>"
                          "(incremental forecast contribution · 인과효과 아님)</span>",
                    ylab="상대 개선률 (%)", xlab="예측 시점", height=420))
        st.caption(
            "**‘기여’는 중첩된 예측층 사이의 오차 차이**이며 인과효과가 아닙니다. "
            "M2 는 활성 Material Event 가 없으면 M1 과 **정확히 같습니다**(구조적 안전장치).")

# ===========================================================================
# 3. 리서치 분석
# ===========================================================================
with tabs[2]:
    st.subheader("리서치 분석")
    view = st.radio("무엇을 볼까요?",
                    ["상품 비교", "신호 & Event 분석", "예측 수렴", "큰 변동 조기경보"],
                    horizontal=True, key="ra_view")

    if view == "상품 비교":
        mode = st.selectbox("이력 조건", ["MATCHED", "MAXIMUM"], key="cc_mode",
                            format_func=lambda m: MODE_LABEL[m])
        rows = []
        for t in PRIMARY:
            r1 = traj_row(t, mode, "M1")
            s = skill_rows(t, mode)
            if r1 is None or not len(s):
                continue
            w4 = s[s.stage == "W4"].iloc[0]
            rows.append({"상품": TL[t],
                         "Rolling Skill (W0→W4)": float(r1["rolling_skill_W4_pct"]),
                         "Market Skill (W4)": float(w4["market_skill_pct"]),
                         "Event Skill (W4)": float(w4["event_skill_pct"])})
        df = pd.DataFrame(rows)
        fig = go.Figure()
        for col, color in (("Rolling Skill (W0→W4)", "#2563EB"),
                           ("Market Skill (W4)", MODEL_COLOR["M1"]),
                           ("Event Skill (W4)", MODEL_COLOR["M2"])):
            fig.add_bar(x=df["상품"], y=df[col], name=col, marker_color=color,
                        text=[f"{x:+.1f}%" for x in df[col]], textposition="outside")
        fig.add_hline(y=0, line=dict(color="#374151", width=1.2))
        show(finish(fig, question="Q. 어떤 정보가, 어떤 상품에서 예측을 개선하는가?",
                    title="상품별 상대 개선률  <span style='font-size:13px;color:#6B7280'>"
                          "상품 안에서의 비율로만 비교합니다</span>",
                    ylab="상대 개선률 (%)", xlab="", height=450))
        st.info(
            "**절대 오차로 상품 순위를 매기지 않습니다.** 세 지수는 단위·수준·변동성이 "
            "달라 절대값 비교가 의미 없습니다. 그래서 **상품 안에서의 상대 개선률**만 씁니다.")
        safe_table(df.style.format({c: "{:+.2f}" for c in df.columns if c != "상품"}),
                   hide_index=True, width="stretch")
        reading_guide(
            how="파란 막대가 **월중 정보 갱신**의 효과, 초록이 시장정보, 분홍이 사건 정보입니다.",
            now="**세 상품 모두 정보 갱신 효과가 압도적**이고 사건 정보는 0 근처이거나 음수입니다.",
            caution="Rolling 과 Market/Event 는 서로 다른 비교입니다. 같은 축에 있지만 "
                    "합산되는 값이 아닙니다.")

    elif view == "신호 & Event 분석":
        ev = M["event"]
        st.markdown("#### 더 많이 찾는 대신, 전달 가능성이 있는 것만 남긴다")
        c = st.columns(4)
        c[0].metric("공식 문서 (Broad)", f"{ev['broad_documents']:,}")
        c[1].metric("사안 (Episode)", f"{ev['broad_episodes']:,}")
        c[2].metric("Material Event · 스크랩", ev["material_events"]["SCRAP"])
        c[3].metric("압축비",
                    f"{ev['broad_documents'] // max(1, ev['material_events']['SCRAP']):,}:1")
        st.markdown("```\n공식 문서 → 사안(Episode) → Material Event → Rolling Impulse\n```")

        st.markdown("##### 판정 규칙 — 네 조건을 **모두** 만족해야 합니다")
        safe_table(pd.DataFrame([
            {"조건": "① 전달 경로", "규칙": ev["gate_conditions"]["1_transmission"],
             "뜻": "해당 상품 사슬에 직접 닿아야 한다"},
            {"조건": "② 새 정보", "규칙": ev["gate_conditions"]["2_novelty"],
             "뜻": "지속 상태는 새 신호를 만들지 않는다"},
            {"조건": "③ 확실성", "규칙": ev["gate_conditions"]["3_certainty"],
             "뜻": "조사 개시·잠정 판정은 제외"},
            {"조건": "④ 경제적 폭", "규칙": ev["gate_conditions"]["4_scope"],
             "뜻": "국가 단위 조치 또는 시장 구조를 바꾸는 품목 조치"}]),
            hide_index=True, width="stretch")

        with st.expander("후보 규칙 4종을 성능 이전에 비교했습니다"):
            safe_table(pd.DataFrame([
                {"후보": g["id"], "규칙": g["rule"],
                 "스크랩 건수": g.get("scrap_events"),
                 "판정": g["verdict"][:70]} for g in ev["candidate_gates"]]),
                hide_index=True, width="stretch")
            st.caption("목표 희소도를 정해 두고 맞춘 것이 아닙니다. 어떤 예측 성능도 "
                       "보지 않은 상태에서 **건수 구조만** 비교했습니다.")

        st.markdown("##### Event 는 실제로 도움이 됐나")
        mode = st.selectbox("이력 조건", ["MATCHED", "MAXIMUM"], key="ev_mode",
                            format_func=lambda m: MODE_LABEL[m])
        fig = go.Figure()
        for t in PRIMARY:
            s = skill_rows(t, mode)
            if not len(s):
                continue
            fig.add_scatter(x=s.stage, y=s.event_skill_pct.astype(float),
                            mode="lines+markers", name=TL[t],
                            line=dict(width=3), marker=dict(size=9))
        fig.add_hline(y=0, line=dict(color="#374151", width=1.2))
        fig.add_hline(y=3, line=dict(color="#DC2626", width=1.4, dash="dash"))
        fig.add_annotation(xref="paper", x=0.99, y=3, xanchor="right",
                           text="강한 결과 판정 임계 +3%", showarrow=False, yshift=12,
                           font=dict(size=11.5, color="#DC2626"))
        show(finish(fig, question="Q. 희소화한 Material Event 는 예측을 개선했는가?",
                    title="시점별 Event 증분 개선률  "
                          "<span style='font-size:13px;color:#6B7280'>양수 = 도움</span>",
                    ylab="Event 증분 개선률 (%)", xlab="예측 시점", height=430))
        st.error(
            "**희소화해도 증분 가치는 없었습니다.** 스크랩은 W2 에서 통계적으로 유의하게 "
            "**해로웠고**(−4.81%, p=0.012), 철광석은 사실상 0, 원유는 평가 구간에 "
            "Material Event 가 없어 정의상 0 입니다. 사전 동결한 중단 규칙 8조건 중 "
            "**1개만 통과**했습니다.")

        st.markdown("##### 실제로 남은 Material Event")
        pick = st.selectbox("상품", PRIMARY, format_func=lambda t: TL[t], key="me_t")
        mm = D["material"]
        mm = mm[mm.target_id == pick]
        if len(mm):
            safe_table(mm[["known_at", "family", "stage", "direction", "surprise",
                           "title"]].rename(columns={
                               "known_at": "공개일", "family": "발행", "stage": "단계",
                               "direction": "방향", "surprise": "신규성",
                               "title": "제목"}),
                       hide_index=True, width="stretch", height=320)
        else:
            st.warning(
                f"**{TL[pick]} 는 평가 구간에서 Material Event 가 없습니다.** 따라서 "
                "M2 는 M1 과 정확히 같습니다 — 모델링 선택이 아니라 자료의 구조입니다.")

        c = st.columns(3)
        c[0].metric("Event 활성 시점", f"{ev['event_active_rows']:,}")
        c[1].metric("M2 == M1 시점", f"{ev['m2_equals_m1_rows']:,}")
        c[2].metric("안전장치 위반", ev["safeguard_violations"],
                    help="활성 Event 가 없는데 M2 가 M1 과 달랐던 경우. 0이어야 합니다")

    elif view == "예측 수렴":
        mode = st.selectbox("이력 조건", ["MATCHED", "MAXIMUM"], key="conv_mode",
                            format_func=lambda m: MODE_LABEL[m])
        fig = go.Figure()
        for t in PRIMARY:
            r = traj_row(t, mode, "M1")
            if r is None:
                continue
            fig.add_scatter(x=STAGES, y=[float(r[f"mae_{s}"]) for s in STAGES],
                            mode="lines+markers", name=TL[t],
                            line=dict(width=3), marker=dict(size=9))
        show(finish(fig, question="Q. 예측은 얼마나 빨리 수렴하는가?",
                    title="시점별 절대 오차 (M1)  "
                          "<span style='font-size:13px;color:#6B7280'>"
                          "지수 단위가 달라 상품 간 절대 비교는 하지 않습니다</span>",
                    ylab="MAE (지수 Point)", xlab="예측 시점", height=430))
        rows = []
        for t in PRIMARY:
            r = traj_row(t, mode, "M1")
            if r is None:
                continue
            rows.append({"상품": TL[t],
                         "W0→W4 개선률 %": float(r["rolling_skill_W4_pct"]),
                         "단조 수렴률": float(r["monotonic_convergence_rate"]),
                         "개선된 달 비율": float(r["beneficial_revision_rate"]),
                         "악화된 달 비율": float(r["harmful_reversal_rate"]),
                         "최종 오차 분산": float(r["final_stage_dispersion"])})
        safe_table(pd.DataFrame(rows).style.format({
            "W0→W4 개선률 %": "{:+.2f}", "단조 수렴률": "{:.2f}",
            "개선된 달 비율": "{:.2f}", "악화된 달 비율": "{:.2f}",
            "최종 오차 분산": "{:.1f}"}), hide_index=True, width="stretch")

        st.markdown("#### 어느 시점에 무엇이 도착하는가")
        rr = D["release"]
        rr = rr[rr.history_mode == mode]
        fig = go.Figure()
        for blk, col, name in (
                ("months_with_new_target_release", "#2563EB", "새 예측대상 발표"),
                ("months_with_new_x_release", MODEL_COLOR["M1"], "새 시장 X 발표"),
                ("months_with_new_material_event", MODEL_COLOR["M2"],
                 "새 Material Event")):
            g = rr.groupby("stage")[blk].mean().reindex(STAGES)
            fig.add_bar(x=STAGES, y=g.values, name=name, marker_color=col,
                        text=[f"{x:.0f}" for x in g.values], textposition="outside")
        show(finish(fig, question="Q. 개선은 어느 시점의 어떤 발표와 겹치는가?",
                    title="시점별 새 정보 도착  <span style='font-size:13px;color:#6B7280'>"
                          "50개 대상월 중 몇 달에 새 정보가 있었나 (상품 평균)</span>",
                    ylab="대상월 수", xlab="예측 시점", height=420))
        st.success(
            "**W0·W1 에는 새 정보가 0개월**이고 오차 변화도 정확히 0 입니다. "
            "**W2 에서 50개월 중 36개월에 전월 공식 지수가 도착**하면서 오차가 급감합니다. "
            "개선은 모델이 아니라 **발표 일정**에서 옵니다.")

    else:
        mode = st.selectbox("이력 조건", ["MATCHED", "MAXIMUM"], key="lm_mode",
                            format_func=lambda m: MODE_LABEL[m])
        rows = []
        for t in PRIMARY:
            for mdl in ("M0", "M1", "M2"):
                r = traj_row(t, mode, mdl)
                if r is None:
                    continue
                rows.append({
                    "상품": TL[t], "모델": MODEL_NAME[mdl],
                    "큰 변동 월 수": int(r["n_large_moves"]),
                    "방향이 처음 맞는 시점 (전체)":
                        (float(r["first_correct_direction_stage_mean"])
                         if pd.notna(r["first_correct_direction_stage_mean"]) else None),
                    "방향이 처음 맞는 시점 (큰 변동)":
                        (float(r["large_move_first_correct_stage_mean"])
                         if pd.notna(r["large_move_first_correct_stage_mean"]) else None),
                    "끝까지 못 맞힌 달": int(r["months_never_correct_direction"])})
        safe_table(pd.DataFrame(rows).style.format({
            "방향이 처음 맞는 시점 (전체)": "{:.2f}",
            "방향이 처음 맞는 시점 (큰 변동)": "{:.2f}"}, na_rep="—"),
            hide_index=True, width="stretch")
        st.caption(
            "숫자는 **시점 번호**입니다(0=W0 … 4=W4). 작을수록 일찍 방향을 맞혔다는 뜻입니다. "
            "큰 변동 정의는 이전 단계에서 동결한 규칙(|변화| 80분위)을 그대로 씁니다.")
        st.warning(
            "큰 변동이 상품당 **10개월**뿐입니다. 표본이 작아 점 추정치이며 여기서 강한 "
            "주장을 하지 않습니다.")

# ===========================================================================
# 4. 데이터 & 방법
# ===========================================================================
with tabs[3]:
    st.subheader("데이터 & 방법 — 연구 무결성")
    c = st.columns(4)
    c[0].metric("유료 데이터", f"{M['rights']['paid_sources_used']}건")
    c[1].metric("V11 이 새로 도입한 기관", f"{M['rights']['new_organizations']}곳")
    c[2].metric("PASS 소스", M["rights"]["pass"])
    c[3].metric("REVIEW·REJECT (사용 금지)",
                M["rights"]["review"] + M["rights"]["reject"])

    # -- 전향 검증 현황 ------------------------------------------------------
    PV = M.get("prospective", {})
    st.markdown("#### 전향 검증 — 결과가 나오기 전에 잠근 예측")
    locked = int(PV.get("months_locked", 0))
    evaluated = int(PV.get("months_evaluated", 0))
    p = st.columns(4)
    p[0].metric("잠긴 달", f"{locked}건")
    p[1].metric("채점된 달", f"{evaluated}건")
    p[2].metric("첫 예정 잠금", PV.get("first_planned_lock", "2026-09-02"))
    p[3].metric("결과 등급", PV.get("result_tier", "D"),
                help="과거 창(Tier A) 통계에 섞지 않습니다")
    if locked == 0:
        st.info(
            "**아직 잠긴 달이 없습니다.** 이건 결측이 아니라 상태입니다 — 전향 관측은 "
            "만들어 낼 수 없고 시간이 지나야 쌓입니다. 소급해서 만든 잠금은 증거가 "
            "아니므로 만들지 않습니다.")
    else:
        st.success(f"전향 관측 {locked}건이 잠겨 있고 그중 {evaluated}건이 채점됐습니다.")
    st.markdown(
        f"- **무엇인가** — {PV.get('label', 'pre-outcome locked prospective monthly evaluation with PIT-reconstructed weekly vintages')}\n"
        "- **어떻게 동작하나** — 대상월이 끝났고 공식 결과가 아직 나오지 않은 시점에 "
        "W0~W4 를 동결 로직으로 재구성하고, SHA256 해시와 커밋으로 잠급니다.\n"
        "- **왜 필요한가** — 위의 50개월 평가창은 다년 창이지만 V5~V11 에 걸쳐 반복해 "
        "관측됐습니다. 한 번도 보지 않은 관측은 앞으로 쌓는 수밖에 없습니다.\n"
        "- **아닌 것** — 매주 실시간으로 도는 운영 시스템이 아닙니다. 도구는 한 달에 "
        "한 번 돌고, 주간 vintage 는 그 시점 정보로 **재구성**한 것입니다.")
    st.caption(
        "결과 방화벽: 예측 경로에는 결과값이 들어갈 자리가 없습니다(대상월 라벨이 NaN). "
        "채점은 별도 경로가 하고, 잠긴 파일은 해시 검증 후 읽기만 합니다.")

    st.divider()
    st.markdown("#### 예측 대상과 Target-Specific X")
    safe_table(D["targets"][["label", "series_id", "official_name", "status", "role",
                             "x_core", "matched_train_start", "matched_n_train_first",
                             "maximum_train_start", "maximum_n_train_first"]]
               .rename(columns={
                   "label": "대상", "series_id": "계열 ID", "official_name": "공식 계열명",
                   "status": "지위", "role": "역할", "x_core": "Target-Specific X",
                   "matched_train_start": "공통 학습시작",
                   "matched_n_train_first": "공통 학습행",
                   "maximum_train_start": "최대 학습시작",
                   "maximum_n_train_first": "최대 학습행"}),
               hide_index=True, width="stretch")

    if M["targets"]["excluded"]:
        st.info(
            f"**구리 스크랩은 1차 비교에서 뺐습니다 — 사유는 성능이 아니라 데이터 설계입니다.** "
            f"이 상품의 자료 공백이 공통 학습 시작을 {M['history']['v10_common_start']} 로 "
            f"끌어내렸고, 빼면 **{M['history']['gain_months']}개월** 앞당겨집니다"
            f"({M['history']['matched_train_start']}). V10 에서 구리의 시장정보 기여는 "
            "네 상품 중 **가장 컸습니다** — 쓸모없는 대상이 아니라 **공통 이력을 깎는 "
            "대상**이었습니다.")
    with st.expander("원시 구리로 대체할 수 있었나 — 실제로 찾아본 결과"):
        for sid, verdict in M["targets"]["raw_copper_verdicts"].items():
            st.markdown(f"- `{sid}` — {verdict}")
        st.markdown(
            "- LME·COMEX 등 상용 데이터는 **권리 규칙상 처음부터 제외**했습니다. "
            "상용 데이터로 넘어가면 다른 대상과 발표 일정·known_at 규칙이 달라져 "
            "공정 비교의 근거가 무너집니다.")
        st.markdown("→ **PASS 하는 원시 구리가 없어 대체를 강행하지 않았습니다.**")

    st.divider()
    st.markdown("#### true Point-in-Time — 이 연구의 핵심 규약")
    a, b = st.columns(2)
    a.markdown(
        "**데이터 규칙**  \n"
        "- 각 시점에서 `발표일 ≤ 그 시점` 인 값만 사용\n"
        "- 발표일은 **원문 안의 릴리스 캘린더**에서 읽음\n"
        "- 발표일을 확인하지 못한 회차는 **추정하지 않고 폐기**\n"
        "- 현재 개정값으로 과거를 채우지 않음")
    b.markdown(
        "**Rolling 규약**  \n"
        f"- 다섯 시점: {' · '.join(f'{s}({STAGE_HELP[s]})' for s in STAGES)}\n"
        "- 대상월은 고정, **정보 절단만 이동**\n"
        f"- W0 기준선 고정: **{'예' if M['rolling']['baseline_frozen_at_w0'] else '아니오'}**\n"
        f"- 주간 시장 계열 채택: "
        f"**{'예' if M['rolling']['weekly_market_block_admitted'] else '아니오'}**\n"
        f"- 통계 단위: **{M['rolling']['statistical_unit']}**")
    st.caption(
        "주간 시장 계열(EIA 주간 등)은 **현재 개정값만 공개**되어 과거 시점 재구성이 "
        "불가능하므로 채택하지 않았습니다. 정보 갱신은 실제 공식 발표와 관보 게재로만 "
        "일어납니다.")

    st.markdown("#### 데이터 권리")
    safe_table(D["rights"].rename(columns={
        "source": "소스", "organization": "기관", "status": "판정", "used": "사용",
        "url": "공식 URL", "note": "비고"}), hide_index=True, width="stretch")
    st.caption("REVIEW 는 모델링 목적에서 REJECT 와 **동일하게** 취급합니다.")

    st.divider()
    st.markdown("#### 연구 수행 체계 (Agent Team)")
    team = D.get("legacy", {}).get("agent_team")
    if team:
        st.markdown(
            "한 모델에게 전부 시킨 것이 아니라 역할별 전문 Agent 로 분해해 수행했습니다. "
            "특히 **독립 QA 역할**이 leakage·PIT·동결 위반을 별도로 검증합니다.")
        for grp in team.get("groups", []):
            st.markdown(f"**{grp['title']}**")
            cols = st.columns(len(grp["agents"]))
            for col, ag in zip(cols, grp["agents"]):
                col.markdown(
                    f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
                    f"border-radius:8px;padding:12px;height:100%'>"
                    f"<b style='font-size:14px'>{ag['role_ko']}</b><br>"
                    f"<code style='font-size:11px'>{ag['name']}</code><br>"
                    f"<span style='font-size:12.5px'>{ag['responsibility']}</span>"
                    "</div>", unsafe_allow_html=True)
            st.write("")
        if team.get("skills"):
            with st.expander("원칙을 강제한 공유 규칙(Skill)"):
                safe_table(pd.DataFrame(team["skills"]), hide_index=True,
                           width="stretch")
    else:
        st.caption("Agent Team 메타데이터를 찾지 못했습니다.")

# ===========================================================================
# 5. 연구 여정
# ===========================================================================
with tabs[4]:
    st.subheader("연구 여정 — V1 → V11")
    st.info(
        "**모든 실험이 보존되어 있습니다. 실패한 것까지 그대로입니다.** 각 세대의 "
        "부정적 결과가 다음 세대를 만든 근거였습니다. 화면 구조는 V11 에서 바꿨지만 "
        "**결과·방법·산출물·커밋은 바뀌지 않았습니다.**")

    for gen in M["journey"]:
        st.markdown(f"### {gen['title']}")
        st.caption(f"{gen['period']} · {gen['theme']}")
        for v in gen["versions"]:
            with st.expander(f"{v['version']} — {v['question'][:70]}"):
                st.markdown(f"**질문**  \n{v['question']}")
                st.markdown(f"**무엇을 바꿨나**  \n{v['change']}")
                st.markdown(f"**결과**  \n{v['result']}")
                if v.get("why_next"):
                    st.markdown(f"**그래서 다음 단계**  \n{v['why_next']}")
                if v.get("freeze_commit"):
                    st.caption(f"동결 커밋 `{v['freeze_commit']}`")
        st.divider()

    st.markdown("#### 무결성 원칙")
    for n in M["journey_integrity_notes"]:
        st.markdown(f"- {n}")

st.divider()
st.caption(FOOT_SOURCE)
st.caption(FOOT_PIT)
