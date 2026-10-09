from typing import Annotated
from fastapi import Depends, Request
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from app.agents.registry import AgentName


def agent_dep(name: AgentName):
    def _get(request: Request) -> CompiledStateGraph:
        return request.app.state.agents[name]
    return _get


def get_store(request: Request) -> BaseStore:
    return request.app.state.store


get_deepwell_agent = agent_dep(AgentName.DEEPWELL)

DeepwellAgent = Annotated[CompiledStateGraph, Depends(get_deepwell_agent)]
Store = Annotated[BaseStore, Depends(get_store)]
