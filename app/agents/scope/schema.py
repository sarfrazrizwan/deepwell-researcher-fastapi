from pydantic import BaseModel, Field

class ClarifyWithUser(BaseModel):
    need_clarification: bool =  Field(description="if it needs more information to prepare the research brief then need_clarification would be True otherwise False")
    question: str = Field(description="When there is more information required from user, write a question for user to get more detail")
    verification: str = Field("When sufficient information gathered to prepare the brief then simply acknowledge sufficient information gathered to prepare research brief.")  
    
class ResearchBriefWriter(BaseModel):
    research_brief: str = Field("Research brief for research writer to write a report")    
