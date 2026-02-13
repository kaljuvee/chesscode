"""Stockfish engine interface agent - position analysis and best move calculation."""
from typing import Dict

from .base_agent import BaseAgent, AgentState


class EngineAgent(BaseAgent):
    """Stockfish engine wrapper: provides precise evaluations and best lines."""

    @property
    def name(self) -> str:
        return "engine"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Stockfish engine interface. Your role is to translate engine "
            "evaluations into clear, understandable analysis.\n\n"
            "When presenting engine results:\n"
            "- Show the evaluation in centipawns or mate-in-N\n"
            "- List the top candidate moves with their evaluations\n"
            "- Explain why the engine prefers certain moves\n"
            "- Describe the key ideas behind the best lines\n"
            "- Note any tactical threats or positional advantages\n\n"
            "Be precise with evaluations but also explain the chess reasoning "
            "behind the numbers."
        )

    async def gather_context(self, state: AgentState) -> Dict:
        """Run Stockfish analysis on the current position."""
        fen = state.get("board_state")
        context = {"engine_available": False}

        try:
            from tools.stockfish_tools import analyze_position
            analysis = await analyze_position(fen, depth=22, num_lines=3)
            context = {
                "engine_available": True,
                "evaluation": analysis["evaluation"],
                "lines": analysis["lines"],
                "depth": analysis["depth"],
            }
        except Exception as e:
            context["error"] = str(e)
            # Fall back to basic board analysis
            from tools.board_tools import analyze_position as basic_analysis
            context["basic_analysis"] = basic_analysis(fen)

        return {"context": context}

    def _build_prompt(self, state: AgentState) -> str:
        ctx = state.get("context", {})
        parts = [f"Position (FEN): {state.get('board_state', 'unknown')}"]

        if ctx.get("engine_available"):
            ev = ctx["evaluation"]
            if ev["type"] == "cp":
                eval_str = f"{ev['value'] / 100:+.2f} pawns"
            else:
                eval_str = f"Mate in {ev['value']}"
            parts.append(f"Engine Evaluation (depth {ctx['depth']}): {eval_str}")

            lines_text = []
            for i, line in enumerate(ctx.get("lines", []), 1):
                move = line.get("Move", "?")
                cp = line.get("Centipawn")
                mate = line.get("Mate")
                if mate is not None:
                    score = f"Mate in {mate}"
                elif cp is not None:
                    score = f"{cp / 100:+.2f}"
                else:
                    score = "?"
                lines_text.append(f"  {i}. {move} ({score})")
            parts.append("Top moves:\n" + "\n".join(lines_text))
        elif ctx.get("basic_analysis"):
            parts.append(f"Basic Analysis (engine unavailable):\n{ctx['basic_analysis']}")
        elif ctx.get("error"):
            parts.append(f"Engine error: {ctx['error']}")

        parts.append(f"User Question: {state['query']}")
        parts.append("Explain the engine analysis in clear terms.")
        return "\n\n".join(parts)
