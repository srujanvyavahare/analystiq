class Tokens:
    # Colors
    PRIMARY = "#1E40AF"
    ON_PRIMARY = "#FFFFFF"
    SECONDARY = "#3B82F6"
    ACCENT = "#D97706"
    BACKGROUND = "#F8FAFC"
    FOREGROUND = "#1E3A8A"
    MUTED = "#E9EEF6"
    BORDER = "#DBEAFE"
    DESTRUCTIVE = "#DC2626"
    FOCUS_RING = "#1E40AF"

    @classmethod
    def apply_plotly_template(cls):
        import plotly.io as pio
        import plotly.graph_objects as go
        
        template = go.layout.Template()
        template.layout.font = dict(family="Fira Sans, sans-serif", color=cls.FOREGROUND)
        template.layout.paper_bgcolor = "rgba(0,0,0,0)"
        template.layout.plot_bgcolor = "rgba(0,0,0,0)"
        template.layout.colorway = [cls.PRIMARY, cls.SECONDARY, cls.ACCENT, "#10B981", "#8B5CF6", "#F59E0B"]
        template.layout.xaxis = dict(showgrid=True, gridcolor=cls.BORDER, zerolinecolor=cls.BORDER)
        template.layout.yaxis = dict(showgrid=True, gridcolor=cls.BORDER, zerolinecolor=cls.BORDER)
        
        pio.templates["analystiq"] = template
        pio.templates.default = "analystiq"

    @classmethod
    def inject_css(cls):
        import streamlit as st
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
        
        :root {{
            --primary: {cls.PRIMARY};
            --on-primary: {cls.ON_PRIMARY};
            --secondary: {cls.SECONDARY};
            --accent: {cls.ACCENT};
            --background: {cls.BACKGROUND};
            --foreground: {cls.FOREGROUND};
            --muted: {cls.MUTED};
            --border: {cls.BORDER};
            --destructive: {cls.DESTRUCTIVE};
            --focus-ring: {cls.FOCUS_RING};
        }}
        
        /* Typography */
        html, body, [class*="css"] {{
            font-family: 'Fira Sans', sans-serif !important;
            font-size: 16px;
            line-height: 1.5;
            color: var(--foreground) !important;
        }}
        
        code, pre, .stDataFrame, table, .stCodeBlock {{
            font-family: 'Fira Code', monospace !important;
        }}
        
        /* Overrides */
        .stApp {{
            background-color: var(--background);
        }}
        
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] > div,
        [data-testid="stMetricLabel"] label,
        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricLabel"] span {{
            visibility: visible !important;
            display: block !important;
            color: var(--foreground) !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }}
        
        .stButton>button {{
            background-color: var(--secondary) !important;
            color: var(--on-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px !important;
        }}
        
        .stButton>button:hover {{
            background-color: var(--primary) !important;
            border-color: var(--focus-ring) !important;
        }}
        
        /* Density & Spacing */
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 1440px !important;
        }}
        
        div[data-testid="stSidebar"] {{
            background-color: var(--on-primary);
            border-right: 1px solid var(--border);
        }}
        </style>
        """, unsafe_allow_html=True)
