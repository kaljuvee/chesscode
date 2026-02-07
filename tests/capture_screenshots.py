#!/usr/bin/env python3
"""Capture screenshots of the Chess TUI application."""
import asyncio
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from textual.app import App
from textual.pilot import Pilot
import chess

# Import the main app
sys.path.insert(0, '/home/ubuntu/chesscode')
from chess_tui import ChessTUI


async def capture_initial_state():
    """Capture the initial state of the application."""
    print("Capturing screenshot 1: Initial state...")
    
    app = ChessTUI()
    async with app.run_test() as pilot:
        # Wait for app to initialize
        await pilot.pause(2)
        
        # Save screenshot
        pilot.app.save_screenshot("/home/ubuntu/chesscode/docs/01_initial_state.svg")
        print("  ✓ Saved: docs/01_initial_state.svg")


async def capture_with_moves():
    """Capture state after making some moves."""
    print("Capturing screenshot 2: After moves...")
    
    app = ChessTUI()
    async with app.run_test() as pilot:
        await pilot.pause(2)
        
        # Make some moves
        await pilot.click("#input_container Input")
        await pilot.press("e", "4")
        await pilot.press("enter")
        await pilot.pause(1)
        
        await pilot.click("#input_container Input")
        await pilot.press("e", "5")
        await pilot.press("enter")
        await pilot.pause(1)
        
        await pilot.click("#input_container Input")
        await pilot.press("N", "f", "3")
        await pilot.press("enter")
        await pilot.pause(1)
        
        # Save screenshot
        pilot.app.save_screenshot("/home/ubuntu/chesscode/docs/02_after_moves.svg")
        print("  ✓ Saved: docs/02_after_moves.svg")


async def capture_with_question():
    """Capture state with AI response."""
    print("Capturing screenshot 3: AI analysis...")
    
    app = ChessTUI()
    async with app.run_test() as pilot:
        await pilot.pause(2)
        
        # Make some moves first
        await pilot.click("#input_container Input")
        await pilot.press("e", "4")
        await pilot.press("enter")
        await pilot.pause(0.5)
        
        await pilot.click("#input_container Input")
        await pilot.press("e", "5")
        await pilot.press("enter")
        await pilot.pause(0.5)
        
        # Ask a question
        await pilot.click("#input_container Input")
        await pilot.press(*list("What should white play next?"))
        await pilot.press("enter")
        await pilot.pause(5)  # Wait for AI response
        
        # Save screenshot
        pilot.app.save_screenshot("/home/ubuntu/chesscode/docs/03_ai_analysis.svg")
        print("  ✓ Saved: docs/03_ai_analysis.svg")


async def main():
    """Main screenshot capture routine."""
    print("=" * 60)
    print("Chess TUI - Screenshot Capture")
    print("=" * 60)
    print()
    
    try:
        await capture_initial_state()
        await capture_with_moves()
        await capture_with_question()
        
        print()
        print("=" * 60)
        print("✓ All screenshots captured successfully!")
        print("=" * 60)
        print()
        print("Screenshots saved to docs/ folder:")
        print("  - 01_initial_state.svg")
        print("  - 02_after_moves.svg")
        print("  - 03_ai_analysis.svg")
        
    except Exception as e:
        print(f"\n✗ Error capturing screenshots: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
