import httpx

from src.config import settings
from src.logger import logger
from src.models import AllergyItem, DrugInteraction, DrugItem, InteractionCheckResponse

# Deterministic drug interaction database fallback index for offline execution
KNOWN_DRUG_INTERACTIONS = [
    ("lisinopril", "potassium", "high", "Risk of severe hyperkalemia when ACE inhibitors are combined with potassium supplements.", "drug-drug"),
    ("lisinopril", "spironolactone", "high", "Concomitant use of ACE inhibitors and potassium-sparing diuretics increases hyperkalemia risk.", "drug-drug"),
    ("warfarin", "aspirin", "high", "Increased risk of major gastrointestinal and systemic bleeding.", "drug-drug"),
    ("metformin", "contrast", "moderate", "Risk of renal impairment and severe lactic acidosis during iodinated radiocontrast procedures.", "drug-drug"),
]

KNOWN_DRUG_ALLERGIES = [
    ("penicillin", "amoxicillin", "high", "Cross-reactivity: Amoxicillin is a beta-lactam penicillin derivative.", "drug-allergy"),
    ("penicillin", "ampicillin", "high", "Cross-reactivity: Ampicillin is a beta-lactam penicillin derivative.", "drug-allergy"),
    ("ace inhibitors", "lisinopril", "high", "Lisinopril is an ACE inhibitor; contraindicated due to reported history of ACE-inhibitor allergy / angioedema.", "drug-allergy"),
    ("sulfa", "sulfamethoxazole", "high", "Sulfamethoxazole contains a sulfonamide moiety causing severe allergic reaction.", "drug-allergy"),
]


async def check_rxnav_api_interactions(rxcuis: list[str]) -> list[DrugInteraction]:
    """Queries NLM RxNav Interaction API for drug-drug interactions using real RxCUI codes."""
    if len(rxcuis) < 2:
        return []

    rx_str = "+".join(rxcuis)
    url = f"{settings.rxnav_interaction_api_url}/list.json?rxcuis={rx_str}"
    interactions: list[DrugInteraction] = []

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                full_group = data.get("fullInteractionTypeGroup", [])
                for group in full_group:
                    for interaction_type in group.get("fullInteractionType", []):
                        pair = interaction_type.get("minConcept", [])
                        item1 = pair[0].get("name", "Drug A") if len(pair) > 0 else "Drug A"
                        item2 = pair[1].get("name", "Drug B") if len(pair) > 1 else "Drug B"

                        for pair_detail in interaction_type.get("interactionPair", []):
                            description = pair_detail.get("description", "Drug-drug interaction reported.")
                            severity_raw = pair_detail.get("severity", "high").lower()
                            severity = "high" if "high" in severity_raw or "severe" in severity_raw else "moderate"

                            interactions.append(
                                DrugInteraction(
                                    interaction_type="drug-drug", source_item=item1, target_item=item2, severity=severity, evidence=description, source_database="NLM_RxNav_Interaction_API"
                                )
                            )
    except Exception as e:
        logger.warning(f"NLM RxNav Interaction API request failed or timed out: {e}")

    return interactions


async def check_all_interactions(medications: list[DrugItem], allergies: list[AllergyItem]) -> InteractionCheckResponse:
    """Checks drug-drug and drug-allergy interactions deterministically using API and clinical database."""
    interactions: list[DrugInteraction] = []

    # 1. Collect RxCUIs and try live NLM RxNav API
    rxcuis = [m.rxnorm_code for m in medications if m.rxnorm_code and m.rxnorm_code != "000000"]
    api_results = await check_rxnav_api_interactions(rxcuis)
    interactions.extend(api_results)

    # 2. Check Drug-Drug interactions against deterministic clinical index
    med_names = [m.name.lower() for m in medications]
    for i in range(len(med_names)):
        for j in range(i + 1, len(med_names)):
            d1, d2 = med_names[i], med_names[j]
            for known_d1, known_d2, sev, evidence, itype in KNOWN_DRUG_INTERACTIONS:
                if (known_d1 in d1 and known_d2 in d2) or (known_d2 in d1 and known_d1 in d2):
                    # Avoid duplicate if already reported by API
                    if not any(known_d1 in inter.source_item.lower() and known_d2 in inter.target_item.lower() for inter in interactions):
                        interactions.append(
                            DrugInteraction(
                                interaction_type=itype, source_item=medications[i].name, target_item=medications[j].name, severity=sev, evidence=evidence, source_database="Clinical_Rx_Database"
                            )
                        )

    # 3. Check Drug-Allergy interactions
    for allergy in allergies:
        alg_sub = allergy.substance.lower()
        for med in medications:
            med_name = med.name.lower()
            for known_alg, known_med, sev, evidence, itype in KNOWN_DRUG_ALLERGIES:
                if (known_alg in alg_sub and known_med in med_name) or (known_alg in med_name and known_med in alg_sub):
                    interactions.append(
                        DrugInteraction(
                            interaction_type="drug-allergy", source_item=allergy.substance, target_item=med.name, severity=sev, evidence=evidence, source_database="Clinical_Allergy_Database"
                        )
                    )

    has_interactions = len(interactions) > 0
    has_high = any(i.severity == "high" for i in interactions)

    # Post-process plain-language explanation (used ONLY after deterministic decision is made)
    if not has_interactions:
        explanation = "No significant drug-drug or drug-allergy interactions detected among the evaluated medications."
    else:
        details = "; ".join([f"[{i.severity.upper()}] {i.interaction_type}: {i.source_item} & {i.target_item} ({i.evidence})" for i in interactions])
        explanation = f"Evaluated {len(medications)} medications and {len(allergies)} allergies. Found {len(interactions)} interaction(s): {details}"

    logger.info(f"Interaction check complete: total={len(interactions)}, high_severity={has_high}")

    return InteractionCheckResponse(has_interactions=has_interactions, has_high_severity=has_high, interactions=interactions, plain_language_explanation=explanation)
