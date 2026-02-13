"""General chess agent - ChessBase AI style database search and Q&A."""
from typing import Dict, List

from .base_agent import BaseAgent, AgentState
from tools.board_tools import analyze_position
from tools import pgn_tools


class GeneralAgent(BaseAgent):
    """ChessBase AI: searches the game database, answers general chess questions."""

    @property
    def name(self) -> str:
        return "general"

    @property
    def system_prompt(self) -> str:
        return (
            "You are ChessBase AI, an expert chess database assistant with deep knowledge "
            "of chess strategy, tactics, theory, and history.\n\n"
            "When analyzing positions:\n"
            "- Consider material balance\n"
            "- Evaluate piece activity and positioning\n"
            "- Identify tactical opportunities (pins, forks, skewers, etc.)\n"
            "- Assess pawn structure\n"
            "- Consider king safety\n"
            "- Suggest candidate moves with explanations\n\n"
            "When searching the database, reference specific games, players, and events. "
            "Provide clear, educational responses that help players improve."
        )

    async def gather_context(self, state: AgentState) -> Dict:
        """Gather position analysis and database search results."""
        position = analyze_position(state.get("board_state"))

        # Search PGN database for relevant games
        query = state.get("query", "")
        search_results = []
        try:
            # Try to extract player name or ECO from query for targeted search
            games = pgn_tools.load_all_pgn_files()
            # Simple keyword search in player names
            for word in query.split():
                if len(word) > 3:
                    matches = pgn_tools.search_games(games=games, player=word)
                    if matches:
                        search_results = [pgn_tools.game_to_dict(g) for g in matches[:5]]
                        break
        except Exception:
            pass

        return {
            "context": {
                "position": position,
                "search_results": search_results,
            }
        }

    def _build_prompt(self, state: AgentState) -> str:
        ctx = state.get("context", {})
        parts = []

        if ctx.get("position"):
            parts.append(f"Current Position Analysis:\n{ctx['position']}")

        if ctx.get("search_results"):
            games_text = "\n".join(
                f"- {g['white']} vs {g['black']} ({g['result']}, {g['eco']}, {g['date']})"
                for g in ctx["search_results"]
            )
            parts.append(f"Database Results:\n{games_text}")

        parts.append(f"User Question: {state['query']}")
        parts.append("Provide a helpful, educational response.")
        return "\n\n".join(parts)
