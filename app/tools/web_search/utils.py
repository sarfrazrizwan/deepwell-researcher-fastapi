from app.tools.web_search.schema import SearchResult, ContentSummary
from langchain_core.messages import HumanMessage
from app.tools.web_search.prompts import SUMMARIZE_CONTENT_PROMPT
from app.utils.utils import get_today_date_str
from langchain.chat_models import init_chat_model


model = init_chat_model("openai:gpt-6-luna")

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
