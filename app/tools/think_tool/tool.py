from langchain_core.tools import tool

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Pause and reflect on research progress before choosing the next action.

    When to use:
    - After each batch of search results arrives, never in parallel with a search.
    - Before writing the final answer, to confirm the evidence is sufficient.

    Cover four points:
    1. Findings: what concrete facts and sources do you have?
    2. Gaps: what specific information is still missing?
    3. Quality: is the evidence strong enough to answer well?
    4. Decision: search again (state the exact query) or stop and answer.

    Stop searching when the answer is supported or new searches return repeated information.

    Args:
        reflection: Analysis of findings so far, remaining gaps, and the next action.

    Returns:
        A short confirmation that the reflection was recorded.
    """
    return f"Reflection recorded: {reflection}"
