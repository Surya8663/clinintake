from typing import List
from src.models import GuidelineChunk
from src.logger import logger

# Real published USPSTF clinical guideline recommendation summaries with clause-level metadata
PUBLISHED_USPSTF_GUIDELINES: List[GuidelineChunk] = [
    GuidelineChunk(
        chunk_id="USPSTF-DM-2021-C1",
        text="The USPSTF recommends screening for prediabetes and type 2 diabetes in adults aged 35 to 70 years who have overweight or obesity. Clinicians should offer or refer patients with prediabetes to effective preventive interventions.",
        source="USPSTF",
        version="2021-V1",
        effective_date="2021-08-24",
        section="Diabetes Screening Guidelines",
        clause_id="USPSTF-DM-B"
    ),
    GuidelineChunk(
        chunk_id="USPSTF-CRC-2021-C1",
        text="The USPSTF recommends screening for colorectal cancer in all adults aged 45 to 75 years. Screening strategies include colonoscopy every 10 years, annual FIT, or stool DNA-FIT every 1 to 3 years.",
        source="USPSTF",
        version="2021-V1",
        effective_date="2021-05-18",
        section="Colorectal Cancer Screening Guidelines",
        clause_id="USPSTF-CRC-A"
    ),
    GuidelineChunk(
        chunk_id="USPSTF-HTN-2021-C1",
        text="The USPSTF recommends screening for hypertension in adults aged 18 years or older with office blood pressure measurement. The USPSTF recommends obtaining measurements outside of the clinical setting for diagnostic confirmation before starting treatment.",
        source="USPSTF",
        version="2021-V1",
        effective_date="2021-04-27",
        section="Hypertension Screening Guidelines",
        clause_id="USPSTF-HTN-A"
    ),
    GuidelineChunk(
        chunk_id="USPSTF-BC-2024-C1",
        text="The USPSTF recommends biennial screening mammography for women aged 40 to 74 years to reduce breast cancer mortality.",
        source="USPSTF",
        version="2024-V1",
        effective_date="2024-04-30",
        section="Breast Cancer Screening Guidelines",
        clause_id="USPSTF-BC-B"
    ),
    GuidelineChunk(
        chunk_id="USPSTF-STATIN-2022-C1",
        text="The USPSTF recommends that clinicians prescribe a statin for the primary prevention of CVD in adults aged 40 to 75 years who have 1 or more CVD risk factors and an estimated 10-year CVD event risk of 10% or greater.",
        source="USPSTF",
        version="2022-V1",
        effective_date="2022-08-23",
        section="Statin Use for Primary Prevention of CVD",
        clause_id="USPSTF-CVD-B"
    )
]

def load_and_chunk_guidelines() -> List[GuidelineChunk]:
    """Ingests published USPSTF clinical guideline chunks with clause metadata."""
    logger.info(f"Loaded {len(PUBLISHED_USPSTF_GUIDELINES)} published USPSTF clinical guideline chunks into ingestion pipeline.")
    return PUBLISHED_USPSTF_GUIDELINES
