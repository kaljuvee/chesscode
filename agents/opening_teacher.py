"""Opening and variation teacher agent - teaches opening theory from PGN files."""
from typing import Dict

from .base_agent import BaseAgent, AgentState
from tools.board_tools import analyze_position
from tools import pgn_tools


class OpeningTeacherAgent(BaseAgent):
    """Opening theory specialist: explains variations, plans, and typical ideas."""

    @property
    def name(self) -> str:
        return "opening_teacher"

    @property
    def system_prompt(self) -> str:
        return (
            "You are an opening theory specialist with encyclopedic knowledge "
            "of chess openings and their variations.\n\n"
            "When teaching openings:\n"
            "- Identify the opening by name and ECO code\n"
            "- Explain the main ideas and plans for both sides\n"
            "- Show key variations and move orders\n"
            "- Discuss typical middlegame structures that arise\n"
            "- Reference famous games where the opening was played\n"
            "- Warn about common traps and pitfalls\n"
            "- Suggest which openings suit different playing styles\n\n"
            "Use the database results to support your teaching with real game examples."
        )

    async def gather_context(self, state: AgentState) -> Dict:
        """Identify the opening and find relevant variations."""
        fen = state.get("board_state", "")
        position = analyze_position(fen)

        # Identify the opening from the current position
        opening_info = pgn_tools.identify_opening(fen) if fen else None

        # Search for games and variations with this opening
        variations = []
        master_games = []
        eco = None
        if opening_info:
            eco = opening_info.get("eco", "")
            try:
                variations = pgn_tools.get_opening_variations(eco, max_results=5)
                master_games_raw = pgn_tools.search_games(eco=eco)
                master_games = [pgn_tools.game_to_dict(g) for g in master_games_raw[:5]]
            except Exception:
                pass

        # Also search opening-specific PGN files in data/openings/
        opening_file_games = []
        try:
            from pathlib import Path
            openings_dir = Path("data/openings")
            if openings_dir.exists():
                for pgn_path in openings_dir.glob("*.pgn"):
                    games = pgn_tools.load_pgn_file(str(pgn_path))
                    if eco:
                        games = pgn_tools.search_games(games=games, eco=eco)
                    opening_file_games.extend(
                        pgn_tools.game_to_dict(g) for g in games[:3]
                    )
        except Exception:
            pass

        return {
            "context": {
                "position": position,
                "opening": opening_info,
                "eco": eco,
                "variations": variations,
                "master_games": master_games,
                "opening_file_games": opening_file_games,
            }
        }

    def _build_prompt(self, state: AgentState) -> str:
        ctx = state.get("context", {})
        parts = []

        if ctx.get("position"):
            parts.append(f"Current Position:\n{ctx['position']}")

        if ctx.get("opening"):
            op = ctx["opening"]
            parts.append(f"Opening: {op.get('name', 'Unknown')} ({op.get('eco', '?')})")

        if ctx.get("variations"):
            var_text = "\n".join(
                f"- {v['white']} vs {v['black']}: {v['moves']}"
                for v in ctx["variations"]
            )
            parts.append(f"Example Variations:\n{var_text}")

        if ctx.get("master_games"):
            games_text = "\n".join(
                f"- {g['white']} vs {g['black']} ({g['result']}, {g['date']})"
                for g in ctx["master_games"]
            )
            parts.append(f"Master Games:\n{games_text}")

        if ctx.get("opening_file_games"):
            of_text = "\n".join(
                f"- {g['white']} vs {g['black']} ({g['result']})"
                for g in ctx["opening_file_games"]
            )
            parts.append(f"Opening File Examples:\n{of_text}")

        parts.append(f"User Question: {state['query']}")
        parts.append("Explain the opening theory, key ideas, and typical plans.")
        return "\n\n".join(parts)
