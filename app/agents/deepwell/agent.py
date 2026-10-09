from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END, add_messages
from typing import Annotated, Sequence, Optional, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from app.agents.scope.agent import build as scope_agent
from langgraph.types import interrupt, Command

class AgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)
    research_brief: Optional[str] = None
    report: Optional[str] = None


#todo: replace

async def research_stub(state: AgentState) -> dict:
    # Fake output so you can confirm the brief arrived intact
    return {
        "messages": [AIMessage(content=f"[STUB] Research would run on:\n{state.research_brief}")]
    }

## todo: end
def route_approve_brief(state: AgentState) -> Literal["approve_brief", "__end__"]:
    return "approve_brief" if state.research_brief else END


def approve_brief(state: AgentState) -> Command[Literal["research", "scope"]]:
    decision = interrupt({"type": "approve_brief", "brief": state.research_brief})
    
    if decision.get("approved"):
        return Command(
            goto="research",
            update={"research_brief": decision.get("brief") or state.research_brief}
        )
    
    
    return Command(
        goto="scope",
        update={
            "research_brief": None,
            "messages": [HumanMessage(content=decision.get("feedback", ""))]
        }
    )    

def build(checkpointer, store):
    builder = StateGraph(AgentState)
    builder.add_node("scope", scope_agent())
    builder.add_node("approve_brief", approve_brief)
    builder.add_node("research", research_stub)

    builder.add_edge(START, "scope")
    builder.add_conditional_edges("scope", route_approve_brief)
    builder.add_edge("research", END)
    
    agent = builder.compile(checkpointer=checkpointer, store=store)
    
    return agent


