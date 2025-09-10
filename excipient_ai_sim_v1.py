import random
import numpy as np  # FIXED: Added this missing import statement

# --- DATA CLASSES ---
class Excipient:
    def __init__(self, name, function, properties, cost_per_kg):
        self.name = name
        self.function = function
        self.properties = properties
        self.cost_per_kg = cost_per_kg

class Component:
    def __init__(self, name, function, pct):
        self.name = name
        self.function = function
        self.pct = pct

class Formulation:
    def __init__(self, api_name, dosage_form, api_load_mg, components, flags):
        self.api_name = api_name
        self.dosage_form = dosage_form
        self.api_load_mg = api_load_mg
        self.components = components
        self.flags = flags

    def validate_and_report(self):
        # Placeholder for validation logic
        return {"total_pct": sum(c.pct for c in self.components)}

    @staticmethod
    def example_ir_tablet(api_name, load_mg):
        return Formulation(
            api_name=api_name,
            dosage_form="ir_tablet",
            api_load_mg=load_mg,
            components=[
                Component("Microcrystalline cellulose (MCC)", "Diluent", 93.0),
                Component("Povidone (PVP K30)", "Binder", 3.0),
                Component("Croscarmellose sodium (CCS)", "Disintegrant", 3.0),
                Component("Colloidal silicon dioxide", "Glidant", 0.5),
                Component("Magnesium stearate", "Lubricant", 0.5),
            ],
            flags={}
        )

# --- EXCIPIENT DATABASE ---
EXCIPIENTS_DB = [
    Excipient("Microcrystalline cellulose (MCC)", "Diluent", ["low_moisture", "inert"], 2.50),
    Excipient("Lactose monohydrate", "Diluent", ["reducing_sugar", "high_moisture"], 1.80),
    Excipient("Dicalcium phosphate (DCP)", "Diluent", ["basic", "low_moisture"], 2.00),
    Excipient("Starch (Corn)", "Diluent", ["high_moisture"], 1.50),
    Excipient("Mannitol", "Diluent", ["inert", "low_moisture"], 3.00),
    Excipient("Povidone (PVP K30)", "Binder", ["peg_like", "binder_property"], 5.50),
    Excipient("Hydroxypropyl methylcellulose (HPMC)", "Binder", ["inert", "polymer"], 7.00),
    Excipient("Croscarmellose sodium (CCS)", "Disintegrant", ["superdisintegrant"], 8.00),
    Excipient("Sodium starch glycolate (SSG)", "Disintegrant", ["superdisintegrant"], 7.50),
    Excipient("Magnesium stearate", "Lubricant", ["hydrophobic", "basic"], 10.00),
    Excipient("Stearic acid", "Lubricant", ["hydrophobic", "acidic"], 9.00),
    Excipient("Colloidal silicon dioxide", "Glidant", ["inert", "glidant_property"], 12.00),
    Excipient("Talc", "Glidant", ["inert"], 4.00),
    Excipient("Sodium lauryl sulfate (SLS)", "Wetting Agent", ["surfactant"], 6.00),
    Excipient("Polysorbate 80", "Wetting Agent", ["surfactant", "peg_like"], 15.00),
    Excipient("Opadry (HPMC coat)", "Coating Agent", ["inert", "coating"], 20.00),
]


# --- COMPATIBILITY LOGIC ---
def compatibility_matrix(api_flags, components):
    results = []
    for comp in components:
        risk = 0
        excipient = next((e for e in EXCIPIENTS_DB if e.name == comp.name), None)
        if not excipient:
            results.append({"excipient": comp.name, "function": comp.function, "pct": comp.pct, "risk": 0})
            continue

        if api_flags.get("amine") and "reducing_sugar" in excipient.properties: risk = max(risk, 3)
        if (api_flags.get("ester") or api_flags.get("moistureSensitive")) and "high_moisture" in excipient.properties: risk = max(risk, 3)
        if api_flags.get("acidic") and "basic" in excipient.properties: risk = max(risk, 2)
        if api_flags.get("ester") and "peg_like" in excipient.properties: risk = max(risk, 2)

        results.append({"excipient": comp.name, "function": comp.function, "pct": comp.pct, "risk": risk})
    return results


# --- SIMULATORS ---
class Simulators:
    @staticmethod
    def disintegration_time(disintegrant_pct, lubricant_pct, mcc_pct):
        base_time = 15.0
        time = base_time - (disintegrant_pct * 2.5)
        time = time + (lubricant_pct * 3.0)
        return max(2.0, min(time, 30.0))

    @staticmethod
    def dissolution_weibull(T, beta, Td):
        t = np.linspace(0, 60, 13)
        F = 1 - np.exp(-(((t - 0)**beta)) / Td**beta)
        return t, F * 100

def evaluate_profile(formulation):
    return {"passed": random.choice([True, False])}
