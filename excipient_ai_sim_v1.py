
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import numpy as np

@dataclass
class Excipient:
    name: str
    function: str
    range_min: float
    range_max: float
    flags: Dict[str, bool] = field(default_factory=dict)
    notes: str = ""

EXCIPIENTS_DB: List[Excipient] = [
    Excipient("Lactose monohydrate","Diluent",10,80, {"reducingSugar":True, "hygroscopic":False}, "May cause Maillard with amines."),
    Excipient("Microcrystalline cellulose (MCC)","Diluent",10,60, {"hygroscopic":False}, "Compressibility; wicking."),
    Excipient("Dicalcium phosphate anhydrous (DCPA)","Diluent",10,60, {"hygroscopic":False}, "Insoluble; brittle fracture."),
    Excipient("Povidone (PVP K30)","Binder",2,6, {"hygroscopic":True}, "Solution/dry binder; hygroscopic."),
    Excipient("Hydroxypropyl methylcellulose (HPMC)","Binder",1,5, {"hygroscopic":True}, "Viscosity-grade dependent; moderately hygroscopic."),
    Excipient("Croscarmellose sodium (CCS)","Disintegrant",2,5, {"alkaline":False}, "Crosslinked cellulose."),
    Excipient("Sodium starch glycolate (SSG)","Disintegrant",2,8, {"alkaline":True}, "Swelling; sodium salt can raise local pH."),
    Excipient("Crospovidone (XL-10)","Disintegrant",2,5, {"hygroscopic":False}, "Capillary action."),
    Excipient("Magnesium stearate","Lubricant",0.2,1.0, {"hydrophobic":True, "alkaline":True, "basicExcipient":True}, "Hydrophobic; basic; slows dissolution if high."),
    Excipient("Colloidal silicon dioxide","Glidant",0.1,1.0, {"adsorbent":True}, "Flow aid; moisture adsorbent."),
    Excipient("Opadry (HPMC-based)","Film coat",2,5, {"hygroscopic":True}, "Weight gain in % for coat."),
    Excipient("Polysorbate 80","Wetting agent",0.1,1.0, {"surfactant":True}, "Improves wetting."),
]

EX_BY_NAME: Dict[str, Excipient] = {e.name:e for e in EXCIPIENTS_DB}

@dataclass
class Component:
    name: str
    function: str
    pct: float
    def to_dict(self): return {"name":self.name,"function":self.function,"pct":self.pct}

@dataclass
class Formulation:
    api_name: str
    dosage_form: str  # 'ir_tablet' | 'capsule' | 'syrup'
    api_load_mg: float
    components: List[Component]
    notes: str = ""
    flags: Dict[str,bool] = field(default_factory=dict)

    def total_pct(self)->float:
        return float(sum(c.pct for c in self.components))

    def to_dataframe(self):
        import pandas as pd
        return pd.DataFrame([c.to_dict() for c in self.components])

    def validate(self)->List[Dict[str,str]]:
        msgs = []
        tot = self.total_pct()
        if abs(tot-100)<1e-6: msgs.append({"level":"ok","msg":f"Total is {tot:.2f}% (balanced)."})
        elif tot>100: msgs.append({"level":"err","msg":f"Total exceeds 100% ({tot:.2f}%). Reduce some excipients."})
        else: msgs.append({"level":"warn","msg":f"Total below 100% ({tot:.2f}%). Add q.s. diluent (e.g., MCC/DCPA/Lactose)."})
        funcs = {c.function for c in self.components if c.pct>0}
        if self.dosage_form=='ir_tablet':
            if 'Disintegrant' not in funcs: msgs.append({"level":"warn","msg":"IR tablet without disintegrant."})
            if 'Lubricant' not in funcs: msgs.append({"level":"warn","msg":"No lubricant present — sticking/picking risk."})
            if 'Glidant' not in funcs: msgs.append({"level":"warn","msg":"No glidant present — poor flow risk."})
        for c in self.components:
            e = EX_BY_NAME.get(c.name)
            if not e: continue
            if c.pct>0:
                if c.pct < e.range_min: msgs.append({"level":"warn","msg":f"{c.name} at {c.pct:.2f}% below typical {e.range_min}-{e.range_max}%."})
                if c.pct > e.range_max: msgs.append({"level":"warn","msg":f"{c.name} at {c.pct:.2f}% exceeds typical {e.range_min}-{e.range_max}%."})
            if e.flags.get("reducingSugar") and self.flags.get("amine"):
                msgs.append({"level":"warn","msg":f"{c.name} (reducing sugar) with amine APIs → Maillard risk; consider DCPA/MCC."})
            if e.name=='Magnesium stearate' and c.pct>1.0:
                msgs.append({"level":"warn","msg":"Magnesium stearate >1% can slow dissolution; keep minimal."})
        return msgs

    def validate_and_report(self)->Dict[str,object]:
        return {"api":self.api_name,"dosage_form":self.dosage_form,"api_load_mg":self.api_load_mg,
                "table":self.to_dataframe(),"messages":self.validate()}

    @staticmethod
    def example_ir_tablet(api_name="Model API", api_load_mg=200):
        comps = [
            Component("Microcrystalline cellulose (MCC)","Diluent",35.0),
            Component("Povidone (PVP K30)","Binder",3.0),
            Component("Croscarmellose sodium (CCS)","Disintegrant",3.0),
            Component("Colloidal silicon dioxide","Glidant",0.5),
            Component("Magnesium stearate","Lubricant",0.5),
        ]
        current = sum(c.pct for c in comps)
        if current<100:
            for c in comps:
                if c.name=="Microcrystalline cellulose (MCC)":
                    c.pct += 100-current
                    break
        return Formulation(api_name=api_name, dosage_form='ir_tablet', api_load_mg=api_load_mg, components=comps,
                           notes="Example IR tablet", flags={"poorSolubility":False,"amine":False})

class Simulators:
    @staticmethod
    def dissolution_weibull(T:int=60, beta:float=1.6, Td:float=12.0):
        t = np.linspace(0,T,T+1)
        F = 1.0 - np.exp(-(t/np.clip(Td,1e-6,None))**beta)
        return t, np.clip(F,0,1)
    @staticmethod
    def disintegration_time(dis_pct:float, lub_pct:float, mcc_pct:float)->float:
        base = 15.0
        t = base * (1.0/(1+0.25*dis_pct)) * (1+0.5*max(0.0, lub_pct-0.5)) * (1.0/(1+0.02*mcc_pct))
        return float(np.clip(t, 1.0, 60.0))

def evaluate_profile(form:Formulation)->Dict[str,object]:
    sim = Simulators()
    msgs = []; passed = True
    if abs(form.total_pct()-100.0)>1e-6:
        passed=False; msgs.append("Total not 100%.")
    funcs = {c.function for c in form.components if c.pct>0}
    if 'Disintegrant' not in funcs: passed=False; msgs.append("No Disintegrant.")
    if 'Glidant' not in funcs: passed=False; msgs.append("No Glidant.")
    lub_pct = next((c.pct for c in form.components if c.function=='Lubricant'), 0.0)
    if lub_pct>1.0: passed=False; msgs.append("Lubricant >1.0%.")
    dis_pct = next((c.pct for c in form.components if c.function=='Disintegrant'), 0.0)
    mcc_pct = next((c.pct for c in form.components if c.name=='Microcrystalline cellulose (MCC)'), 0.0)
    tdis = sim.disintegration_time(dis_pct,lub_pct,mcc_pct)
    if tdis>15.0: passed=False; msgs.append(f"Disintegration {tdis:.1f} min > 15.")
    t,F = sim.dissolution_weibull(T=60, beta=1.6, Td=max(5.0, tdis*0.8))
    if float(F[30])<0.80: passed=False; msgs.append("Dissolution 30 min < 0.80.")
    if passed: msgs.append("USP IR defaults passed.")
    return {"passed":passed,"details":msgs}

# -------- NEW: API–Excipient Compatibility Matrix --------
def compatibility_matrix(api_flags:Dict[str,bool], components:List[Component])->List[Dict[str,object]]:
    """
    Returns a list with per-excipient risk score (0-3) and reasons.
    api_flags may include: amine, acidic, basic, ester, aldehyde, phenol, thiol, moistureSensitive, poorSolubility
    """
    rows = []
    for c in components:
        e = EX_BY_NAME.get(c.name)
        if not e: continue
        score = 0
        reasons = []

        # Maillard: amine API + reducing sugar excipient (e.g., lactose)
        if api_flags.get("amine") and e.flags.get("reducingSugar"):
            score = max(score, 3); reasons.append("Maillard risk: amine API + reducing sugar (browning).")

        # Moisture: moisture-sensitive API + hygroscopic binders/coats
        if api_flags.get("moistureSensitive") and e.flags.get("hygroscopic"):
            score = max(score, 2); reasons.append("Moisture uptake: hygroscopic excipient with moisture‑sensitive API.")

        # Hydrolysis: ester API with alkaline/basic excipients or high-moisture binders
        if api_flags.get("ester") and (e.flags.get("alkaline") or e.flags.get("basicExcipient") or e.flags.get("hygroscopic")):
            score = max(score, 2); reasons.append("Ester hydrolysis risk: alkaline/hygroscopic environment.")

        # Acidic API with basic/alkaline excipients (salt formation / dissolution issues)
        if api_flags.get("acidic") and e.flags.get("basicExcipient"):
            score = max(score, 2); reasons.append("Acid–base interaction: acidic API with basic lubricant (salt formation).")

        # Basic API with alkaline disintegrants (SSG local pH ↑)
        if api_flags.get("basic") and e.name == "Sodium starch glycolate (SSG)":
            score = max(score, 1); reasons.append("Local pH shifts (Na+ SSG) may affect basic APIs.")

        # Poor solubility + hydrophobic lubricant at high %
        if api_flags.get("poorSolubility") and e.name=="Magnesium stearate" and c.pct>=1.0:
            score = max(score, 2); reasons.append("Hydrophobic film from high Mg stearate can slow wetting/dissolution.")

        # Default minor risk for unknown interactions
        if score==0:
            reasons.append("No specific risk detected with current rules.")

        rows.append({"excipient": c.name, "function": c.function, "pct": c.pct, "risk": int(score), "reasons": reasons})
    return rows
