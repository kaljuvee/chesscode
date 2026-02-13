"""Router agent that classifies user queries and dispatches to specialized agents."""
import os
from typing import Dict, List, Optional

import chess
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from .base_agent import AgentState, BaseAgent
from .llm_provider import LLMProvider


CLASSIFICATION_PROMPT = """You are a chess assistant router. Classify the user's query into exactly one category.

Categories:
- "general": General chess questions, database searches, game lookups, historical facts, strategy discussion
- "children_coach": Teaching chess to children or beginners, simple explanations, learning exercises, basic rules
- "opening_teacher": Questions about specific openings, variations, opening theory, ECO codes, opening preparation
- "player_analyst": Analyzing a specific player's games, error patterns, centipawn loss, blunder statistics, PGN-Spy style
- "personal_teacher": Assessing player strength, improvement advice, personalized exercises, study recommendations, "what should I work on"
- "engine": Position evaluation, best move calculation, engine lines, depth analysis, "what is the best move"

User query: {query}
Board context: {board_context}

Respond with ONLY the category name, nothing else."""


class Router:
    """Classifies queries and dispatches to the appropriate specialized agent."""

    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        model = os.getenv("MODEL", "grok-4-fast-reasoning")
        provider = os.getenv("MODEL_PROVIDER", "xai")
        self.classifier_llm = LLMProvider.get_model(model, provider, temperature=0.0)
        self.last_agent_name: str = "general"
        self._forced_agent: Optional[str] = None
        self.graph = self._build_router_graph()

    def force_agent(self, agent_name: str) -> bool:
        """Force the router to use a specific agent for the next query.

        Returns True if the agent name is valid, False otherwise.
        """
        if agent_name in self.agents:
            self._forced_agent = agent_name
            return True
        return False

    def clear_forced_agent(self):
        """Clear the forced agent selection."""
        self._forced_agent = None

    async def classify(self, state: AgentState) -> Dict:
        """Use LLM to classify the query into an agent category."""
        # Check for forced agent
        if self._forced_agent:
            agent_name = self._forced_agent
            self._forced_agent = None  # One-shot: clear after use
            self.last_agent_name = agent_name
            return {"agent_name": agent_name}

        board_context = "starting position"
        fen = state.get("board_state", "")
        if fen:
            try:
                board = chess.Board(fen)
                if board.fullmove_number > 1:
                    board_context = f"move {board.fullmove_number}, {'White' if board.turn else 'Black'} to play"
            except Exception:
                pass

        prompt = CLASSIFICATION_PROMPT.format(
            query=state["query"],
            board_context=board_context,
        )
        response = self.classifier_llm.invoke([HumanMessage(content=prompt)])
        agent_name = response.content.strip().lower().replace('"', "").replace("'", "")

        # Validate and fallback
        if agent_name not in self.agents:
            agent_name = "general"

        self.last_agent_name = agent_name
        return {"agent_name": agent_name}

    def route(self, state: AgentState) -> str:
        """Return the node name to route to based on classified agent_name."""
        return state["agent_name"]

    def _build_router_graph(self) -> StateGraph:
        """Build the router graph with conditional edges."""
        builder = StateGraph(AgentState)

        # Node 1: classify the query
        builder.add_node("classify", self.classify)

        # One node per agent
        for name in self.agents:
            async def agent_node(state, _name=name):
                agent = self.agents[_name]
                answer = await agent.query(
                    state["query"],
                    state.get("board_state"),
                    state.get("move_history", []),
                )
                return {"final_answer": answer}

            builder.add_node(name, agent_node)

        # Entry -> classify
        builder.set_entry_point("classify")

        # Conditional routing from classify to the appropriate agent
        builder.add_conditional_edges(
            "classify",
            self.route,
            {name: name for name in self.agents},
        )

        # Each agent node -> END
        for name in self.agents:
            builder.add_edge(name, END)

        return builder.compile()

    async def query(
        self,
        question: str,
        board_state: str = None,
        move_history: List[str] = None,
    ) -> str:
        """Public interface matching BaseAgent.query signature."""
        initial_state = AgentState(
            messages=[],
            query=question,
            board_state=board_state or chess.Board().fen(),
            move_history=move_history or [],
            context={},
            agent_name="",
            final_answer=None,
        )
        result = await self.graph.ainvoke(initial_state)
        return result.get("final_answer", "No response generated")
