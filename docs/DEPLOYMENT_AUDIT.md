# DEPLOYMENT AUDIT

- 감사 시각(UTC): 2026-08-27T00:14:19+00:00
- 검사 파일 수: 52
- 문제: **0건**

> 배포된 앱이 공개로 보일 수 있다고 가정하고 **PUBLIC-SAFE 기준**으로 감사한다.

## 검사 항목

- 금지 파일명 패턴 (FRED/ALFRED/raw/secrets/원문 PDF·XLSX·ZIP)
- 비밀정보 패턴 (토큰·API key·비밀번호·이메일)
- 로컬 절대경로 / 사용자명
- 5MB 초과 대용량 파일

## 결과

- ✅ 문제 없음. 위 모든 검사를 통과했다.

이 저장소는 **연구 저장소의 사본이 아니라** 사전 계산된 안전 산출물만
담은 별도 저장소다. 원본 BLS/Fed artifact, FRED/ALFRED 데이터,
기사 본문, 자격증명, 회사 내부 정보는 포함되지 않는다.

## 포함된 파일

- `.gitignore`
- `.streamlit/config.toml`
- `assets/agent_team.png`
- `assets/event_pressure_timeline.png`
- `assets/event_trust.png`
- `assets/executive_performance.png`
- `assets/forecast_actual_vs_pred.png`
- `assets/model_story.png`
- `assets/two_by_two.png`
- `data/demo_v3_metrics.csv`
- `data/demo_v4_comparisons.csv`
- `data/demo_v4_event_attribution.csv`
- `data/demo_v4_metrics.csv`
- `data/demo_v4_predictions.csv`
- `data/demo_v4_selected_models.csv`
- `data/demo_v5_comparisons.csv`
- `data/demo_v5_event_attribution.csv`
- `data/demo_v5_metrics.csv`
- `data/demo_v5_predictions.csv`
- `data/demo_v5_selected_models.csv`
- `data/demo_v6_comparisons.csv`
- `data/demo_v6_metrics.csv`
- `data/demo_v6_regime.csv`
- `data/demo_v6_selected_models.csv`
- `data/demo_v6_support.csv`
- `data/demo_v7_comparisons.csv`
- `data/demo_v7_conditional_by_origin.csv`
- `data/demo_v7_metrics.csv`
- `data/demo_v7_risk_by_origin.csv`
- `data/event_channel_panel_v5.csv`
- `data/event_contribution_v3.csv`
- `data/event_episode_registry_v3.csv`
- `data/event_monthly_category_state_v3.csv`
- `data/event_transition_registry_v3.csv`
- `data/metrics.csv`
- `data/pep_nep_v3.csv`
- `data/predictions.csv`
- `data/run_metadata.json`
- `data/x_feature_registry.csv`
- `docs/event_method.md`
- `docs/event_method_v3.md`
- `docs/executive_summary.md`
- `docs/findings_v3.md`
- `docs/findings_v4.md`
- `docs/findings_v5.md`
- `docs/findings_v6.md`
- `docs/findings_v7.md`
- `docs/methodology_summary.md`
- `docs/next_phase_plan.md`
- `README.md`
- `requirements.txt`
- `streamlit_app.py`
