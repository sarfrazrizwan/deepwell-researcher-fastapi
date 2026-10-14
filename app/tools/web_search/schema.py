from pydantic import BaseModel, Field

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
