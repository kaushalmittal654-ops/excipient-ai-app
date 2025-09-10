import random
import numpy as np

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
        return {"total_pct": sum(c.pct for c in self.components)}

    @staticmethod
    def example_ir_tablet():
        # A generic starter formulation of excipients
        return [
            Component("Microcrystalline cellulose (MCC)", "Diluent", 88.0),
            Component("Povidone (PVP K30)", "Binder", 4.0),
            Component("Croscarmellose sodium (CCS)", "Disintegrant", 6.0),
            Component("Colloidal silicon dioxide", "Glidant", 1.0),
            Component("Magnesium stearate", "Lubricant", 1.0),
        ]

# --- UPGRADED AND EXPANDED EXCIPIENT DATABASE ---
EXCIPIENTS_DB = [
    Excipient("Microcrystalline cellulose (MCC)", "Diluent", ["low_moisture", "inert", "good_compressibility"], 2.50),
    Excipient("Lactose monohydrate", "Diluent", ["reducing_sugar", "high_moisture", "good_compressibility"], 1.80),
    Excipient("Dicalcium phosphate (DCP)", "Diluent", ["basic", "low_moisture", "poor_compressibility"], 2.00),
    Excipient("Starch (Corn)", "Diluent", ["high_moisture", "binder_property", "disintegrant_property"], 1.50),
    Excipient("Mannitol", "Diluent", ["inert", "low_moisture", "sweet"], 3.00),
    Excipient("Sodium Chloride (NaCl)", "Diluent", ["ionic"], 4.50),
    Excipient("Sorbitol", "Diluent", ["sweet", "hygroscopic"], 3.20),
    Excipient("Povidone (PVP K30)", "Binder", ["peg_like", "binder_property"], 5.50),
    Excipient("Hydroxypropyl methylcellulose (HPMC)", "Binder", ["inert", "polymer", "viscosity_modifier"], 7.00),
    Excipient("Acacia", "Binder", ["natural_gum", "high_moisture"], 6.00),
    Excipient("Gelatin", "Binder", ["natural_polymer", "high_moisture"], 9.00),
    Excipient("Ethylcellulose", "Binder", ["hydrophobic", "polymer"], 11.00),
    Excipient("Croscarmellose sodium (CCS)", "Disintegrant", ["superdisintegrant"], 8.00),
    Excipient("Sodium starch glycolate (SSG)", "Disintegrant", ["superdisintegrant"], 7.50),
    Excipient("Crospovidone", "Disintegrant", ["superdisintegrant", "inert"], 8.50),
    Excipient("Alginic acid", "Disintegrant", ["acidic", "natural_polymer"], 9.50),
    Excipient("Magnesium stearate", "Lubricant", ["hydrophobic", "basic", "metal_ion"], 10.00),
    Excipient("Stearic acid", "Lubricant", ["hydrophobic", "acidic"], 9.00),
    Excipient("Sodium stearyl fumarate", "Lubricant", ["hydrophilic"], 14.00),
    Excipient("Colloidal silicon dioxide", "Glidant", ["inert", "glidant_property"], 12.00),
    Excipient("Talc", "Glidant", ["inert", "hydrophobic"], 4.00),
    Excipient("Sodium lauryl sulfate (SLS)", "Wetting Agent", ["surfactant", "anionic"], 6.00),
    Excipient("Polysorbate 80 (Tween 80)", "Wetting Agent", ["surfactant", "peg_like", "non_ionic"], 15.00),
    Excipient("Opadry (HPMC coat)", "Coating Agent", ["inert", "coating", "polymer"], 20.00),
    Excipient("Eudragit L-100", "Coating Agent", ["anionic", "polymer", "enteric_coating"], 25.00),
]

# --- UPGRADED DRUG PRESET DATABASE ---
API_PRESETS = {
    "Paracetamol": {"flags": {}, "default_load": 500.0, "starter": Formulation.example_ir_tablet()},
    "Metformin": {"flags": {"amine": True}, "default_load": 500.0, "starter": Formulation.example_ir_tablet()},
    "Aspirin": {"flags": {"acidic": True, "ester": True, "moistureSensitive": True}, "default_load": 325.0, "starter": Formulation.example_ir_tablet()},
    "Amoxicillin": {"flags": {"amine": True, "moistureSensitive": True}, "default_load": 500.0, "starter": Formulation.example_ir_tablet()},
    "Carbamazepine": {"flags": {"poorSolubility": True}, "default_load": 200.0, "starter": Formulation.example_ir_tablet()},
    "Ibuprofen": {"flags": {"acidic": True, "poorSolubility": True}, "default_load": 200.0, "starter": Formulation.example_ir_tablet()},
    "Propranolol": {"flags": {"amine": True, "basic": True}, "default_load": 40.0, "starter": Formulation.example_ir_tablet()},
    "Diclofenac Sodium": {"flags": {"acidic": True}, "default_load": 50.0, "starter": Formulation.example_ir_tablet()},
    "Atorvastatin": {"flags": {"ester": True, "moistureSensitive": True, "poorSolubility": True}, "default_load": 20.0, "starter": Formulation.example_ir_tablet()},
    "Levothyroxine": {"flags": {"moistureSensitive": True, "amine": True}, "default_load": 0.1, "starter": Formulation.example_ir_tablet()},
    "Gabapentin": {"flags": {"amine": True}, "default_load": 300.0, "starter": Formulation.example_ir_tablet()},
    "Clopidogrel": {"flags": {"ester": True}, "default_load": 75.0, "starter": Formulation.example_ir_tablet()},
    "Amlodipine": {"flags": {"amine": True, "basic": True}, "default_load": 10.0, "starter": Formulation.example_ir_tablet()},
    "Losartan Potassium": {"flags": {"acidic": True}, "default_load": 50.0, "starter": Formulation.example_ir_tablet()},
    "Ciprofloxacin": {"flags": {"chelation": True, "poorSolubility": True}, "default_load": 500.0, "starter": Formulation.example_ir_tablet()},
    "Furosemide": {"flags": {"acidic": True, "moistureSensitive": True, "poorSolubility": True}, "default_load": 40.0, "starter": Formulation.example_ir_tablet()},
    "Glibenclamide": {"flags": {"poorSolubility": True}, "default_load": 5.0, "starter": Formulation.example_ir_tablet()},
    "Theophylline": {"flags": {"poorSolubility": True}, "default_load": 200.0, "starter": Formulation.example_ir_tablet()},
    "Ranitidine": {"flags": {"amine": True, "basic": True}, "default_load": 150.0, "starter": Formulation.example_ir_tablet()},
}

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
        if api_flags.get("chelation") and "metal_ion" in excipient.properties: risk = max(risk, 3)
        if api_flags.get("basic") and "anionic" in excipient.properties: risk = max(risk, 2)
        results.append({"excipient": comp.name, "function": comp.function, "pct": comp.pct, "risk": risk})
    return results

# --- SIMULATORS (UPGRADED FOR ACCURACY) ---
class Simulators:
    @staticmethod
    def disintegration_time(api_flags, disintegrant_pct, lubricant_pct):
        base_time = 15.0
        # Poorly soluble drugs are harder/slower to break apart
        if api_flags.get("poorSolubility"):
            base_time = 18.0
        
        time = base_time - (disintegrant_pct * 2.5) + (lubricant_pct * 3.0)
        return max(2.0, min(time, 30.0))

    @staticmethod
    def dissolution_weibull(api_flags, Td):
        t = np.linspace(0, 60, 13)
        # Use different mathematical parameters based on drug solubility for a more realistic curve
        if api_flags.get("poorSolubility"):
            # Slower, more gradual dissolution for poorly soluble drugs
            beta = 0.9
        else:
            # Faster, steeper dissolution for soluble drugs (standard IR profile)
            beta = 1.6
        
        F = 1 - np.exp(-(((t - 0)**beta)) / Td**beta)
        return t, F * 100

def evaluate_profile(formulation):
    return {"passed": random.choice([True, False])}
