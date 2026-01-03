# src/graph.py
from langgraph.graph import StateGraph, END
from src.state import GraphState
from src.nodes import (
    analyze_diff,
    retrieve_guidelines,
    reviewer_agent,
    tool_executor,  # New Node
    senior_filter_agent,
    publisher_node
)

def should_continue(state: GraphState):
    """
    Conditional Logic: Check if the reviewer requested a tool.
    """
    last_message = state["initial_critique"]
    
    # If it's an AIMessage with tool_calls, we go to tool execution
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
    
    # Otherwise, we go to the next stage
    return "pass"

def build_graph():
    workflow = StateGraph(GraphState)

    # Add Nodes
    workflow.add_node("analyze", analyze_diff)
    workflow.add_node("retrieve", retrieve_guidelines)
    workflow.add_node("review", reviewer_agent)
    workflow.add_node("tools", tool_executor)  # New Node
    workflow.add_node("filter", senior_filter_agent)
    workflow.add_node("publish", publisher_node)

    # Edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "retrieve")
    workflow.add_edge("retrieve", "review")

    # Conditional Edge from Reviewer
    workflow.add_conditional_edges(
        "review",
        should_continue,
        {
            "tools": "tools",  # If tool called -> execute it
            "pass": "filter"   # If done -> filter and publish
        }
    )

    # IMPORTANT: The tool executor must go BACK to the reviewer
    workflow.add_edge("tools", "review")
    
    workflow.add_edge("filter", "publish")
    workflow.add_edge("publish", END)

    return workflow.compile()