from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, get_buffer_string
from langchain.chat_models import init_chat_model
from langgraph.graph import add_messages
from typing import Annotated, Optional, Sequence, Literal
from langgraph.graph import StateGraph, START, END
from app.agents.scope.schema import ClarifyWithUser, ResearchBriefWriter
from app.agents.scope.prompts import SCOPING_PROMPT, BRIEF_WRITER_PROMPT
from app.utils.utils import get_today_date_str
from app.config import settings as config
from langgraph.types import Command

model = init_chat_model("openai:gpt-6-luna", temperature=0.0, api_key=config.openai_api_key)

class AgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    research_brief: Optional[str] = None
    
    

async def clarify_with_user(state: AgentState) -> Command[Literal["write_research_brief", "__end__"]]:
    
    chat_model = model.with_structured_output(ClarifyWithUser)
    messages = get_buffer_string(state.messages)
    prompt = SCOPING_PROMPT.format(messages=messages, date=get_today_date_str())
    
    response = await chat_model.ainvoke([HumanMessage(content=prompt)])
    
    if response.need_clarification:
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=response.question)]}
        )
    
    return Command(
        goto="write_research_brief",
        update={"messages": [AIMessage(content=response.verification)]}
    )


async def write_research_brief(state: AgentState) -> dict:
    
    chat_model = model.with_structured_output(ResearchBriefWriter)
    messages = get_buffer_string(state.messages)
    
    response = await chat_model.ainvoke([HumanMessage(content=BRIEF_WRITER_PROMPT.format(
        messages=messages,
        date=get_today_date_str()
    ))])
    
    
    return { "research_brief": response.research_brief }
    
    
def build():
    
    builder = StateGraph(AgentState)
    builder.add_node("clarify_with_user", clarify_with_user)    
    builder.add_node("write_research_brief", write_research_brief)

    builder.add_edge(START, "clarify_with_user")
    builder.add_edge("write_research_brief", END)

    agent = builder.compile()
    return agent

    

