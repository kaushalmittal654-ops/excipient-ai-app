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

# --- Local Imports ---
from excipient_ai_sim_v1 import (
    Formulation, Component, Simulators, evaluate_profile,
    EXCIPIENTS_DB, compatibility_matrix
)
from knowledge_base import REACTION_EVIDENCE

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="ExcipientAI v2.0",
    page_icon="💊",
    layout="wide"
)

# --- Header ---
cols_header = st.columns([1, 10])
with cols_header[0]:
    st.image("https://www.nicepng.com/png/detail/22-221946_research-and-development-icon-png.png", width=100)
with cols_header[1]:
    st.title("ExcipientAI v2.0 — Formulation Intelligence System")
    st.info("This AI-powered system predicts drug-excipient compatibility, simulates performance, and provides evidence-based risk analysis for pharmaceutical formulations.")

# ------------------ DATA PRESETS ------------------
API_PRESETS = {
    "Paracetamol": {"flags": {}, "starter": Formulation.example_ir_tablet("Paracetamol", 500).components},
    "Metformin (amine)": {"flags": {"amine": True}, "starter": Formulation.example_ir_tablet("Metformin", 500).components},
    "Aspirin (acidic + ester)": {"flags": {"acidic": True, "ester": True}, "starter": Formulation.example_ir_tablet("Aspirin", 325).components},
    "Amoxicillin (amine + moisture-sensitive)": {"flags": {"amine": True, "moistureSensitive": True}, "starter": Formulation.example_ir_tablet("Amoxicillin", 500).components},
    "Carbamazepine (poorly soluble)": {"flags": {"poorSolubility": True}, "starter": Formulation.example_ir_tablet("Carbamazepine", 200).components},
    "Ibuprofen (weak acid)": {"flags": {"acidic": True}, "starter": Formulation.example_ir_tablet("Ibuprofen", 200).components},
    "Propranolol (basic amine)": {"flags": {"basic": True}, "starter": Formulation.example_ir_tablet("Propranolol", 40).components},
}

# ------------------ HELPER FUNCTIONS ------------------
def get_risk_color_hex(risk):
    if risk == 3: return "#FFC7CE"  # High Risk - Red
    if risk == 2: return "#FFEB9C"  # Moderate Risk - Yellow
    if risk == 1: return "#C6EFCE"  # Low Risk - Green
    if risk == 0: return "#F0F0F0"  # No Risk - Light Grey
    return None

def highlight_risks_in_ui(row):
    color = get_risk_color_hex(row['Risk'])
    return [f'background-color: {color}'] * len(row) if color else [''] * len(row)

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.header("⚙️ Formulation Setup")

    preset = st.selectbox("Select API Preset", list(API_PRESETS.keys()), index=0)
    api = st.text_input("API Name", preset.split(" (")[0])
    load = st.number_input("API Load (mg)", min_value=1, max_value=1000, value=500, step=25)
    form = st.selectbox("Dosage Form", ["ir_tablet", "capsule", "syrup"], index=0)

    with st.expander("🔬 Advanced API Flags (Chemical Properties)"):
        pflags = {k: False for k in ["amine","acidic","basic","ester","aldehyde","phenol","thiol","moistureSensitive","poorSolubility"]}
        pflags.update(API_PRESETS[preset]["flags"])
        st.markdown("Select the chemical properties of your API.")
        cols = st.columns(2)
        pflags["amine"] = cols[0].checkbox("Amine", value=pflags["amine"], help="Contains a primary or secondary amine group (risk of Maillard reaction).")
        pflags["acidic"] = cols[0].checkbox("Acidic", value=pflags["acidic"], help="Is an acidic compound (risk of acid-base reactions).")
        pflags["ester"] = cols[0].checkbox("Ester", value=pflags["ester"], help="Contains an ester functional group (risk of hydrolysis).")
        pflags["moistureSensitive"] = cols[1].checkbox("Moisture Sensitive", value=pflags["moistureSensitive"], help="Degrades in the presence of water.")
        pflags["poorSolubility"] = cols[1].checkbox("Poorly Soluble", value=pflags["poorSolubility"], help="Has low water solubility (BCS Class II/IV).")

    st.markdown("---")
    
    st.header("💾 Save & Load")
    formulation_json = st.session_state.get('table', pd.DataFrame()).to_json(orient='records')
    st.download_button(
        label="Save Formulation",
        data=formulation_json,
        file_name=f"{api}_formulation.json",
        mime="application/json",
        help="Save the current formulation table to a file."
    )
    uploaded_file = st.file_uploader("Load Formulation", type=["json"], help="Load a previously saved formulation file.")
    if uploaded_file is not None:
        try:
            st.session_state['table'] = pd.read_json(uploaded_file)
            st.success("Formulation loaded successfully!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Error loading file: {e}")

# ------------------ INIT ------------------
if 'table' not in st.session_state or st.session_state['table'].empty:
    st.session_state['table'] = pd.DataFrame([c.__dict__ for c in API_PRESETS[preset]["starter"]])

components = [Component(r["name"], r["function"], float(r["pct"])) for _,r in st.session_state['table'].iterrows()]
f = Formulation(api_name=api, dosage_form=form, api_load_mg=load, components=components, flags=pflags)
comp_results = compatibility_matrix(pflags, components)

# ------------------ MAIN TABS ------------------
st.header("Formulation Analysis Dashboard")
tabs = st.tabs(["📝 Formulation Table", "📊 Compatibility Analysis", "🧪 Simulation", "📚 Evidence Explorer", "📑 Export Report"])

with tabs[0]:
    st.subheader("Add, Edit, or Remove Excipients")
    
    with st.form("add_excipient_form"):
        cols = st.columns([2, 2, 1, 1])
        func_options = sorted({e.function for e in EXCIPIENTS_DB})
        func_choice = cols[0].selectbox("Function", func_options)
        name_options = [e.name for e in EXCIPIENTS_DB if e.function == func_choice]
        name_choice = cols[1].selectbox("Excipient Name", name_options)
        pct_choice = cols[2].number_input("% w/w", min_value=0.0, step=0.1, value=1.0)
        submitted = cols[3].form_submit_button("Add")

        if submitted:
            df = st.session_state['table'].copy()
            new_row = {"name": name_choice, "function": func_choice, "pct": float(pct_choice)}
            st.session_state['table'] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    st.session_state['table'] = st.data_editor(
        st.session_state['table'],
        num_rows="dynamic",
        use_container_width=True,
        column_config={"pct": st.column_config.NumberColumn("Weight %", format="%.2f%%")}
    )

with tabs[1]:
    st.subheader("Predicted API–Excipient Risks")
    
    dfc = pd.DataFrame([{
        "Excipient": r["excipient"],
        "Function": r["function"],
        "Risk": r["risk"],
        "Risk Level": "⚪️ None" if r["risk"]==0 else ("🟢 Low" if r["risk"]==1 else ("🟡 Moderate" if r["risk"]==2 else "🔴 High"))
    } for r in comp_results])

    st.dataframe(dfc.style.apply(highlight_risks_in_ui, axis=1), use_container_width=True)
    st.caption("Risk scale: 0=None, 1=Low, 2=Moderate, 3=High")
    
    st.markdown("---")
    
    st.subheader("Chemical Rationale for High Risks")
    high_risks_found = False
    for r in comp_results:
        if r['risk'] >= 2:
            excipient_details = next((e for e in EXCIPIENTS_DB if e.name == r['excipient']), None)
            if excipient_details:
                for reaction, details in REACTION_EVIDENCE.items():
                    flags_match = all(pflags.get(flag) for flag in details['flags_needed'])
                    props_match = any(prop in excipient_details.properties for prop in details['excipient_properties'])
                    
                    if flags_match and props_match:
                        with st.expander(f"⚠️ {r['excipient']} ({reaction}) - Risk Level: {details['risk_level']}"):
                            st.error(details['explanation'])
                            high_risks_found = True
    
    if not high_risks_found:
        st.success("No significant chemical interaction risks were identified based on the provided API flags.")

with tabs[2]:
    st.subheader("In-Vitro Performance Simulation")
    dis_pct = next((c.pct for c in components if c.function=="Disintegrant"), 0.0)
    lub_pct = next((c.pct for c in components if c.function=="Lubricant"), 0.0)
    t_dis = Simulators.disintegration_time(dis_pct,lub_pct,0)
    t, F = Simulators.dissolution_weibull(T=60, beta=1.6, Td=max(5.0, t_dis*0.8))

    cols = st.columns(2)
    cols[0].metric("Estimated Disintegration Time (min)", f"{t_dis:.1f}")
    
    total_cost = sum(
        (c.pct / 100) * getattr(next((e for e in EXCIPIENTS_DB if e.name == c.name), None), 'cost_per_kg', 0)
        for c in components
    )
    cols[1].metric("Estimated Excipient Cost per kg", f"${total_cost:.2f}")

    st.line_chart(pd.DataFrame({"Fraction dissolved":F}, index=t))

with tabs[3]:
    st.subheader("Literature Evidence Explorer")
    ev_full = pd.read_csv("api_excipient_evidence_v17.csv")
    
    cols = st.columns(3)
    api_filter = cols[0].multiselect("Filter by API", sorted(ev_full["api"].unique().tolist()))
    excipient_filter = cols[1].multiselect("Filter by Excipient", sorted(ev_full["excipient"].unique().tolist()))
    
    if 'outcome' in ev_full.columns:
        outcome_filter = cols[2].multiselect("Filter by Outcome", sorted(ev_full["outcome"].unique().tolist()))
    else:
        outcome_filter = []

    ev = ev_full
    if api_filter: ev = ev[ev["api"].isin(api_filter)]
    if excipient_filter: ev = ev[ev["excipient"].isin(excipient_filter)]
    if outcome_filter: ev = ev[ev["outcome"].isin(outcome_filter)]
    
    st.dataframe(ev, use_container_width=True,
                   column_config={"url": st.column_config.LinkColumn("Source", display_text="🔗 Link")})

with tabs[4]:
    st.subheader("Generate & Download PDF Report")
    if st.button("Generate PDF Report", key="pdf_button"):
        with st.spinner("Generating PDF..."):
            # --- START of PDF Generation Logic ---
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            styles = getSampleStyleSheet()
            story = []
            
            HEADER_COLOR = HexColor("#003366")

            story.append(Paragraph("ExcipientAI Compatibility Report", styles['h1']))
            story.append(Spacer(1, 0.25 * inch))

            story.append(Paragraph("1. Formulation Overview", styles['h2']))
            story.append(Paragraph(f"<b>API Name:</b> {f.api_name}", styles['Normal']))
            story.append(Paragraph(f"<b>API Load:</b> {f.api_load_mg} mg", styles['Normal']))
            story.append(Paragraph(f"<b>Dosage Form:</b> {f.dosage_form}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
            
            formulation_df = st.session_state['table']
            formulation_data = [formulation_df.columns.values.tolist()] + formulation_df.values.tolist()
            table = Table(formulation_data, colWidths=[3.5*inch, 2*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.25 * inch))

            story.append(Paragraph("2. Compatibility Analysis", styles['h2']))
            comp_df = dfc[["Excipient", "Risk Level"]] 
            comp_data = [comp_df.columns.values.tolist()] + comp_df.values.tolist()
            
            comp_styles = [
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]
            
            for i, row_data in enumerate(comp_results):
                risk_color_hex = get_risk_color_hex(row_data['risk'])
                if risk_color_hex:
                    comp_styles.append(('BACKGROUND', (0, i + 1), (-1, i + 1), HexColor(risk_color_hex)))

            table_comp = Table(comp_data, colWidths=[3.5*inch, 3*inch])
            table_comp.setStyle(TableStyle(comp_styles))
            story.append(table_comp)
            story.append(Spacer(1, 0.25 * inch))

            story.append(Paragraph("3. Simulation Results", styles['h2']))
            story.append(Paragraph(f"<b>Estimated Disintegration Time:</b> {t_dis:.1f} minutes", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

            fig, ax = plt.subplots(figsize=(7, 3.5), dpi=300)
            ax.plot(t, F, marker='o', linestyle='-', color='b')
            ax.set_title("Estimated Dissolution Profile")
            ax.set_xlabel("Time (min)")
            ax.set_ylabel("Fraction Dissolved")
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)
            ax.set_ylim(0, 1.1)
            ax.set_xlim(0, max(t)*1.05)
            fig.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='PNG')
            img_buffer.seek(0)
            plt.close(fig)
            
            dissolution_chart = Image(img_buffer, width=6.5*inch, height=3.25*inch)
            story.append(dissolution_chart)
            story.append(Spacer(1, 0.25 * inch))
            
            story.append(Paragraph("4. Sourced Evidence", styles['h2']))
            desired_evidence_cols = ['api', 'excipient', 'outcome', 'severity', 'url']
            available_evidence_cols = [col for col in desired_evidence_cols if col in ev.columns]
            
            if available_evidence_cols:
                evidence_df = ev[available_evidence_cols].copy()
                data_as_paragraphs = [[Paragraph(str(col), styles['Normal']) for col in evidence_df.columns.values.tolist()]]
                for index, row in evidence_df.iterrows():
                    data_as_paragraphs.append([Paragraph(str(cell), styles['Normal']) for cell in row])
                
                col_widths = [1*inch, 1.5*inch, 1.25*inch, 0.75*inch, 2*inch]
                if len(col_widths) > len(available_evidence_cols):
                    col_widths = col_widths[:len(available_evidence_cols)]
                
                table_ev = Table(data_as_paragraphs, colWidths=col_widths)
                table_ev.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 8)
                ]))
                story.append(table_ev)
            else:
                story.append(Paragraph("No evidence data with expected columns found.", styles['Normal']))

            doc.build(story)
            
            buffer.seek(0)
            st.success("✅ PDF Generated!")
            st.download_button(
                label="Download PDF Report",
                data=buffer,
                file_name=f"ExcipientAI_Report_{f.api_name}.pdf",
                mime="application/pdf"
            )

