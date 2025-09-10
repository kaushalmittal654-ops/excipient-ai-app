"""
This file contains the evidence-backed expert knowledge base for ExcipientAI.
It maps chemical interactions to human-readable explanations and scientific sources.
"""

REACTION_EVIDENCE = {
    "Maillard (Amine-Lactose)": {
        "flags_needed": ["amine"],
        "excipient_properties": ["reducing_sugar"],
        "risk_level": 3,
        "explanation": "High Risk: The primary/secondary amine on the API can undergo a Maillard reaction with reducing sugars like Lactose. This leads to brownish discoloration and degradation of the drug.",
        "citation": "Bharate, S. S., et al. (2014). The Maillard reaction in pharmaceutical formulations. Pharmaceutical Research, 31(8), 1996-2015.",
        "source_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4111867/"
    },
    "Ester Hydrolysis (Moisture)": {
        "flags_needed": ["ester", "moistureSensitive"],
        "excipient_properties": ["high_moisture"],
        "risk_level": 3,
        "explanation": "High Risk: APIs with ester functional groups (e.g., Aspirin) are susceptible to hydrolysis. Excipients with high water content can accelerate this degradation, leading to a loss of potency.",
        "citation": "Waterman, K. C., & Adami, R. C. (2005). Accelerated aging: Prediction of chemical stability of pharmaceuticals. International Journal of Pharmaceutics, 293(1-2), 101-125.",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/15752822/"
    },
    "Metal Ion Chelation": {
        "flags_needed": ["chelation"],
        "excipient_properties": ["metal_ion"],
        "risk_level": 3,
        "explanation": "High Risk: Drugs like Ciprofloxacin can form insoluble complexes (chelates) with di- and trivalent metal ions (e.g., Mg2+ in Magnesium Stearate). This can significantly reduce drug dissolution and bioavailability.",
        "citation": "Stauffer, J. Q., & Hikal, A. H. (1990). In vitro inactivation of ciprofloxacin by antacids and minerals. DICP, 24(10), 963-965.",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/2275039/"
    },
    "Acid-Base Reaction": {
        "flags_needed": ["acidic"],
        "excipient_properties": ["basic"],
        "risk_level": 2,
        "explanation": "Moderate Risk: An acidic API can react with a basic excipient. This can alter the tablet's pH microenvironment, potentially affecting drug dissolution rate and bioavailability.",
        "citation": "Handbook of Pharmaceutical Excipients, 6th Ed. (2009). Rowe, R. C., Sheskey, P. J., & Quinn, M. E. (Eds.). Pharmaceutical Press.",
        "source_url": "https://www.pharmpress.com/product/9780857110275/handbook-of-pharmaceutical-excipients"
    },
    "Ionic Interaction (Basic Drug-Anionic Excipient)": {
        "flags_needed": ["basic"],
        "excipient_properties": ["anionic"],
        "risk_level": 2,
        "explanation": "Moderate Risk: Basic (cationic) drugs can interact with anionic excipients like Sodium Lauryl Sulfate or Eudragit. This can form a less soluble salt, leading to slower drug release.",
        "citation": "F M, Al-Gohary O M N. (2007). Effect of some anionic additives on the release of a cationic drug from an inert matrix. Asian Journal of Pharmaceutical Sciences.",
        "source_url": "https://www.researchgate.net/publication/288052161_Effect_of_some_anionic_additives_on_the_release_of_a_cationic_drug_from_an_inert_matrix"
    }
}
