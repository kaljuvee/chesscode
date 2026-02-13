"""Player analysis agent - PGN-Spy style statistical analysis."""
import re
from typing import Dict, List

from .base_agent import BaseAgent, AgentState
from tools import pgn_tools


class PlayerAnalystAgent(BaseAgent):
    """PGN-Spy style analyzer: measures player performance statistics."""

    @property
    def name(self) -> str:
        return "player_analyst"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a chess performance analyst specializing in statistical analysis "
            "of player games, similar to PGN-Spy.\n\n"
            "When analyzing a player's performance:\n"
            "- Report ACPL (Average CentiPawn Loss) - lower is better\n"
            "- Show blunder rate (moves losing >200cp), mistake rate (100-200cp), "
            "inaccuracy rate (50-100cp)\n"
            "- Report T1/T2/T3 accuracy: how often the player found the engine's "
            "top 1st, 2nd, or 3rd choice\n"
            "- Break down performance by game phase (opening/middlegame/endgame)\n"
            "- Identify patterns: which phases have the most errors?\n"
            "- Compare to typical ratings: ACPL ~30 = ~2000 ELO, ACPL ~50 = ~1500 ELO\n"
            "- Give specific, actionable improvement advice based on the statistics\n\n"
            "Always present statistics clearly and explain what the numbers mean."
        )

    def _extract_player_name(self, query: str) -> str:
        """Extract a player name from the query text."""
        # Known player names from PGN files
        known_players = [
            "Kasparov", "Karpov", "Keres", "Shabalov", "Ehlvest",
        ]
        query_lower = query.lower()
        for name in known_players:
            if name.lower() in query_lower:
                return name

        # Try to find capitalized words that could be names
        words = query.split()
        for word in words:
            cleaned = re.sub(r"[^a-zA-Z]", "", word)
            if cleaned and cleaned[0].isupper() and len(cleaned) > 2:
                if cleaned.lower() not in {
                    "analyze", "analysis", "show", "what", "how", "the",
                    "player", "games", "chess", "blunder", "rate", "statistics",
                }:
                    return cleaned

        return ""

    async def gather_context(self, state: AgentState) -> Dict:
        """Find player games and run statistical analysis."""
        query = state.get("query", "")
        player_name = self._extract_player_name(query)

        context = {
            "player_name": player_name,
            "games_found": 0,
            "stats": None,
            "sample_games": [],
        }

        if not player_name:
            context["error"] = "Could not identify a player name in your query."
            return {"context": context}

        # Find player's games
        try:
            games = pgn_tools.find_player_games(player_name)
            context["games_found"] = len(games)

            if not games:
                context["error"] = f"No games found for '{player_name}' in the database."
                return {"context": context}

            # Sample games for display
            context["sample_games"] = [
                pgn_tools.game_to_dict(g) for g in games[:5]
            ]

            # Run Stockfish analysis if available
            try:
                from tools.stockfish_tools import batch_analyze_games
                # Analyze up to 10 games for reasonable speed
                games_to_analyze = games[:10]
                stats = await batch_analyze_games(games_to_analyze, depth=16)
                context["stats"] = stats
            except Exception as e:
                context["engine_error"] = str(e)
                # Provide basic stats without engine
                context["basic_stats"] = self._compute_basic_stats(games)

        except Exception as e:
            context["error"] = f"Error searching for games: {e}"

        return {"context": context}

    def _compute_basic_stats(self, games: list) -> Dict:
        """Compute basic stats without engine (win/loss/draw, openings, etc.)."""
        stats = {
            "total_games": len(games),
            "wins_white": 0, "wins_black": 0,
            "draws": 0, "losses_white": 0, "losses_black": 0,
            "openings": {},
        }
        for game in games:
            result = game.headers.get("Result", "")
            eco = game.headers.get("ECO", "?")
            stats["openings"][eco] = stats["openings"].get(eco, 0) + 1

            if result == "1-0":
                stats["wins_white"] += 1
            elif result == "0-1":
                stats["wins_black"] += 1
            elif result == "1/2-1/2":
                stats["draws"] += 1

        # Top 5 openings
        stats["top_openings"] = sorted(
            stats["openings"].items(), key=lambda x: -x[1]
        )[:5]
        return stats

    def _build_prompt(self, state: AgentState) -> str:
        ctx = state.get("context", {})
        parts = []

        if ctx.get("player_name"):
            parts.append(f"Player: {ctx['player_name']}")
            parts.append(f"Games found in database: {ctx.get('games_found', 0)}")

        if ctx.get("error"):
            parts.append(f"Note: {ctx['error']}")

        if ctx.get("stats"):
            s = ctx["stats"]
            parts.append(
                f"Engine Analysis Results ({s.get('games_analyzed', 0)} games analyzed):\n"
                f"- ACPL: {s.get('acpl', 'N/A')}\n"
                f"- Blunder rate: {s.get('blunder_rate', 0):.1%}\n"
                f"- Mistake rate: {s.get('mistake_rate', 0):.1%}\n"
                f"- Inaccuracy rate: {s.get('inaccuracy_rate', 0):.1%}\n"
                f"- T1 accuracy: {s.get('t1_accuracy', 0):.1%}\n"
                f"- T2 accuracy: {s.get('t2_accuracy', 0):.1%}\n"
                f"- T3 accuracy: {s.get('t3_accuracy', 0):.1%}"
            )
            phases = s.get("phase_stats", {})
            for phase_name, ps in phases.items():
                if ps.get("positions", 0) > 0:
                    parts.append(
                        f"- {phase_name.capitalize()}: ACPL={ps.get('acpl', 'N/A')}, "
                        f"Blunders={ps.get('blunders', 0)}"
                    )

        if ctx.get("basic_stats"):
            bs = ctx["basic_stats"]
            parts.append(
                f"Basic Statistics:\n"
                f"- Total games: {bs['total_games']}\n"
                f"- Wins as White: {bs['wins_white']}\n"
                f"- Wins as Black: {bs['wins_black']}\n"
                f"- Draws: {bs['draws']}"
            )
            if bs.get("top_openings"):
                openings = ", ".join(f"{eco}({n})" for eco, n in bs["top_openings"])
                parts.append(f"- Top openings: {openings}")

        if ctx.get("sample_games"):
            games_text = "\n".join(
                f"  {g['white']} vs {g['black']} ({g['result']}, {g['eco']})"
                for g in ctx["sample_games"]
            )
            parts.append(f"Sample Games:\n{games_text}")

        if ctx.get("engine_error"):
            parts.append(f"Engine unavailable: {ctx['engine_error']}")

        parts.append(f"User Question: {state['query']}")
        parts.append(
            "Provide a detailed statistical analysis with improvement advice."
        )
        return "\n\n".join(parts)
