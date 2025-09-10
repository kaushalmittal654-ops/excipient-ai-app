import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch

from excipient_ai_sim_v1 import (
    Formulation, Component, Simulators, evaluate_profile,
    EXCIPIENTS_DB, API_PRESETS, compatibility_matrix
)
from knowledge_base import REACTION_EVIDENCE

st.set_page_config(page_title="ExcipientAI v4.1", page_icon="💊", layout="wide")

cols_header = st.columns([1, 10])
with cols_header[0]: st.image("https://www.nicepng.com/png/detail/22-221946_research-and-development-icon-png.png", width=100)
with cols_header[1]:
    st.title("ExcipientAI v4.1 — Final Version")
    st.info("Upgraded with accurate simulations and user-controlled dynamic formulation.")

def get_risk_color_hex(risk):
    if risk == 3: return "#FFC7CE"
    if risk == 2: return "#FFEB9C"
    if risk == 1: return "#C6EFCE"
    if risk == 0: return "#F0F0F0"
    return None

def highlight_risks_in_ui(row):
    color = get_risk_color_hex(row['Risk'])
    return [f'background-color: {color}'] * len(row) if color else [''] * len(row)

with st.sidebar:
    st.header("⚙️ Formulation Setup")
    
    preset = st.selectbox("Select API Preset", list(API_PRESETS.keys()))
    api_details = API_PRESETS[preset]
    
    # This button is now the ONLY way to load a preset into the main table
    if st.button("Load Starter Formulation for Selected API"):
        st.session_state.table = pd.DataFrame([c.__dict__ for c in api_details["starter"]])
        st.rerun()

    api = st.text_input("API Name", preset)
    default_load = api_details.get("default_load", 100.0)
    load = st.number_input("API Load (mg)", min_value=0.1, max_value=1000.0, value=default_load, step=10.0, format="%.1f")
    form = st.selectbox("Dosage Form", ["ir_tablet", "capsule", "syrup"])

    with st.expander("🔬 Advanced API Flags (Chemical Properties)", expanded=True):
        # These checkboxes now reflect the SELECTED preset, but do not alter the main table
        pflags = api_details["flags"].copy()
        pflags["amine"] = st.checkbox("Amine", value=pflags.get("amine", False))
        pflags["acidic"] = st.checkbox("Acidic", value=pflags.get("acidic", False))
        pflags["basic"] = st.checkbox("Basic", value=pflags.get("basic", False))
        pflags["ester"] = st.checkbox("Ester", value=pflags.get("ester", False))
        pflags["moistureSensitive"] = st.checkbox("Moisture Sensitive", value=pflags.get("moistureSensitive", False))
        pflags["poorSolubility"] = st.checkbox("Poorly Soluble", value=pflags.get("poorSolubility", False))
        pflags["chelation"] = st.checkbox("Chelation Risk", value=pflags.get("chelation", False))

    st.markdown("---")
    st.header("💾 Save & Load")
    
    formulation_df = st.session_state.get('table', pd.DataFrame())
    formulation_json = formulation_df.to_json(orient='records')
    st.download_button("Save Formulation", formulation_json, f"{api}_formulation.json", "application/json")
    
    uploaded_file = st.file_uploader("Load Formulation", type=["json"])
    if uploaded_file:
        try:
            st.session_state.table = pd.read_json(uploaded_file)
            st.success("Formulation loaded!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading file: {e}")

# Initialize the formulation table only on the very first run
if 'table' not in st.session_state:
    st.session_state.table = pd.DataFrame([c.__dict__ for c in API_PRESETS["Paracetamol"]["starter"]])

# --- Core Logic ---
components = [Component(r["name"], r["function"], float(r["pct"])) for _, r in st.session_state.table.iterrows()]
f = Formulation(api_name=api, dosage_form=form, api_load_mg=load, components=components, flags=pflags)
comp_results = compatibility_matrix(pflags, components)

st.header("Formulation Analysis Dashboard")
tabs = st.tabs(["📝 Formulation Table", "📊 Compatibility Analysis", "🧪 Simulation", "📚 Evidence Explorer", "📑 Export Report"])

with tabs[0]:
    st.subheader("Add, Edit, or Remove Excipients")
    with st.form("add_excipient_form"):
        cols = st.columns([2, 2, 1, 1])
        func_choice = cols[0].selectbox("Function", sorted({e.function for e in EXCIPIENTS_DB}))
        name_choice = cols[1].selectbox("Excipient Name", [e.name for e in EXCIPIENTS_DB if e.function == func_choice])
        pct_choice = cols[2].number_input("% w/w", min_value=0.0, step=0.1, value=1.0)
        if cols[3].form_submit_button("Add"):
            new_row = {"name": name_choice, "function": func_choice, "pct": float(pct_choice)}
            st.session_state.table = pd.concat([st.session_state.table, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()
    st.session_state.table = st.data_editor(st.session_state.table, num_rows="dynamic", use_container_width=True, column_config={"pct": st.column_config.NumberColumn("Weight %", format="%.2f%%")})

with tabs[1]:
    st.subheader("Predicted API–Excipient Risks")
    dfc = pd.DataFrame([{"Excipient": r["excipient"], "Function": r["function"], "Risk": r["risk"], "Risk Level": "⚪️ None" if r["risk"]==0 else ("🟢 Low" if r["risk"]==1 else ("🟡 Moderate" if r["risk"]==2 else "🔴 High"))} for r in comp_results])
    st.dataframe(dfc.style.apply(highlight_risks_in_ui, axis=1), use_container_width=True)
    
    st.subheader("Evidence-Backed Chemical Rationale")
    high_risks_found = False
    for r in comp_results:
        if r['risk'] >= 2:
            excipient_details = next((e for e in EXCIPIENTS_DB if e.name == r['excipient']), None)
            if excipient_details:
                for reaction, details in REACTION_EVIDENCE.items():
                    if all(pflags.get(flag) for flag in details['flags_needed']) and any(prop in excipient_details.properties for prop in details['excipient_properties']):
                        with st.expander(f"⚠️ {r['excipient']} ({reaction}) - Risk Level: {details['risk_level']}"):
                            st.error(details['explanation'])
                            st.info(f"**Source:** {details['citation']}")
                            st.markdown(f"[Read More Here]({details['source_url']})")
                            high_risks_found = True
    if not high_risks_found:
        st.success("No significant chemical interaction risks were identified based on the provided API flags and evidence base.")

with tabs[2]:
    st.subheader("In-Vitro Performance Simulation")
    dis_pct = next((c.pct for c in components if c.function=="Disintegrant"), 0.0)
    lub_pct = next((c.pct for c in components if c.function=="Lubricant"), 0.0)
    # ACCURATE SIMULATION: Pass the current API flags to the simulator
    t_dis = Simulators.disintegration_time(pflags, dis_pct, lub_pct)
    t, F = Simulators.dissolution_weibull(pflags, Td=max(5.0, t_dis*0.8))
    cols = st.columns(2)
    cols[0].metric("Estimated Disintegration Time (min)", f"{t_dis:.1f}")
    total_cost = sum((c.pct / 100) * getattr(next((e for e in EXCIPIENTS_DB if e.name == c.name), None), 'cost_per_kg', 0) for c in components)
    cols[1].metric("Estimated Excipient Cost per kg", f"${total_cost:.2f}")
    st.line_chart(pd.DataFrame({"Fraction dissolved (%)":F}, index=t).set_index(pd.Index(t, name="Time (min)")))

with tabs[3]:
    st.subheader("Literature Evidence Explorer")
    ev_full = pd.read_csv("api_excipient_evidence_v17.csv")
    cols = st.columns(3)
    api_filter = cols[0].multiselect("Filter by API", sorted(ev_full["api"].unique().tolist()))
    excipient_filter = cols[1].multiselect("Filter by Excipient", sorted(ev_full["excipient"].unique().tolist()))
    outcome_filter = cols[2].multiselect("Filter by Outcome", sorted(ev_full["outcome"].unique().tolist())) if 'outcome' in ev_full.columns else []
    
    ev = ev_full
    if api_filter: ev = ev[ev["api"].isin(api_filter)]
    if excipient_filter: ev = ev[ev["excipient"].isin(excipient_filter)]
    if outcome_filter: ev = ev[ev["outcome"].isin(outcome_filter)]
    st.dataframe(ev, use_container_width=True, column_config={"url": st.column_config.LinkColumn("Source", display_text="🔗 Link")})

with tabs[4]:
    st.subheader("Generate & Download PDF Report")
    if st.button("Generate PDF Report"):
        with st.spinner("Generating PDF..."):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            HEADER_COLOR = HexColor("#003366")

            story.append(Paragraph("ExcipientAI Compatibility Report", styles['h1']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>API Name:</b> {f.api_name}", styles['Normal']))
            story.append(Spacer(1, 24))

            story.append(Paragraph("1. Formulation Details", styles['h2']))
            formulation_data = [st.session_state.table.columns.tolist()] + st.session_state.table.values.tolist()
            table = Table(formulation_data, colWidths=[3.5*inch, 2*inch, 1*inch])
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            story.append(table)
            story.append(Spacer(1, 24))

            story.append(Paragraph("2. Compatibility Analysis", styles['h2']))
            comp_data = [dfc[["Excipient", "Risk Level"]].columns.tolist()] + dfc[["Excipient", "Risk Level"]].values.tolist()
            comp_styles = [('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0, 0), (-1, -1), 1, colors.black)]
            for i, row_data in enumerate(comp_results):
                risk_color_hex = get_risk_color_hex(row_data['risk'])
                if risk_color_hex: comp_styles.append(('BACKGROUND', (0, i + 1), (-1, i + 1), HexColor(risk_color_hex)))
            table_comp = Table(comp_data, colWidths=[3.5*inch, 3*inch])
            table_comp.setStyle(TableStyle(comp_styles))
            story.append(table_comp)
            story.append(Spacer(1, 24))

            story.append(Paragraph("3. Simulation Results", styles['h2']))
            fig, ax = plt.subplots(figsize=(7, 3.5), dpi=300)
            ax.plot(t, F, marker='o', linestyle='-')
            ax.set_title("Estimated Dissolution Profile")
            ax.set_xlabel("Time (min)")
            ax.set_ylabel("Fraction Dissolved (%)")
            ax.grid(True)
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='PNG')
            plt.close(fig)
            story.append(Image(img_buffer, width=6.5*inch, height=3.25*inch))
            story.append(Spacer(1, 24))
            
            story.append(Paragraph("4. Sourced Evidence", styles['h2']))
            if not ev.empty:
                evidence_data = [ev.columns.tolist()] + ev.values.tolist()
                data_as_paragraphs = [[Paragraph(str(cell), styles['Normal']) for cell in row] for row in evidence_data]
                table_ev = Table(data_as_paragraphs, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 0.8*inch, 1.8*inch])
                table_ev.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black), ('FONTSIZE', (0,0), (-1,-1), 8), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
                ]))
                story.append(table_ev)
            
            doc.build(story)
            buffer.seek(0)
            st.success("✅ PDF Generated!")
            st.download_button("Download PDF Report", buffer, f"ExcipientAI_Report_{f.api_name}.pdf", "application/pdf")

