from langchain_core.messages import BaseMessage, get_buffer_string, HumanMessage
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

TITLE_GENERATION_PROMPT="""
You generate short titles for chat conversations.

Read the messages below and write one title that names the main topic or task.

Rules:
- 3 to 6 words.
- Use Title Case.
- Name the specific subject, not the activity. Prefer "Laravel Queue Retry Logic" over "Help With Code".
- Use the user's own key terms (library names, product names, error codes) when present.
- If the conversation covers several topics, title the one the user spent the most messages on.
- Write in the same language the user writes in.
- No quotes, no ending punctuation, no emojis.
- Never start with "Chat about", "Discussion of", "Question about", or "Help with".
- If the messages are only a greeting or have no clear topic, return: New Conversation

Return only the title text, nothing else.

<messages>
{messages}
</messages>
"""

class MessageTitle(BaseModel):
    title: str = Field("Chat title")

async def generate_title(messages: list[BaseMessage]) -> str:
    
    model = init_chat_model("openai:gpt-4.1-nano").with_structured_output(MessageTitle)
    response = await model.ainvoke([HumanMessage(content=TITLE_GENERATION_PROMPT.format(messages=get_buffer_string(messages=messages)))])
    
    return response.title
    