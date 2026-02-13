"""Base agent class providing shared LangGraph patterns for all specialized agents."""
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Annotated, TypedDict
from operator import add

import chess
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from .llm_provider import LLMProvider


class AgentState(TypedDict):
    """Shared state schema used by all agents."""
    messages: Annotated[List[BaseMessage], add]
    query: str
    board_state: str          # FEN string
    move_history: List[str]
    context: Dict             # Agent-specific context (search results, analysis, etc.)
    agent_name: str           # Which agent is handling this
    final_answer: Optional[str]


class BaseAgent(ABC):
    """Abstract base for all chess agents.

    Subclasses must implement:
    - name (property): unique agent identifier
    - system_prompt (property): agent persona and capabilities
    - gather_context(): domain-specific context gathering
    - _build_prompt(): construct user prompt from state + context
    """

    def __init__(self, model: str = None, provider: str = None, temperature: float = 0.7):
        model = model or os.getenv("MODEL", "grok-4-fast-reasoning")
        provider = provider or os.getenv("MODEL_PROVIDER", "xai")
        self.llm = LLMProvider.get_model(model, provider, temperature=temperature)
        self.graph = self._build_graph()

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier used for routing."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining this agent's persona and capabilities."""
        ...

    @abstractmethod
    async def gather_context(self, state: AgentState) -> Dict:
        """Agent-specific context gathering (DB queries, engine analysis, etc.).

        Must return a dict with at least a 'context' key containing
        the gathered information.
        """
        ...

    @abstractmethod
    def _build_prompt(self, state: AgentState) -> str:
        """Construct the user-facing prompt from state + context."""
        ...

    async def generate_response(self, state: AgentState) -> Dict:
        """Shared LLM response generation using context + system prompt."""
        prompt = self._build_prompt(state)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)
        return {
            "final_answer": answer,
            "messages": [AIMessage(content=answer)],
        }

    def _build_graph(self) -> StateGraph:
        """Standard 2-node graph: gather_context -> generate_response -> END."""
        builder = StateGraph(AgentState)
        builder.add_node("gather_context", self.gather_context)
        builder.add_node("generate_response", self.generate_response)
        builder.set_entry_point("gather_context")
        builder.add_edge("gather_context", "generate_response")
        builder.add_edge("generate_response", END)
        return builder.compile()

    async def query(
        self,
        question: str,
        board_state: str = None,
        move_history: List[str] = None,
    ) -> str:
        """Public interface called by the router or TUI."""
        initial_state = AgentState(
            messages=[],
            query=question,
            board_state=board_state or chess.Board().fen(),
            move_history=move_history or [],
            context={},
            agent_name=self.name,
            final_answer=None,
        )
        result = await self.graph.ainvoke(initial_state)
        return result.get("final_answer", "No response generated")
