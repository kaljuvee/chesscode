"""Personal teacher agent - assesses player strength and provides tailored coaching."""
from typing import Dict, List

from .base_agent import BaseAgent, AgentState
from tools.board_tools import analyze_position, get_game_phase
from tools import pgn_tools


class PersonalTeacherAgent(BaseAgent):
    """Personal chess coach: measures, advises, and assigns exercises by level."""

    @property
    def name(self) -> str:
        return "personal_teacher"

    @property
    def system_prompt(self) -> str:
        return (
            "You are an experienced personal chess coach. Your approach is:\n\n"
            "1. ASSESS: Evaluate the student's current level based on their games "
            "and the current position. Estimate their approximate rating.\n"
            "2. IDENTIFY: Find their specific weaknesses - are they struggling with "
            "tactics, positional play, endgames, openings, or time management?\n"
            "3. ADVISE: Give clear, actionable advice on what to study and practice.\n"
            "4. EXERCISE: Provide a concrete exercise or study task tailored to their level.\n\n"
            "Rating guidelines:\n"
            "- ACPL ~15: 2200+ (Master level)\n"
            "- ACPL ~25: 1800-2200 (Advanced)\n"
            "- ACPL ~40: 1400-1800 (Intermediate)\n"
            "- ACPL ~60: 1000-1400 (Beginner-Intermediate)\n"
            "- ACPL ~100+: Under 1000 (Beginner)\n\n"
            "Always be encouraging but honest. Focus on one improvement area at a time."
        )

    async def gather_context(self, state: AgentState) -> Dict:
        """Analyze games to assess player level and identify weaknesses."""
        fen = state.get("board_state", "")
        position = analyze_position(fen)
        phase = get_game_phase(fen) if fen else "unknown"

        context = {
            "position": position,
            "game_phase": phase,
            "assessment": None,
            "weaknesses": [],
        }

        # Try to get player stats from engine analysis
        try:
            from tools.stockfish_tools import analyze_position as engine_analyze
            engine_result = await engine_analyze(fen, depth=20, num_lines=3)
            context["engine_eval"] = engine_result
        except Exception:
            pass

        # Check if there are player games to analyze
        query = state.get("query", "")
        # Try to find a player name for personalized analysis
        for word in query.split():
            if len(word) > 3 and word[0].isupper():
                try:
                    games = pgn_tools.find_player_games(word)
                    if games:
                        context["player_name"] = word
                        context["player_games_count"] = len(games)

                        # Compute basic win/loss stats
                        wins = sum(1 for g in games if g.headers.get("Result") in ["1-0", "0-1"])
                        draws = sum(1 for g in games if g.headers.get("Result") == "1/2-1/2")
                        context["basic_record"] = {
                            "total": len(games),
                            "decisive": wins,
                            "draws": draws,
                        }

                        # Try engine analysis for a few games
                        try:
                            from tools.stockfish_tools import batch_analyze_games
                            stats = await batch_analyze_games(games[:5], depth=14)
                            context["assessment"] = stats
                            context["weaknesses"] = self._identify_weaknesses(stats)
                        except Exception:
                            pass
                        break
                except Exception:
                    continue

        return {"context": context}

    def _identify_weaknesses(self, stats: Dict) -> List[str]:
        """Identify specific areas for improvement from statistical analysis."""
        weaknesses = []
        phases = stats.get("phase_stats", {})

        # Check endgame vs opening performance
        endgame_acpl = phases.get("endgame", {}).get("acpl", 0)
        opening_acpl = phases.get("opening", {}).get("acpl", 0)
        middlegame_acpl = phases.get("middlegame", {}).get("acpl", 0)

        if endgame_acpl > opening_acpl * 1.5 and endgame_acpl > 30:
            weaknesses.append("endgame_technique")

        if opening_acpl > middlegame_acpl * 1.5 and opening_acpl > 30:
            weaknesses.append("opening_preparation")

        if stats.get("blunder_rate", 0) > 0.05:
            weaknesses.append("tactical_awareness")

        if stats.get("t1_accuracy", 0) < 0.3:
            weaknesses.append("move_accuracy")

        if stats.get("acpl", 0) > 60:
            weaknesses.append("general_chess_understanding")

        return weaknesses

    def _build_prompt(self, state: AgentState) -> str:
        ctx = state.get("context", {})
        parts = []

        if ctx.get("position"):
            parts.append(f"Current Position:\n{ctx['position']}")
            parts.append(f"Game Phase: {ctx.get('game_phase', 'unknown')}")

        if ctx.get("player_name"):
            parts.append(
                f"Student: {ctx['player_name']} "
                f"({ctx.get('player_games_count', 0)} games in database)"
            )

        if ctx.get("basic_record"):
            rec = ctx["basic_record"]
            parts.append(
                f"Record: {rec['total']} games, "
                f"{rec['decisive']} decisive, {rec['draws']} draws"
            )

        if ctx.get("assessment"):
            s = ctx["assessment"]
            parts.append(
                f"Performance Analysis:\n"
                f"- ACPL: {s.get('acpl', 'N/A')}\n"
                f"- Blunder rate: {s.get('blunder_rate', 0):.1%}\n"
                f"- T1 accuracy: {s.get('t1_accuracy', 0):.1%}"
            )

        if ctx.get("weaknesses"):
            weakness_names = {
                "endgame_technique": "Endgame technique needs work",
                "opening_preparation": "Opening preparation is weak",
                "tactical_awareness": "Too many blunders - tactical vision needed",
                "move_accuracy": "Low move accuracy - calculation needs improvement",
                "general_chess_understanding": "Overall chess understanding needs development",
            }
            items = [weakness_names.get(w, w) for w in ctx["weaknesses"]]
            parts.append("Identified Weaknesses:\n" + "\n".join(f"- {i}" for i in items))

        parts.append(f"Student's Question: {state['query']}")
        parts.append(
            "Assess the student's level, explain their weaknesses, and "
            "assign a specific exercise or study task appropriate for their level."
        )
        return "\n\n".join(parts)
