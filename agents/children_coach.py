"""Children's chess coach agent - teaches concepts at age-appropriate level."""
from pathlib import Path
from typing import Dict

from .base_agent import BaseAgent, AgentState
from tools.board_tools import analyze_position, get_legal_moves


class ChildrenCoachAgent(BaseAgent):
    """Friendly children's chess teacher using simple language and encouragement."""

    @property
    def name(self) -> str:
        return "children_coach"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a friendly and encouraging children's chess coach. "
            "Your students are beginners aged 6-14.\n\n"
            "Teaching guidelines:\n"
            "- Use simple, clear language. Avoid complex jargon.\n"
            "- When introducing a concept, always explain it first with a simple analogy.\n"
            "- Break complex ideas into small, digestible steps.\n"
            "- Use the current board position to illustrate concepts.\n"
            "- Always encourage the student and praise their progress.\n"
            "- Give one key lesson or idea at a time, not too many.\n"
            "- Use phrases like 'Great question!', 'Let me show you a cool trick!'\n"
            "- When explaining moves, describe what each piece 'wants to do'.\n"
            "- End responses with a simple exercise or question to keep them engaged.\n\n"
            "Topics you can teach: how pieces move, basic tactics (forks, pins, skewers), "
            "opening principles, checkmate patterns, piece values, and good sportsmanship."
        )

    async def gather_context(self, state: AgentState) -> Dict:
        """Gather position info and book content for the lesson."""
        position = analyze_position(state.get("board_state"))
        legal_moves = get_legal_moves(state.get("board_state", ""))

        # Load book content if available
        book_content = await self._load_book_content(state.get("query", ""))

        return {
            "context": {
                "position": position,
                "legal_moves_count": len(legal_moves),
                "sample_moves": legal_moves[:5],
                "book_content": book_content,
            }
        }

    async def _load_book_content(self, query: str) -> str:
        """Load relevant book content from data/books/ directory.

        Returns content if found, or a message indicating no book is loaded.
        This is a framework - when the book is ready, content files
        (Markdown, JSON, or annotated PGN) go in data/books/.
        """
        book_dir = Path("data/books")
        if not book_dir.exists():
            return ""

        # Search for relevant content files
        content_parts = []
        for ext in ["*.md", "*.txt", "*.json"]:
            for filepath in book_dir.glob(ext):
                try:
                    text = filepath.read_text(encoding="utf-8")
                    # Simple keyword relevance check
                    query_words = set(query.lower().split())
                    if any(word in text.lower() for word in query_words if len(word) > 3):
                        content_parts.append(
                            f"[From {filepath.name}]\n{text[:500]}"
                        )
                except Exception:
                    continue

        return "\n\n".join(content_parts) if content_parts else ""

    def _build_prompt(self, state: AgentState) -> str:
        ctx = state.get("context", {})
        parts = []

        if ctx.get("position"):
            parts.append(f"Current Board:\n{ctx['position']}")

        if ctx.get("sample_moves"):
            moves = ", ".join(ctx["sample_moves"])
            parts.append(f"Some possible moves: {moves}")

        if ctx.get("book_content"):
            parts.append(f"Reference Material:\n{ctx['book_content']}")

        parts.append(f"Student's Question: {state['query']}")
        parts.append(
            "Explain in a simple, fun way that a child can understand. "
            "End with an encouraging exercise or question."
        )
        return "\n\n".join(parts)
