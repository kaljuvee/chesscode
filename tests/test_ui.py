#!/usr/bin/env python3
"""Comprehensive UI tests for Chess TUI application."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import chess
from agents.chess_agent import ChessAgent


class TestChessTUI:
    """Test suite for Chess TUI components."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.agent = None
    
    def test_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result."""
        if passed:
            self.passed += 1
            print(f"  ✓ {test_name}")
            if message:
                print(f"    {message}")
        else:
            self.failed += 1
            print(f"  ✗ {test_name}")
            if message:
                print(f"    Error: {message}")
    
    def test_board_creation(self):
        """Test chess board initialization."""
        print("\n1. Testing Board Creation")
        try:
            board = chess.Board()
            self.test_result(
                "Board initialization",
                board.fen() == chess.STARTING_FEN,
                f"FEN: {board.fen()}"
            )
        except Exception as e:
            self.test_result("Board initialization", False, str(e))
    
    def test_move_validation(self):
        """Test move validation."""
        print("\n2. Testing Move Validation")
        board = chess.Board()
        
        # Test valid move
        try:
            move = board.parse_san("e4")
            self.test_result(
                "Valid move parsing (e4)",
                move in board.legal_moves,
                f"Move: {move}"
            )
        except Exception as e:
            self.test_result("Valid move parsing (e4)", False, str(e))
        
        # Test invalid move
        try:
            board.parse_san("e5")  # Invalid for white
            self.test_result("Invalid move detection", False, "Should have raised exception")
        except:
            self.test_result("Invalid move detection", True, "Correctly rejected e5 for white")
    
    def test_move_execution(self):
        """Test move execution and board state."""
        print("\n3. Testing Move Execution")
        board = chess.Board()
        
        try:
            # Make a move
            board.push_san("e4")
            piece_at_e4 = board.piece_at(chess.E4)
            
            self.test_result(
                "Move execution (e4)",
                piece_at_e4 is not None and piece_at_e4.piece_type == chess.PAWN,
                f"Piece at e4: {piece_at_e4}"
            )
            
            # Verify turn changed
            self.test_result(
                "Turn change after move",
                board.turn == chess.BLACK,
                f"Current turn: {'Black' if board.turn == chess.BLACK else 'White'}"
            )
        except Exception as e:
            self.test_result("Move execution", False, str(e))
    
    def test_game_states(self):
        """Test various game states."""
        print("\n4. Testing Game States")
        
        # Test normal position
        board = chess.Board()
        self.test_result(
            "Normal position detection",
            not board.is_checkmate() and not board.is_stalemate(),
            "Board is in normal state"
        )
        
        # Test checkmate position (Fool's Mate)
        board = chess.Board()
        board.push_san("f3")
        board.push_san("e5")
        board.push_san("g4")
        board.push_san("Qh4")
        
        self.test_result(
            "Checkmate detection",
            board.is_checkmate(),
            "Fool's Mate detected"
        )
    
    def test_material_counting(self):
        """Test material counting logic."""
        print("\n5. Testing Material Counting")
        board = chess.Board()
        
        # Count material
        white_material = sum([
            len(board.pieces(pt, chess.WHITE)) * [0, 1, 3, 3, 5, 9][pt] 
            for pt in range(1, 6)
        ])
        black_material = sum([
            len(board.pieces(pt, chess.BLACK)) * [0, 1, 3, 3, 5, 9][pt] 
            for pt in range(1, 6)
        ])
        
        self.test_result(
            "Material equality at start",
            white_material == black_material == 39,
            f"White: {white_material}, Black: {black_material}"
        )
    
    async def test_agent_initialization(self):
        """Test chess agent initialization."""
        print("\n6. Testing Agent Initialization")
        try:
            self.agent = ChessAgent()
            self.test_result(
                "Agent initialization",
                self.agent is not None and self.agent.llm is not None,
                "Agent and LLM initialized"
            )
        except Exception as e:
            self.test_result("Agent initialization", False, str(e))
    
    async def test_agent_query(self):
        """Test agent query functionality."""
        print("\n7. Testing Agent Query")
        
        if not self.agent:
            self.test_result("Agent query", False, "Agent not initialized")
            return
        
        try:
            board = chess.Board()
            response = await self.agent.query(
                "What is the best first move for white?",
                board.fen()
            )
            
            self.test_result(
                "Agent query response",
                len(response) > 0,
                f"Response length: {len(response)} chars"
            )
        except Exception as e:
            self.test_result("Agent query", False, str(e))
    
    async def test_agent_position_analysis(self):
        """Test agent position analysis."""
        print("\n8. Testing Agent Position Analysis")
        
        if not self.agent:
            self.test_result("Agent position analysis", False, "Agent not initialized")
            return
        
        try:
            board = chess.Board()
            board.push_san("e4")
            board.push_san("e5")
            board.push_san("Nf3")
            
            response = await self.agent.query(
                "Analyze this position",
                board.fen()
            )
            
            self.test_result(
                "Position analysis",
                len(response) > 50,
                f"Analysis provided ({len(response)} chars)"
            )
        except Exception as e:
            self.test_result("Position analysis", False, str(e))
    
    def test_unicode_pieces(self):
        """Test Unicode piece rendering."""
        print("\n9. Testing Unicode Piece Rendering")
        
        piece_symbols = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
        }
        
        try:
            board = chess.Board()
            piece_at_e2 = board.piece_at(chess.E2)
            symbol = piece_symbols.get(piece_at_e2.symbol(), '?')
            
            self.test_result(
                "Unicode piece rendering",
                symbol == '♙',
                f"White pawn symbol: {symbol}"
            )
        except Exception as e:
            self.test_result("Unicode piece rendering", False, str(e))
    
    def test_fen_parsing(self):
        """Test FEN notation parsing."""
        print("\n10. Testing FEN Parsing")
        
        test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        
        try:
            board = chess.Board(test_fen)
            self.test_result(
                "FEN parsing",
                board.piece_at(chess.E4) is not None,
                f"Loaded position from FEN"
            )
        except Exception as e:
            self.test_result("FEN parsing", False, str(e))
    
    async def run_all_tests(self):
        """Run all tests."""
        print("=" * 70)
        print("Chess TUI - Comprehensive Test Suite")
        print("=" * 70)
        
        # Synchronous tests
        self.test_board_creation()
        self.test_move_validation()
        self.test_move_execution()
        self.test_game_states()
        self.test_material_counting()
        self.test_unicode_pieces()
        self.test_fen_parsing()
        
        # Asynchronous tests
        await self.test_agent_initialization()
        await self.test_agent_query()
        await self.test_agent_position_analysis()
        
        # Summary
        print("\n" + "=" * 70)
        print(f"Test Results: {self.passed} passed, {self.failed} failed")
        print("=" * 70)
        
        return self.failed == 0


async def main():
    """Main test runner."""
    tester = TestChessTUI()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {tester.failed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
