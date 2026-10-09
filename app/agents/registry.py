from app.agents.deepwell.agent import build as deepwell_agent
from langgraph.graph.state import CompiledStateGraph
from enum import StrEnum

class AgentName(StrEnum):
    DEEPWELL = "deepwell"

AGENT_BUILDERS = {
    AgentName.DEEPWELL: deepwell_agent
}


def build_agents(checkpointer, store) -> dict[AgentName, CompiledStateGraph]:
    return {name: build(checkpointer, store) for name, build in AGENT_BUILDERS.items()}
