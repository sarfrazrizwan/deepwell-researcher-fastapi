from langchain_core.tools import tool, InjectedToolArg
from typing import Annotated
from app.tools.web_search.schema import SearchResult


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
