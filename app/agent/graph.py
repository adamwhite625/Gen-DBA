"""LangGraph workflow definition for the Gen-DBA agent pipeline."""
import uuid
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState, AgentPhase
from app.agent.nodes.perception import perception_node
from app.agent.nodes.reasoning import reasoning_node
from app.agent.nodes.validation import validation_node
from app.agent.nodes.action import action_node
from app.agent.nodes.evaluation import evaluation_node

def _should_continue_after_perception(state: AgentState) -> str:
    """Route after perception: if failed, end; otherwise reason."""
    if state.phase == AgentPhase.FAILED:
        return END
    return "reasoning"

def _should_continue_after_reasoning(state: AgentState) -> str:
    """Route after reasoning: if failed, end; otherwise validate."""
    if state.phase == AgentPhase.FAILED:
        return END
    return "validation"

def _should_continue_after_action(state: AgentState) -> str:
    """Route after action: if failed, end; otherwise evaluate."""
    if state.phase == AgentPhase.FAILED or state.phase == AgentPhase.COMPLETED:
        return END
    return "evaluation"

def build_agent_graph() -> StateGraph:
    """Construct the LangGraph state machine for the database agent."""
    workflow = StateGraph(AgentState)

    workflow.add_node("perception", perception_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("action", action_node)
    workflow.add_node("evaluation", evaluation_node)

    workflow.set_entry_point("perception")

    workflow.add_conditional_edges("perception", _should_continue_after_perception)
    workflow.add_conditional_edges("reasoning", _should_continue_after_reasoning)
    
    # After validation, the pipeline pauses for human approval.
    # We exit the graph here. The action node is triggered via a separate API call later.
    workflow.add_edge("validation", END)

    # Secondary execution flow (Action -> Evaluation)
    workflow.add_conditional_edges("action", _should_continue_after_action)
    workflow.add_edge("evaluation", END)

    return workflow.compile()

# Global instance of the compiled graph
agent_graph = build_agent_graph()

def create_new_run() -> AgentState:
    """Initialize a new agent state with a unique run ID."""
    return AgentState(run_id=str(uuid.uuid4()))
