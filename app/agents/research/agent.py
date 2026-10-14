from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, HumanMessage, filter_messages, AIMessage
from typing import Literal, Sequence, Annotated, List
from operator import add
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from tavily import AsyncTavilyClient
from app.utils.utils import get_today_date_str
from app.agents.research.prompts import RESEARCHER_SYSTEM_PROMPT, COMPRESS_RESEARCH_SYS_PROMPT, COMPRESS_RESEARCH_HUMAN_PROMPT
from app.tools.web_search.tool import web_search
from app.tools.think_tool.tool import think_tool

model = init_chat_model("openai:gpt-6-luna")
compress_research_model = init_chat_model("openai:gpt-6-luna")
tavily = AsyncTavilyClient()
 
class AgentState(BaseModel):
    research_brief: str
    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]
    compressed_research: str | None = None
    raw_notes: Annotated[List[str], add] = Field(default_factory=list)
    tool_iteration_count: int = 0
    web_search_count: int = 0
    think_tool_count: int = 0

class AgentInputState(BaseMessage):
    research_brief: str



class CompressedResearch(BaseModel):
    compressed_research: str = Field(description="It give comprehensive research without losing any of details but in organize format")
    
    
tools = [web_search, think_tool]
tools_by_name = {t.name: t for t in tools}    
    
model_with_tools = model.bind_tools(tools)   

async def llm_call(state: AgentState):
    response = await model_with_tools.ainvoke(
        [SystemMessage(content=RESEARCHER_SYSTEM_PROMPT.format(
            date=get_today_date_str()))
        ]
        + [HumanMessage(content=state.research_brief)]
        + state.researcher_messages
    )
    
    return {"researcher_messages": [response]}


async def tool_node(state: AgentState):
    
    tool_calls = state.researcher_messages[-1].tool_calls
    observation = []
    
    web_search_count = state.web_search_count
    tool_iteration = state.tool_iteration_count
    think_tool = state.think_tool_count
    
    for tool_call in tool_calls:
        tool_iteration += 1
        if tool_call['name'] == 'web_search':
            web_search_count += 1
        elif tool_call['name'] == 'think_tool':
             think_tool += 1    
            
        tool = tools_by_name.get(tool_call['name'])
        tool_output = await tool.ainvoke(tool_call["args"])
        observation.append(ToolMessage(
            content=tool_output,
            name=tool_call['name'],
            tool_call_id=tool_call['id']
        ))
    
    print("web_search_count: ", web_search_count)
    print("tool_iteration: ", tool_iteration)
    print("think_tool: ", think_tool)
    
    return {
        "researcher_messages": observation,
        "web_search_count": web_search_count,
        "tool_iteration_count": tool_iteration,
        "think_tool_count": think_tool,
        }

async def should_continue(state: AgentState) -> Literal["tool_node", "compress_research"]:
    
    if state.researcher_messages[-1].tool_calls:
        return "tool_node"
    
    return "compress_research"
    
async def compress_research(state: AgentState) -> dict:
    """"""
    response = await compress_research_model.with_structured_output(CompressedResearch).ainvoke(
        [SystemMessage(content=COMPRESS_RESEARCH_SYS_PROMPT.format(date=get_today_date_str()))] + 
         state.researcher_messages + 
         [HumanMessage(content=COMPRESS_RESEARCH_HUMAN_PROMPT)]
        )
    
    raw_notes = [
        str(message.content) for message in filter_messages(
            messages=state.researcher_messages, 
            include_types=["tool", 'ai']
            )
        ]
    
    return {
        "compressed_research": response.compressed_research,
        "raw_notes" :[ "\n".join(raw_notes)]
    }
    
def build():
    
    builder = StateGraph(AgentState, input_schema=AgentInputState)
    builder.add_node("llm_call", llm_call)
    builder.add_node("compress_research", compress_research)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "llm_call")
    builder.add_conditional_edges("llm_call", should_continue)
    builder.add_edge("tool_node", "llm_call")
    builder.add_edge("compress_research", END)

    return builder.compile()
