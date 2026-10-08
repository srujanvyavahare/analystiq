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
        
        uploaded_file = st.file_uploader("Upload CSV / Excel", type=['csv', 'xlsx', 'xls'])
        if uploaded_file is not None:
            if st.session_state.df is None or uploaded_file.name != st.session_state.get('uploaded_file_name'):
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.session_state.df = df
                    st.session_state.uploaded_file_name = uploaded_file.name
                    
                    buffer = []
                    buffer.append(f"Total Rows: {df.shape[0]}, Total Columns: {df.shape[1]}")
                    buffer.append(f"Columns: {', '.join(df.columns)}")
                    buffer.append(f"Data types:\n{df.dtypes}")
                    buffer.append(f"Sample data (first 3 rows):\n{df.head(3).to_string()}")
                    st.session_state.df_info = "\n".join(buffer)
                    
                    st.session_state.messages = []
                    st.session_state.generated_code = ""
                    st.session_state.result_df = None
                    
                    st.success(f"Loaded {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Error loading file: {e}")
                    
        if st.session_state.df is not None:
            with st.expander("📋 Schema", expanded=True):
                for col, dtype in st.session_state.df.dtypes.items():
                    st.caption(f"**{col}** `{dtype}`")
                    
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
        col_main, col_right = st.columns([7, 3], gap="large")
        
        with col_main:
            chat_container = st.container(height=600, border=False)
            with chat_container:
                if not st.session_state.messages and st.session_state.df is not None:
                    st.info("👋 Welcome! Ask me anything about your dataset.")
                    
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
                                    
                                with st.expander("Audit Trail & Code"):
                                    if msg.get("code"):
                                        st.code(msg["code"], language="python")
                                    else:
                                        st.write("No code was generated.")

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
        st.info("Recipe view placeholder.")
        
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
                            
                            analysis_result = run_analysis_pipeline(
                                prompt_text=prompt_text,
                                df=st.session_state.df,
                                df_info=st.session_state.df_info,
                                model_name=model_name,
                                temperature=temp
                            )
                            
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
