import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from ui.tokens import Tokens
from core.pipeline import run_analysis_pipeline
from utils.llm import configure_llm

# Configure page
st.set_page_config(page_title="AnalystIQ", layout="wide", page_icon="📊")

# Load env variables and configure LLM
load_dotenv()
configure_llm()

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'df' not in st.session_state:
    st.session_state.df = None
if 'df_info' not in st.session_state:
    st.session_state.df_info = ""
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = ""
if 'result_df' not in st.session_state:
    st.session_state.result_df = None

# --- Login Page ---
def show_login():
    Tokens.inject_css()
    st.markdown("<h1 style='text-align: center; margin-top: 10vh;'>Welcome to AnalystIQ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please log in to access your dashboard.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username == "admin" and password == "admin":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please use admin/admin.")

@st.fragment
def render_kpi_strip():
    if st.session_state.df is not None:
        df = st.session_state.df
        rows = df.shape[0]
        cols = df.shape[1]
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        null_pct = df.isnull().sum().sum() / (rows * cols) * 100 if rows > 0 else 0
        
        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Rows", f"{rows:,}")
        kpi_cols[1].metric("Columns", f"{cols:,}")
        kpi_cols[2].metric("Memory", f"{memory_mb:.2f} MB")
        kpi_cols[3].metric("Missing Data", f"{null_pct:.1f}%")
        st.divider()

# --- Dashboard ---
def show_dashboard():
    Tokens.inject_css()
    
    # Left Rail
    with st.sidebar:
        st.markdown("<h2>📊 AnalystIQ</h2>", unsafe_allow_html=True)
        
        def load_dataset(file_obj, name, is_csv=True):
            try:
                df = pd.read_csv(file_obj) if is_csv else pd.read_excel(file_obj)
                st.session_state.df = df
                st.session_state.uploaded_file_name = name
                
                buffer = [
                    f"Total Rows: {df.shape[0]}, Total Columns: {df.shape[1]}",
                    f"Columns: {', '.join(df.columns)}",
                    f"Data types:\n{df.dtypes}",
                    f"Sample data (first 3 rows):\n{df.head(3).to_string()}"
                ]
                st.session_state.df_info = "\n".join(buffer)
                
                # Phase 4: Cache Auto-Insights on load
                from core.auto_insights import compute_deterministic_stats, get_auto_insights_brief
                stats = compute_deterministic_stats(df)
                st.session_state.auto_insights = get_auto_insights_brief(stats)
                st.session_state.data_stats = stats
                
                st.session_state.messages = []
                st.session_state.generated_code = ""
                st.session_state.result_df = None
                st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {e}")

        uploaded_file = st.file_uploader("Upload CSV / Excel", type=['csv', 'xlsx', 'xls'])
        if uploaded_file is not None and (st.session_state.df is None or uploaded_file.name != st.session_state.get('uploaded_file_name')):
            load_dataset(uploaded_file, uploaded_file.name, uploaded_file.name.endswith('.csv'))
                    
        if st.session_state.df is not None:
            with st.expander("📋 Schema", expanded=True):
                for col, dtype in st.session_state.df.dtypes.items():
                    st.caption(f"**{col}** `{dtype}`")
                    
        with st.expander("📏 Metric Registry"):
            from core.registry import load_metrics, save_metric, delete_metric
            metrics = load_metrics()
            
            if metrics:
                for m_name, m_def in metrics.items():
                    st.caption(f"**{m_name}**: {m_def}")
            else:
                st.write("No custom metrics defined.")
                
            with st.form("new_metric_form"):
                new_m_name = st.text_input("Metric Name (e.g. 'Active User')")
                new_m_def = st.text_input("Definition (e.g. 'Login < 30 days')")
                if st.form_submit_button("Save Metric"):
                    if new_m_name and new_m_def:
                        save_metric(new_m_name, new_m_def)
                        st.success("Saved!")
                        st.rerun()
                    
        st.markdown("---")
        if st.button("➕ New Analysis", use_container_width=True):
            st.session_state.messages = []
            st.session_state.generated_code = ""
            st.session_state.result_df = None
            st.rerun()
            
        with st.expander("💡 Example Questions"):
            st.markdown("- *What is the total number of rows?*\n- *Show me sales by region as a bar chart.*")
            
        with st.expander("🔖 Saved Insights"):
            if 'saved_insights' not in st.session_state:
                st.session_state.saved_insights = []
            if st.session_state.saved_insights:
                for idx, insight in enumerate(st.session_state.saved_insights):
                    st.success(f"**Insight {idx+1}:** {insight}")
            else:
                st.write("No insights saved yet.")
                
        with st.expander("⚙️ Settings"):
            st.session_state.temperature = st.slider("AI Creativity (Temperature)", 0.0, 1.0, st.session_state.get('temperature', 0.2))
            st.write("Current Model: **gemini-3.6-flash**")
            
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Center Workspace
    render_kpi_strip()
    
    tab_chat, tab_explore, tab_recipe, tab_report = st.tabs(["💬 Chat", "🔍 Explore", "🧾 Recipe", "📑 Report"])
    
    with tab_chat:
        # Phase 3: Export Header
        if st.session_state.messages and st.session_state.df is not None:
            with st.container():
                st.markdown("### 📥 Export Session")
                from core.exporter import generate_python_script, generate_notebook, generate_html_report
                
                fname = st.session_state.get('uploaded_file_name', 'data.csv')
                csv_data = st.session_state.result_df.to_csv(index=False) if st.session_state.result_df is not None else st.session_state.df.to_csv(index=False)
                
                dl_cols = st.columns(4)
                dl_cols[0].download_button("Python Script (.py)", generate_python_script(st.session_state.messages, fname), file_name="analysis.py", use_container_width=True)
                dl_cols[1].download_button("Jupyter Notebook (.ipynb)", generate_notebook(st.session_state.messages, fname), file_name="analysis.ipynb", use_container_width=True)
                dl_cols[2].download_button("HTML Report", generate_html_report(st.session_state.messages, fname), file_name="report.html", use_container_width=True)
                dl_cols[3].download_button("Cleaned Data (.csv)", csv_data, file_name="cleaned_data.csv", use_container_width=True)
                st.divider()

        col_main, col_right = st.columns([7, 3], gap="large")
        
        with col_main:
            chat_container = st.container(height=600, border=False)
            with chat_container:
                if st.session_state.df is None:
                    # Phase 4: Landing Page
                    st.markdown("## 🚀 Welcome to AnalystIQ")
                    st.markdown("Instantly analyze your data using natural language. Upload a file on the left, or try one of our sample datasets below to get started.")
                    st.markdown("---")
                    st.markdown("#### Try a Sample Dataset")
                    samp_cols = st.columns(3)
                    if samp_cols[0].button("📦 Sales Data", use_container_width=True):
                        load_dataset("samples/sales.csv", "sales.csv", True)
                    if samp_cols[1].button("👥 Customer Data", use_container_width=True):
                        load_dataset("samples/customers.csv", "customers.csv", True)
                    if samp_cols[2].button("🌤️ Weather Data", use_container_width=True):
                        load_dataset("samples/weather.csv", "weather.csv", True)
                        
                elif not st.session_state.messages:
                    # Phase 4: Auto-Insight Brief & First-run sequence
                    st.markdown(f"### 📊 Analysis Brief: `{st.session_state.uploaded_file_name}`")
                    
                    # Auto-Insights Brief
                    with st.container(border=True):
                        st.markdown("#### 💡 Quick Insights")
                        insights = st.session_state.get("auto_insights", [])
                        for insight in insights:
                            st.write(f"• {insight}")
                            
                    # Suggested Questions
                    st.markdown("#### 🎯 Suggested Questions")
                    sg_cols = st.columns(3)
                    cols = st.session_state.df.columns.tolist()
                    q1 = f"What is the total number of rows?"
                    q2 = f"Show me a summary of {cols[0]}." if cols else "What are the data types?"
                    q3 = f"Are there any missing values?"
                    
                    if sg_cols[0].button(q1, use_container_width=True):
                        st.session_state.messages.append({"role": "user", "content": q1})
                        st.rerun()
                    if sg_cols[1].button(q2, use_container_width=True):
                        st.session_state.messages.append({"role": "user", "content": q2})
                        st.rerun()
                    if sg_cols[2].button(q3, use_container_width=True):
                        st.session_state.messages.append({"role": "user", "content": q3})
                        st.rerun()
                    
                for idx, msg in enumerate(st.session_state.messages):
                    if msg["role"] == "user":
                        with st.chat_message("user"):
                            st.write(msg["content"])
                    else:
                        with st.chat_message("assistant"):
                            with st.container(border=True):
                                if "insights" in msg and msg["insights"]:
                                    for item in msg["insights"]:
                                        st.write(f"- {item}")
                                
                                if "fig" in msg and msg["fig"]:
                                    if isinstance(msg["fig"], plt.Figure):
                                        st.pyplot(msg["fig"])
                                    else:
                                        st.plotly_chart(msg["fig"], use_container_width=True)
                                
                                if "error" in msg:
                                    st.error(msg["error"])
                                    
                                # Trust Layer (Phase 2)
                                from ui.components.trust_card import render_trust_layer
                                
                                assumptions = msg.get("assumptions", {})
                                exec_facts = msg.get("execution_facts", {})
                                confidence = msg.get("confidence", "Green")
                                confidence_reason = msg.get("confidence_reason", [])
                                
                                if msg.get("code") or assumptions:
                                    render_trust_layer(idx, assumptions, exec_facts, confidence, confidence_reason)
                                
                                with st.expander("Prompt & Code Inspector"):
                                    if msg.get("code"):
                                        st.code(msg["code"], language="python")
                                    else:
                                        st.write("No code was generated.")
                                    # We don't have full prompt history in msg yet, but we could add it
                                    # if we returned it from the pipeline.

            # Handle pending overrides
            if getattr(st.session_state, "pending_override", None):
                override_data = st.session_state.pending_override
                idx_to_revert = override_data["idx"]
                override_text = override_data["text"]
                # Clear it
                st.session_state.pending_override = None
                
                # Truncate messages history back to the prompt that caused this
                # The user prompt is at idx_to_revert - 1
                if idx_to_revert > 0:
                    st.session_state.messages = st.session_state.messages[:idx_to_revert]
                    st.session_state.user_overrides = override_text
                    st.rerun()

            prompt = st.chat_input("Ask a question about your data...")
            if prompt:
                if st.session_state.df is None:
                    st.error("Please upload a dataset first.")
                elif not os.environ.get("GEMINI_API_KEY"):
                    st.error("GEMINI_API_KEY is not set in the environment.")
                else:
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.rerun()

        with col_right:
            st.markdown("### Data Preview")
            if st.session_state.result_df is not None:
                if isinstance(st.session_state.result_df, pd.DataFrame):
                    st.dataframe(st.session_state.result_df, use_container_width=True)
                elif isinstance(st.session_state.result_df, pd.Series):
                    st.dataframe(st.session_state.result_df.to_frame(), use_container_width=True)
            elif st.session_state.df is not None:
                st.dataframe(st.session_state.df.head(), use_container_width=True)
            else:
                st.info("Upload data to see a preview.")

    with tab_explore:
        st.info("Explore view placeholder (Data quality, auto-insights).")
        
    with tab_recipe:
        st.markdown("### 🧾 Analysis Recipes")
        st.write("Save your current chat session as a repeatable workflow, then apply it to new datasets instantly with zero LLM calls.")
        
        from core.recipe import save_recipe, list_recipes, apply_recipe
        
        col_save, col_load = st.columns(2)
        with col_save:
            with st.container(border=True):
                st.markdown("#### Save Current Session")
                recipe_name = st.text_input("Recipe Name", key="save_recipe_name")
                if st.button("Save as Recipe", use_container_width=True):
                    if st.session_state.messages:
                        path = save_recipe(recipe_name, st.session_state.messages)
                        st.success(f"Saved to {path}")
                    else:
                        st.warning("No chat history to save.")
                        
        with col_load:
            with st.container(border=True):
                st.markdown("#### Apply a Recipe")
                recipes = list_recipes()
                if recipes:
                    recipe_options = {r["name"]: r for r in recipes}
                    selected_recipe = st.selectbox("Select Recipe", list(recipe_options.keys()))
                    
                    if st.button("Run on Current Dataset", use_container_width=True):
                        if st.session_state.df is not None:
                            recipe_obj = recipe_options[selected_recipe]
                            st.write(f"Running '{selected_recipe}'...")
                            res = apply_recipe(recipe_obj, st.session_state.df)
                            
                            if res["success"]:
                                st.success("Recipe applied successfully!")
                                # Inject into chat
                                for r in res["results"]:
                                    st.session_state.messages.append({"role": "user", "content": f"[Recipe] {r['prompt']}"})
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "insights": ["Generated automatically via Recipe."], 
                                        "code": r['code'], 
                                        "fig": r['fig'], 
                                        "confidence": "Green",
                                        "confidence_reason": ["Zero-LLM deterministic execution."]
                                    })
                                    if r['result_df'] is not None:
                                        st.session_state.result_df = r['result_df']
                                st.rerun()
                            else:
                                st.error(res["error"])
                        else:
                            st.warning("Please upload a dataset first.")
                else:
                    st.info("No saved recipes yet.")
        
    with tab_report:
        st.info("Report builder placeholder.")

    # Processing User Prompt
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with tab_chat:
            with col_main:
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing..."):
                            prompt_text = st.session_state.messages[-1]["content"]
                            model_name = "gemini-3.6-flash"
                            temp = st.session_state.get('temperature', 0.2)
                            user_overrides = st.session_state.get("user_overrides", None)
                            
                            analysis_result = run_analysis_pipeline(
                                prompt_text=prompt_text,
                                df=st.session_state.df,
                                df_info=st.session_state.df_info,
                                model_name=model_name,
                                temperature=temp,
                                user_overrides=user_overrides
                            )
                            
                            # Clear overrides after use
                            st.session_state.user_overrides = None
                            
                            if not analysis_result["success"]:
                                st.session_state.messages.append({"role": "assistant", "error": analysis_result["error"], "code": analysis_result.get("code", "")})
                            else:
                                st.session_state.result_df = analysis_result["result_df"] if analysis_result["result_df"] is not None else st.session_state.df.head()
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "fig": analysis_result["fig"],
                                    "insights": analysis_result["insights"],
                                    "code": analysis_result["code"]
                                })
                            st.rerun()

# --- Main Routing ---
if __name__ == "__main__":
    if st.session_state.logged_in:
        show_dashboard()
    else:
        show_login()
