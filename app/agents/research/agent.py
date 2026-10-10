from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, HumanMessage, filter_messages
from typing import Literal, Sequence, Annotated, List
from operator import add
from langchain.chat_models import init_chat_model
from langchain.tools import tool, InjectedToolArg
from tavily import AsyncTavilyClient
from app.utils.utils import get_today_date_str
from app.agents.research.prompts import RESEARCHER_SYSTEM_PROMPT, SUMMARIZE_CONTENT_PROMPT, COMPRESS_RESEARCH_SYS_PROMPT, COMPRESS_RESEARCH_HUMAN_PROMPT

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

class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float
    raw_content: str | None = None
    id: str

class ContentSummary(BaseModel):
    summary: str = Field(description="Concise summary of content details")
    key_expert: str = Field(description="Important notes from the content")

class CompressedResearch(BaseModel):
    compressed_research: str = Field(description="It give comprehensive research without losing any of details but in organize format")
    
def filter_unique_searches(searches: list[SearchResult]) -> list[SearchResult]:
    
    unique: dict[str, SearchResult] = {}
    for search in searches:
        unique[search['url']] = search
    
    return list(unique.values())

async def summarize_search_results(search: SearchResult) -> str:
  
    summarizer = await model.with_structured_output(ContentSummary).ainvoke([
        HumanMessage(
            content=SUMMARIZE_CONTENT_PROMPT.format(
                date=get_today_date_str(),
                query=search["title"], 
                content=search["raw_content"]
            ))
    ])
    
    return (
        f"<summary>{summarizer.summary}</summary>\n\n"
        f"<key_experts>{summarizer.key_expert}</key_experts>"
        )

async def process_search_results(searches: list[SearchResult]) -> dict:
    
    contents = {}
    for search in searches:
        print(search)
        if not search.get("raw_content"):
            content = search.get("content")
        else:
            content = await summarize_search_results(search=search)
        
        contents[search['url']] = {
            "title": search["title"],
            "content": content
        }
    
    return contents    


def format_search_results(items: dict) -> str:

    formatted_str: str = ""
    for i, (url, item ) in enumerate(items.items(), 1):
        formatted_str += f"{i}. SOURCE: {url} \n"
        formatted_str += f"TITLE: {item["title"]} \n"
        formatted_str += f"CONTENT: {item["content"]} \n"
        formatted_str += "=" * 80 + "\n\n"
    
    return formatted_str 

@tool(parse_docstring=True)
async def web_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 3,
    include_raw_content: Annotated[int, InjectedToolArg] = True
):
    """Fetch results from Tavily search API with content summarization.

    Args:
        query: A single search query to execute
        max_results: Maximum number of results to return

    Returns:
        Formatted string of search results with summaries
    """
    
    response: list[SearchResult] = await tavily.search(
        query=query, 
        max_results=max_results, 
        include_raw_content=include_raw_content
    )
    
    results = response["results"]
    unique_results: list[SearchResult] = filter_unique_searches(results)
    processed_results = await process_search_results(unique_results)
    
    return format_search_results(processed_results)


@tool
def think_tool(reflection: Annotated[str, "Your detailed reflection on findings, gaps, and next steps."]) -> str:
    """Tool for strategic reflection on research progress and decision-making.
    
    
    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.
    
    
    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?
    
    
    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?
    
    
    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps
    
            
    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"
    
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
