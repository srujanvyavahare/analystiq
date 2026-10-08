import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from utils.sandbox import execute_code
from utils.llm import configure_llm, get_insights_and_code

# Configure page
st.set_page_config(page_title="AnalystIQ", layout="wide", page_icon="📊")

# Load env variables and configure LLM
load_dotenv()
configure_llm()

# --- CSS for styling ---
def apply_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }
        
        .main-header {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 5px;
            color: #1e1e1e;
            letter-spacing: -0.5px;
        }
        .sub-header {
            font-size: 16px;
            color: #6c757d;
            margin-bottom: 25px;
            font-weight: 400;
        }
        .insight-box {
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
            border-left: 5px solid #2e66ff;
            color: #1e3a8a;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        .insight-box ul {
            margin-bottom: 0;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .sidebar-badge {
            background-color: #f0fdf4;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            color: #166534;
            font-size: 14px;
            border: 1px solid #dcfce7;
        }
        </style>
    """, unsafe_allow_html=True)

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
    st.markdown("<h1 style='text-align: center; margin-top: 10vh;'>Welcome to AnalystIQ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please log in to access your dashboard.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                # Basic hardcoded login for demonstration
                if username == "admin" and password == "admin":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please use admin/admin.")

# --- Dashboard ---
def show_dashboard():
    apply_css()
    
    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='color:#1e88e5;'>📊 AnalystIQ</h2>", unsafe_allow_html=True)
        st.write("Upload. Ask. Discover.")
        st.markdown("<br>", unsafe_allow_html=True)
        
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
                    
                    # Generate df_info for LLM
                    buffer = []
                    buffer.append(f"Total Rows: {df.shape[0]}, Total Columns: {df.shape[1]}")
                    buffer.append(f"Columns: {', '.join(df.columns)}")
                    buffer.append(f"Data types:\n{df.dtypes}")
                    buffer.append(f"Sample data (first 3 rows):\n{df.head(3).to_string()}")
                    st.session_state.df_info = "\n".join(buffer)
                    
                    # Clear chat history when new file is uploaded
                    st.session_state.messages = []
                    st.session_state.generated_code = ""
                    st.session_state.result_df = None
                    
                    st.success(f"Loaded {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Error loading file: {e}")
            else:
                st.success(f"Loaded {uploaded_file.name}")
                
        st.markdown("---")
        st.markdown("### Menu")
        if st.button("➕ New Analysis", use_container_width=True):
            st.session_state.messages = []
            st.session_state.generated_code = ""
            st.session_state.result_df = None
            st.rerun()
            
        with st.expander("💡 Example Questions"):
            st.markdown("""
            Try asking:
            - *What is the total number of rows?*
            - *Show me sales by region as a bar chart.*
            - *What are the top 5 products by revenue?*
            - *Show a line chart of sales over time.*
            """)
            
        with st.expander("🔖 Saved Insights"):
            if 'saved_insights' not in st.session_state:
                st.session_state.saved_insights = []
            if st.session_state.saved_insights:
                for idx, insight in enumerate(st.session_state.saved_insights):
                    st.success(f"**Insight {idx+1}:** {insight}")
            else:
                st.write("No insights saved yet. Click 'Save' under an AI response.")
                
        with st.expander("⚙️ Settings"):
            st.session_state.temperature = st.slider("AI Creativity (Temperature)", 0.0, 1.0, st.session_state.get('temperature', 0.2))
            
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        
        st.markdown('<div class="sidebar-badge">🔒 <strong>Your data is secure</strong><br><small>Files are processed in a sandboxed environment with zero data retention.</small></div>', unsafe_allow_html=True)

    # Main Layout
    st.markdown('<div class="main-header">Conversational Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Turn your data into insights with the power of AI</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 6], gap="large")
    
    with col1:
        st.markdown('<div class="sub-header" style="margin-bottom: 10px;">💬 Chat Area</div>', unsafe_allow_html=True)
        # Chat history container
        chat_container = st.container(height=650)
        with chat_container:
            if not st.session_state.messages and st.session_state.df is not None:
                st.info("👋 Welcome! Ask me anything about your dataset. For example: 'What are the top 5 products by sales?'")
                
            for idx, msg in enumerate(st.session_state.messages):
                with st.chat_message(msg["role"]):
                    if msg["role"] == "user":
                        st.write(msg["content"])
                    else:
                        if "insights" in msg and msg["insights"]:
                            st.markdown('<div class="insight-box"><strong>💡 Insights</strong><ul>' + 
                                        ''.join([f"<li>{i}</li>" for i in msg["insights"]]) + 
                                        '</ul></div>', unsafe_allow_html=True)
                            
                            # Add Save button
                            if st.button("🔖 Save Insight", key=f"save_btn_{idx}"):
                                if 'saved_insights' not in st.session_state:
                                    st.session_state.saved_insights = []
                                # Save the first bullet point or the whole thing
                                st.session_state.saved_insights.append(" | ".join(msg["insights"]))
                                st.rerun()
                                
                        if "error" in msg:
                            st.error(msg["error"])

        # Chat Input
        prompt = st.chat_input("Ask a question about your data...")
        if prompt:
            if st.session_state.df is None:
                st.error("Please upload a dataset first from the sidebar.")
            elif not os.environ.get("GEMINI_API_KEY"):
                st.error("GEMINI_API_KEY is not set in the environment.")
            else:
                # Display user prompt instantly
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
                
    with col2:
        st.markdown('<div class="sub-header" style="margin-bottom: 10px;">📊 Analysis & Data</div>', unsafe_allow_html=True)
        tab_viz, tab_data, tab_code = st.tabs(["🖼️ Visualizations", "🗃️ Data Preview", "🐍 Generated Code"])
        
        with tab_viz:
            viz_container = st.container(height=650)
            with viz_container:
                has_viz = False
                # Show the latest figure from the chat history
                for msg in reversed(st.session_state.messages):
                    if msg.get("role") == "assistant" and msg.get("fig") is not None:
                        if isinstance(msg["fig"], plt.Figure):
                            st.pyplot(msg["fig"])
                        else:
                            st.plotly_chart(msg["fig"], use_container_width=True)
                        has_viz = True
                        break
                if not has_viz:
                    st.info("Visualizations will appear here when you ask for charts or plots.")

        with tab_data:
            data_container = st.container(height=650)
            with data_container:
                if st.session_state.result_df is not None:
                    if isinstance(st.session_state.result_df, pd.DataFrame):
                        st.dataframe(st.session_state.result_df, use_container_width=True)
                    elif isinstance(st.session_state.result_df, pd.Series):
                        st.dataframe(st.session_state.result_df.to_frame(), use_container_width=True)
                elif st.session_state.df is not None:
                    st.dataframe(st.session_state.df, use_container_width=True)
                else:
                    st.info("Upload data to see a preview.")

        with tab_code:
            code_container = st.container(height=650)
            with code_container:
                if st.session_state.generated_code:
                    st.code(st.session_state.generated_code, language="python")
                else:
                    st.info("Code will appear here after you ask a question.")

    # We handle the assistant response outside the if prompt block, but we need to trigger it if the last message was user
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with col1:
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing your data and generating insights..."):
                        prompt_text = st.session_state.messages[-1]["content"]
                        
                        from core.pipeline import run_analysis_pipeline
                        
                        model_name = st.session_state.get('selected_model', 'gemini-3.6-flash')
                        temp = st.session_state.get('temperature', 0.2)
                        
                        analysis_result = run_analysis_pipeline(
                            prompt_text=prompt_text,
                            df=st.session_state.df,
                            df_info=st.session_state.df_info,
                            model_name=model_name,
                            temperature=temp
                        )
                        
                        st.session_state.generated_code = analysis_result.get("code", "")
                        
                        if not analysis_result["success"]:
                            st.session_state.messages.append({"role": "assistant", "error": analysis_result["error"]})
                        else:
                            st.session_state.result_df = analysis_result["result_df"] if analysis_result["result_df"] is not None else st.session_state.df.head()
                            st.session_state.messages.append({
                                "role": "assistant",
                                "fig": analysis_result["fig"],
                                "insights": analysis_result["insights"]
                            })
                        st.rerun()

# --- Main Routing ---
if __name__ == "__main__":
    if not st.session_state.logged_in:
        show_login()
    else:
        show_dashboard()
