from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END, add_messages
from typing import Annotated, Sequence, Optional, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.agents.scope.agent import build as scope_agent
from app.agents.research.agent import build as research_agent
from langgraph.types import interrupt, Command
from langchain.chat_models import init_chat_model
from app.agents.deepwell.prompts import APPROVE_BRIEF_CLASSIFICATION_PROMPT, APPROVE_BRIEF_CLASSIFICATION_SYS_PROMPT

class AgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)
    research_brief: Optional[str] = None
    compressed_research: Optional[str] = None
    raw_notes: Optional[str] = None


classifier = init_chat_model(model="openai:gpt-5.4-nano")

class ApproveClassifier(BaseModel):
    approved: bool = Field(description="If user is agree with generated brief approved would be True otherwise False")
    feedback: bool = Field(description="Write feedback to user as per the user reply.")

def route_approve_brief(state: AgentState) -> Literal["approve_brief", "__end__"]:
    return "approve_brief" if state.research_brief else END


def approve_brief(state: AgentState) -> Command[Literal["research", "scope"]]:
    user_reply = interrupt({"type": "approve_brief", "brief": state.research_brief})
    
    decision = classifier.with_structured_output(ApproveClassifier).ainvoke(
        [SystemMessage(content=APPROVE_BRIEF_CLASSIFICATION_SYS_PROMPT)],
        [HumanMessage(content=APPROVE_BRIEF_CLASSIFICATION_PROMPT.format(brief=state.research_brief, user_reply=user_reply))]
    )
    
    if decision.approved:
        return Command(
            goto="research",
            update={"research_brief": state.research_brief}
        )
    
    
    return Command(
        goto="scope",
        update={
            "research_brief": None,
            "messages": [HumanMessage(content=user_reply)]
        }
    )    

def build(checkpointer, store):
    builder = StateGraph(AgentState)
    builder.add_node("scope", scope_agent())
    builder.add_node("approve_brief", approve_brief)
    builder.add_node("research", research_agent())

    builder.add_edge(START, "scope")
    builder.add_conditional_edges("scope", route_approve_brief)
    builder.add_edge("research", END)
    
    agent = builder.compile(checkpointer=checkpointer, store=store)
    
    return agent


