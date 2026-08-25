# DEPLOYMENT AUDIT

- 감사 시각(UTC): 2026-08-25T09:36:47+00:00
- 검사 파일 수: 17
- 문제: **0건**

## 검사 항목

- 금지 파일명 패턴 (FRED/ALFRED/raw/secrets/원문 PDF·XLSX·ZIP)
- 비밀정보 패턴 (토큰·API key·비밀번호·이메일)
- 로컬 절대경로 / 사용자명
- 5MB 초과 대용량 파일

## 결과

- ✅ 문제 없음. 위 모든 검사를 통과했다.

이 저장소는 **연구 저장소의 사본이 아니라** 사전 계산된 안전 산출물만
담은 별도 저장소다. 원본 BLS/Fed artifact, FRED/ALFRED 데이터,
기사 본문, 자격증명은 포함되지 않는다.

## 포함된 파일

- `.gitignore`
- `.streamlit/config.toml`
- `assets/claude_code_workflow.png`
- `assets/event_pressure_timeline.png`
- `assets/forecast_actual_vs_pred.png`
- `assets/forecast_comparison.png`
- `assets/model_stages.png`
- `data/event_pressure.csv`
- `data/event_registry.csv`
- `data/metrics.csv`
- `data/predictions.csv`
- `data/run_metadata.json`
- `docs/executive_summary.md`
- `docs/methodology_summary.md`
- `README.md`
- `requirements.txt`
- `streamlit_app.py`
