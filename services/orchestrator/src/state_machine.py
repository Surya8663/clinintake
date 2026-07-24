from transitions import Machine, MachineError
from src.logger import logger

class DocumentWorkflow:
    def __init__(self, document_id: str, state: str = "received", context: dict = None):
        self.document_id = document_id
        self.state = state
        self.context = context or {}

class WorkflowMachine:
    STATES = [
        "received",
        "sanitizing",
        "extracting",
        "validating",
        "reasoning",
        "awaiting_approval",
        "writing_ehr",
        "complete",
        "escalated",
        "rejected",
    ]
    
    TRANSITIONS = [
        {"trigger": "start_sanitize", "source": "received", "dest": "sanitizing"},
        {"trigger": "sanitize_success", "source": "sanitizing", "dest": "extracting"},
        {"trigger": "sanitize_fail", "source": "sanitizing", "dest": "rejected"},
        
        {"trigger": "extraction_success", "source": "extracting", "dest": "validating"},
        {"trigger": "extraction_fail", "source": "extracting", "dest": "escalated"},
        
        {"trigger": "validation_success", "source": "validating", "dest": "reasoning"},
        {"trigger": "validation_needs_review", "source": "validating", "dest": "awaiting_approval"},
        {"trigger": "validation_fail", "source": "validating", "dest": "rejected"},
        
        {"trigger": "reasoning_success", "source": "reasoning", "dest": "writing_ehr"},
        {"trigger": "reasoning_needs_review", "source": "reasoning", "dest": "awaiting_approval"},
        {"trigger": "reasoning_fail", "source": "reasoning", "dest": "escalated"},
        
        {"trigger": "approve", "source": "awaiting_approval", "dest": "writing_ehr"},
        {"trigger": "reject", "source": "awaiting_approval", "dest": "rejected"},
        
        {"trigger": "write_ehr_success", "source": "writing_ehr", "dest": "complete"},
        {"trigger": "write_ehr_fail", "source": "writing_ehr", "dest": "escalated"},
        
        # Global safety/operational escapes
        {"trigger": "force_escalate", "source": "*", "dest": "escalated"},
        {"trigger": "force_reject", "source": "*", "dest": "rejected"},
    ]

    @classmethod
    def get_machine(cls, model: DocumentWorkflow) -> Machine:
        # We specify send_event=True so callback functions receive the EventData object
        return Machine(
            model=model,
            states=cls.STATES,
            transitions=cls.TRANSITIONS,
            initial=model.state,
            send_event=True,
            auto_transitions=False
        )

def transition_workflow(model: DocumentWorkflow, trigger: str, *args, **kwargs) -> DocumentWorkflow:
    """
    Attempts to trigger a transition on the document workflow model.
    Raises MachineError if transition is illegal.
    """
    machine = WorkflowMachine.get_machine(model)
    logger.info(
        f"Attempting transition: {trigger}",
        extra={
            "document_id": model.document_id,
            "current_state": model.state,
            "trigger": trigger
        }
    )
    
    # Executing the trigger (e.g., model.trigger_name())
    try:
        trigger_func = getattr(model, trigger)
        trigger_func(*args, **kwargs)
    except MachineError as e:
        logger.error(
            f"Invalid transition attempted: {trigger}",
            extra={
                "document_id": model.document_id,
                "current_state": model.state,
                "trigger": trigger,
                "error": str(e)
            }
        )
        raise e
        
    logger.info(
        f"Transition successful: {trigger}",
        extra={
            "document_id": model.document_id,
            "new_state": model.state,
            "trigger": trigger
        }
    )
    return model
