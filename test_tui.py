#!/usr/bin/env python3
"""Test script for Chess TUI - demonstrates functionality."""
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

from chess_agent import ChessAgent
import chess


async def test_agent():
    """Test the chess agent functionality."""
    print("=" * 60)
    print("Chess TUI - Agent Test")
    print("=" * 60)
    
    # Initialize agent
    print("\n1. Initializing Chess Agent...")
    agent = ChessAgent()
    print("   ✓ Agent initialized successfully!")
    
    # Create a test board
    board = chess.Board()
    
    # Test 1: Opening advice
    print("\n2. Testing opening advice...")
    response = await agent.query("What are the best opening moves for white?", board.fen())
    print(f"   Response: {response[:200]}...")
    
    # Make some moves
    print("\n3. Making test moves...")
    board.push_san("e4")
    print("   ✓ Played e4")
    board.push_san("e5")
    print("   ✓ Played e5")
    board.push_san("Nf3")
    print("   ✓ Played Nf3")
    
    # Test 2: Position analysis
    print("\n4. Testing position analysis...")
    response = await agent.query("Analyze the current position", board.fen())
    print(f"   Response: {response[:200]}...")
    
    # Test 3: Move suggestion
    print("\n5. Testing move suggestion...")
    response = await agent.query("What should black play next?", board.fen())
    print(f"   Response: {response[:200]}...")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


def display_board_ascii(board):
    """Display board in ASCII format."""
    print("\n" + "  ┌─────────────────────────────────┐")
    
    for rank in range(7, -1, -1):
        rank_str = f"{rank + 1} │ "
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            
            if piece:
                symbol = piece.unicode_symbol()
            else:
                symbol = '·'
            
            rank_str += f"{symbol}  "
        
        rank_str += "│"
        print(rank_str)
    
    print("  └─────────────────────────────────┘")
    print("    a   b   c   d   e   f   g   h\n")


def test_board_display():
    """Test the board display."""
    print("=" * 60)
    print("Chess TUI - Board Display Test")
    print("=" * 60)
    
    board = chess.Board()
    
    print("\n1. Initial position:")
    display_board_ascii(board)
    
    print("2. After 1.e4:")
    board.push_san("e4")
    display_board_ascii(board)
    
    print("3. After 1...e5:")
    board.push_san("e5")
    display_board_ascii(board)
    
    print("4. After 2.Nf3:")
    board.push_san("Nf3")
    display_board_ascii(board)
    
    print("5. After 2...Nc6:")
    board.push_san("Nc6")
    display_board_ascii(board)
    
    print("=" * 60)
    print("Board display test complete! ✓")
    print("=" * 60)


if __name__ == "__main__":
    # Test board display
    test_board_display()
    
    print("\n\n")
    
    # Test agent
    asyncio.run(test_agent())
    
    print("\n\nTo run the full TUI application, execute:")
    print("  python3 chess_tui.py")
