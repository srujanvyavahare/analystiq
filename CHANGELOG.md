# Changelog

## [Unreleased]

### Phase 9 - Documentation
- Authored a comprehensive `README.md` containing a functional architecture map (Orchestrator, Execution Engine, Verifier, Generator).
- Included a feature-by-feature honest comparison table measuring AnalystIQ against commercial competitors (Julius AI, ChatGPT ADA).
- Documented testing instructions via the local `run_checks.ps1` CI script.

### Phase 8 - Charts, Tables, States
- Defined a global `plotly.io.templates["analystiq"]` template inside `ui/tokens.py` matching the brand colors and typography, and forced it as the default so all LLM-generated Plotly charts inherit the theme without needing explicit styling code.
- Enforced tabular data alignment and strict `Fira Code` monospacing in CSS.
- Added a `ui/components/states.py` module to handle distinct empty UI states (e.g., when no data is loaded, or when navigating to the Explore/Report tabs before they are populated).
- Handled edge cases and loading spinners to ensure a polished application experience.

### Phase 7 - Metric Registry
- Built `core/registry.py` to persist custom business logic and metrics definitions locally.
- Added a "Metric Registry" manager to the Left Rail sidebar UI where users can define terms (e.g., "Active User = Login < 30 days").
- Modified `utils/llm.py` to automatically inject all defined metrics straight into the system prompt context, ensuring the LLM inherently understands the user's specific business language without having to be re-taught on every prompt.

### Phase 6 - Analysis Recipes
- Developed `core/recipe.py` to extract, save, and re-apply chat sessions as pure JSON workflow definitions.
- Implemented strict Schema Drift detection that halts execution if a recipe relies on columns missing in the new dataset.
- Added a full UI in the `Recipe` tab to name, save, select, and execute recipes against the currently loaded dataset.
- Applied recipes inject their deterministic (Zero-LLM) results directly back into the chat interface for a seamless experience.

### Phase 5 - Statistical Guardrails
- Implemented deterministic heuristics in `core/guardrails.py` to evaluate the final `result_df`.
- The pipeline now strictly detects high skew/outlier distortion (mean vs median > 20% diff), high missing data concentrations (> 20%), small sample sizes (< 30), and potential Simpson's Paradox / correlation reversals.
- Integrated these checks directly into the Trust Layer, downgrading the Confidence chip dynamically and prominently alerting the user inline when statistical anomalies are present in the final calculation.

### Phase 4 - Auto-insight Brief and First-run Experience
- Implemented a zero-state landing page in the center workspace with three bundled sample datasets (`sales.csv`, `customers.csv`, `weather.csv`).
- Created `core/auto_insights.py` to deterministically calculate skewness, correlations, imbalances, and missing data concentrations on file upload.
- Integrated a cached, single-LLM-call Auto-Insight brief that runs immediately on data load to show 5-7 punchy bullet points before the user asks any questions.
- Added context-aware suggested question chips below the brief.

### Phase 3 - Reproducible Export
- Added `core/exporter.py` with logic to seamlessly convert session history into standalone Python scripts (`.py`), Jupyter Notebooks (`.ipynb`), and HTML reports.
- Added Export buttons to the top of the Chat interface, allowing immediate download of scripts, notebooks, reports, and cleaned CSVs.
- Created `run_checks.ps1` wrapping pytest to act as a local CI, verifying that the generated `analysis.py` successfully runs in isolation without an API key.

### Phase 2 - Trust Layer
- Modified `utils/llm.py` prompt schema to mandate an `assumptions` JSON block dictating column mapping and filters before code generation.
- Created `ui/components/trust_card.py` to render editable assumptions and execution facts.
- Implemented deterministic Execution Facts (rows dropped, nulls) inside `core/pipeline.py`.
- Added dynamic Confidence Chip (Red/Amber/Green) calculated strictly via rules in `core/pipeline.py` (e.g. Red for <30 rows, Amber for inferred mappings).
- Added `tests/test_trust.py` covering confidence rules.

### Phase 1 - Design System and Layout
- Created `ui/tokens.py` to act as a single source of truth for the app's design system (colors, typography).
- Replaced scattered inline CSS and default Streamlit styling with a cohesive Fira Sans / Fira Code theme.
- Restructured `app.py` into a dashboard workspace: Collapsible left sidebar for controls and schema, center chat with bordered cards (`st.container(border=True)`), right rail for data preview, and top-level tabs (Chat, Explore, Recipe, Report).
- Implemented `st.fragment` for a deterministic top-level KPI strip that renders without blocking the rest of the app.

### Phase 0 - Discovery & Refactoring
- Extracted LLM orchestration and code execution loop from `app.py` into a new, isolated module `core/pipeline.py`.
- `app.py` now cleanly delegates to `run_analysis_pipeline()`, fulfilling the Phase 0 prerequisite of separating UI from business logic.
