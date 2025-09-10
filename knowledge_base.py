"""
This file contains the expert knowledge base for ExcipientAI.
It maps chemical interactions to human-readable explanations.
"""

REACTION_EVIDENCE = {
    "Maillard (Amine-Lactose)": {
        "flags_needed": ["amine"],
        "excipient_properties": ["reducing_sugar"],
        "risk_level": 3,
        "explanation": "High Risk: The primary/secondary amine on the API can undergo a Maillard reaction with reducing sugars like Lactose. This chemical reaction can lead to brownish discoloration and degradation of the drug, impacting its stability and efficacy."
    },
    "Acid-Base (Acidic-Basic)": {
        "flags_needed": ["acidic"],
        "excipient_properties": ["basic"],
        "risk_level": 2,
        "explanation": "Moderate Risk: An acidic API can react with a basic excipient (like Calcium Carbonate). This acid-base interaction can alter the pH microenvironment of the tablet, potentially affecting the drug's dissolution rate and bioavailability."
    },
    "Ester Hydrolysis (Moisture)": {
        "flags_needed": ["ester"],
        "excipient_properties": ["high_moisture"],
        "risk_level": 3,
        "explanation": "High Risk: APIs with ester functional groups (like Aspirin) are susceptible to hydrolysis, a reaction that breaks the ester bond. Excipients with high water content can accelerate this degradation, leading to a loss of potency."
    },
    "Transacylation (PEG)": {
        "flags_needed": ["ester"],
        "excipient_properties": ["peg"],
        "risk_level": 2,
        "explanation": "Moderate Risk: Polyethylene Glycols (PEGs) can cause transacylation reactions with ester-containing drugs. This involves the transfer of an acyl group, leading to the formation of drug-PEG adducts and degradation of the active ingredient."
    }
}