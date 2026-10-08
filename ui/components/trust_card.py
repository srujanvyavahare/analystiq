import streamlit as st
from ui.tokens import Tokens

def render_confidence_chip(confidence: str, reasons: list):
    """
    Renders the Red/Amber/Green confidence chip.
    """
    if confidence == "Red":
        bg_color = Tokens.DESTRUCTIVE
        text_color = Tokens.ON_PRIMARY
        icon = "🔴"
    elif confidence == "Amber":
        bg_color = Tokens.ACCENT
        text_color = Tokens.ON_PRIMARY
        icon = "🟠"
    else:
        bg_color = "#166534" # Green
        text_color = Tokens.ON_PRIMARY
        icon = "🟢"
        
    reason_text = " • ".join(reasons) if reasons else "High confidence. No anomalies detected."
        
    st.markdown(f"""
        <div title="{reason_text}" style="
            display: inline-flex;
            align-items: center;
            background-color: {bg_color};
            color: {text_color};
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            cursor: help;
            margin-bottom: 10px;
        ">
            {icon} {confidence}
        </div>
    """, unsafe_allow_html=True)

def render_trust_layer(msg_idx: int, assumptions: dict, exec_facts: dict, confidence: str, reasons: list):
    """
    Renders the 'How this was computed' panel.
    """
    render_confidence_chip(confidence, reasons)
    
    with st.expander("🔍 How this was computed (Audit & Override)"):
        st.markdown("**Assumptions Made:**")
        if assumptions:
            st.caption(f"**Interpretation:** {assumptions.get('interpretation', 'N/A')}")
            st.caption(f"**Columns Used:** {', '.join(assumptions.get('columns_used', []))}")
            st.caption(f"**Filters:** {assumptions.get('filters_applied', 'None')}")
            
            # Edit overrides
            with st.form(f"override_form_{msg_idx}"):
                override = st.text_input("Correct this interpretation (e.g. 'Use Q4 instead of Q3'):", key=f"override_input_{msg_idx}")
                if st.form_submit_button("Re-run with Correction"):
                    # We store this override in session state so the main loop can pick it up
                    st.session_state.pending_override = {
                        "idx": msg_idx,
                        "text": override
                    }
                    st.rerun()
        else:
            st.write("No assumptions recorded.")
            
        st.divider()
        st.markdown("**Execution Facts:**")
        if exec_facts:
            rows_in = exec_facts.get('rows_in', 0)
            rows_out = exec_facts.get('rows_out', 0)
            st.caption(f"**Rows:** {rows_in} in ➔ {rows_out} out")
            if 'dropped_pct' in exec_facts:
                st.caption(f"**Dropped:** {exec_facts['dropped_pct']:.1f}% of data")
        else:
            st.write("No execution facts generated.")
            
        # Render Guardrails prominently
        guardrails = [r for r in reasons if r.startswith("GUARDRAIL")]
        if guardrails:
            st.divider()
            st.markdown("⚠️ **Statistical Guardrails Triggered:**")
            for g in guardrails:
                # Remove the prefix for display
                clean_msg = g.split("): ", 1)[1] if "): " in g else g
                if "(Red)" in g:
                    st.error(clean_msg)
                else:
                    st.warning(clean_msg)
