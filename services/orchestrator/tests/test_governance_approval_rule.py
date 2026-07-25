import pytest
from src.state_machine import DocumentWorkflow, transition_workflow, UnapprovedEHRWriteError

def test_governance_rule_blocks_unapproved_ehr_write():
    """
    CRITICAL PRD 5.7 GOVERNANCE RULE TEST:
    Proves that the Orchestrator is structurally PREVENTED from transitioning to writing_ehr
    or executing FHIR transactions until it receives a genuine Signed Approval event.
    """
    # 1. Initialize workflow in awaiting_approval state
    doc = DocumentWorkflow(
        document_id="DOC-GOVERNANCE-001",
        state="awaiting_approval",
        context={"signed_approval": False} # Unapproved!
    )

    # 2. Attempt to trigger approval / EHR write without signed approval flag
    with pytest.raises(UnapprovedEHRWriteError) as exc_info:
        transition_workflow(doc, "approve")

    assert "Governance Violation: Cannot transition to writing_ehr without genuine Signed Approval event" in str(exc_info.value)
    assert doc.state == "awaiting_approval" # Workflow state remains unchanged

def test_governance_rule_allows_ehr_write_when_signed_approval_present():
    """Verifies that transition to writing_ehr succeeds when genuine signed_approval is present."""
    doc = DocumentWorkflow(
        document_id="DOC-GOVERNANCE-002",
        state="awaiting_approval",
        context={"signed_approval": True, "clinician_id": "DR-SURYA-MD"}
    )

    updated_doc = transition_workflow(doc, "approve")
    assert updated_doc.state == "writing_ehr"
