"""Chess Agent with LangGraph for intelligent analysis."""
import os
import json
from typing import List, Dict, Optional, Annotated, TypedDict
from operator import add
import chess
import chess.pgn

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import StructuredTool, tool
from langgraph.graph import StateGraph, END

from llm_provider import LLMProvider


class ChessAgentState(TypedDict):
    """State management for the chess agent."""
    messages: Annotated[List[BaseMessage], add]
    query: str
    board_state: str
    move_history: List[str]
    analysis: str
    final_answer: Optional[str]


class ChessAgent:
    """LangGraph-based agent for chess analysis and assistance."""

    SYSTEM_PROMPT = """You are an expert chess assistant with deep knowledge of chess strategy, tactics, and theory.
You help players understand positions, suggest moves, and provide educational insights.

When analyzing positions:
- Consider material balance
- Evaluate piece activity and positioning
- Identify tactical opportunities (pins, forks, skewers, etc.)
- Assess pawn structure
- Consider king safety
- Suggest candidate moves with explanations

When a user asks about a move or position, provide clear, educational responses that help them improve their understanding of chess.
Keep responses concise but informative."""

    def __init__(self, model: str = None, provider: str = None):
        """Initialize the chess agent."""
        self.model = model or os.getenv("MODEL", "grok-4-fast-reasoning")
        self.provider = provider or os.getenv("MODEL_PROVIDER", "xai")
        self.llm = LLMProvider.get_model(self.model, self.provider, temperature=0.7)
        
        # No tools needed for simple query-response
        
        # Build graph
        self.graph = self._build_graph()

    def _build_tools(self) -> List:
        """Build chess-specific tools."""
        # Use simple tool decorator instead of StructuredTool
        return []  # Tools are not needed for simple query-response flow

    def _analyze_position(self, fen: str = None) -> str:
        """Analyze a chess position given its FEN."""
        try:
            board = chess.Board(fen) if fen else chess.Board()
            
            # Material count
            material = {
                "white": sum([len(board.pieces(pt, chess.WHITE)) * [0, 1, 3, 3, 5, 9][pt] 
                             for pt in range(1, 6)]),
                "black": sum([len(board.pieces(pt, chess.BLACK)) * [0, 1, 3, 3, 5, 9][pt] 
                             for pt in range(1, 6)])
            }
            
            # Check status
            in_check = board.is_check()
            checkmate = board.is_checkmate()
            stalemate = board.is_stalemate()
            
            # Legal moves count
            legal_moves = board.legal_moves.count()
            
            analysis = f"""Position Analysis:
- Turn: {'White' if board.turn else 'Black'}
- Material: White {material['white']}, Black {material['black']} (Advantage: {abs(material['white'] - material['black'])} for {'White' if material['white'] > material['black'] else 'Black' if material['black'] > material['white'] else 'Equal'})
- Check: {'Yes' if in_check else 'No'}
- Checkmate: {'Yes' if checkmate else 'No'}
- Stalemate: {'Yes' if stalemate else 'No'}
- Legal moves available: {legal_moves}
- FEN: {board.fen()}"""
            
            return analysis
        except Exception as e:
            return f"Error analyzing position: {str(e)}"

    def _suggest_move(self, fen: str = None) -> str:
        """Suggest a move for the current position."""
        try:
            board = chess.Board(fen) if fen else chess.Board()
            
            if board.is_game_over():
                return "Game is over. No moves available."
            
            # Get all legal moves
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return "No legal moves available."
            
            # Simple heuristic: prefer captures, then center control
            captures = [m for m in legal_moves if board.is_capture(m)]
            center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
            center_moves = [m for m in legal_moves if m.to_square in center_squares]
            
            suggested = None
            reason = ""
            
            if captures:
                suggested = captures[0]
                reason = "Capturing opponent's piece"
            elif center_moves:
                suggested = center_moves[0]
                reason = "Controlling the center"
            else:
                suggested = legal_moves[0]
                reason = "Developing pieces"
            
            return f"Suggested move: {board.san(suggested)} - {reason}"
        except Exception as e:
            return f"Error suggesting move: {str(e)}"

    def _explain_move(self, move: str, fen: str = None) -> str:
        """Explain a specific chess move."""
        try:
            board = chess.Board(fen) if fen else chess.Board()
            
            # Try to parse the move
            try:
                parsed_move = board.parse_san(move)
            except:
                return f"Invalid move notation: {move}"
            
            # Check if move is legal
            if parsed_move not in board.legal_moves:
                return f"Illegal move: {move}"
            
            # Analyze the move
            is_capture = board.is_capture(parsed_move)
            gives_check = board.gives_check(parsed_move)
            
            explanation = f"Move {move}:\n"
            explanation += f"- From: {chess.square_name(parsed_move.from_square)}\n"
            explanation += f"- To: {chess.square_name(parsed_move.to_square)}\n"
            
            if is_capture:
                explanation += "- This is a capture\n"
            if gives_check:
                explanation += "- This move gives check\n"
            
            return explanation
        except Exception as e:
            return f"Error explaining move: {str(e)}"

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        builder = StateGraph(ChessAgentState)

        # Define nodes
        builder.add_node("process_query", self._process_query)
        builder.add_node("generate_response", self._generate_response)

        # Define edges
        builder.set_entry_point("process_query")
        builder.add_edge("process_query", "generate_response")
        builder.add_edge("generate_response", END)

        return builder.compile()

    async def _process_query(self, state: ChessAgentState) -> Dict:
        """Process the user query and gather context."""
        query = state["query"]
        board_state = state.get("board_state", chess.Board().fen())
        
        # Analyze current position
        analysis = self._analyze_position(board_state)
        
        return {
            "analysis": analysis,
        }

    async def _generate_response(self, state: ChessAgentState) -> Dict:
        """Generate final response using LLM."""
        query = state["query"]
        board_state = state.get("board_state", chess.Board().fen())
        analysis = state.get("analysis", "")
        
        # Build prompt
        prompt = f"""Current Position Analysis:
{analysis}

User Question: {query}

Please provide a helpful, educational response to the user's question about this chess position."""

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        # Get LLM response
        response = self.llm.invoke(messages)
        final_answer = response.content if hasattr(response, "content") else str(response)
        
        return {
            "final_answer": final_answer,
            "messages": [AIMessage(content=final_answer)]
        }

    async def query(self, question: str, board_state: str = None) -> str:
        """Query the agent with a chess-related question."""
        initial_state = ChessAgentState(
            messages=[],
            query=question,
            board_state=board_state or chess.Board().fen(),
            move_history=[],
            analysis="",
            final_answer=None
        )
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state)
        return result.get("final_answer", "No response generated")
