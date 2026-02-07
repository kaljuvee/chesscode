# ChessCode TUI Screenshots

This document showcases the ChessCode Terminal User Interface in action.

## Screenshot 1: Initial Application State

![Initial State](01_initial_state.svg)

The application starts with:
- **Chess Board** (left panel): Standard starting position with Unicode chess pieces
- **AI Assistant** (right panel): Ready to answer questions
- **Game Status** (bottom left): Shows turn, game status, and material balance
- **Move History** (bottom right): Empty at start
- **Input Field** (bottom): For entering moves or questions
- **Keyboard Shortcuts** (footer): Quick access to common actions

## Screenshot 2: Game in Progress

After playing the moves `1.e4 e5 2.Nf3 Nc6`, the board shows:

```
  ┌─────────────────────────────────┐
8 │ ♜  ·  ♝  ♛  ♚  ♝  ♞  ♜  │
7 │ ♟  ♟  ♟  ♟  ·  ♟  ♟  ♟  │
6 │ ·  ·  ♞  ·  ·  ·  ·  ·  │
5 │ ·  ·  ·  ·  ♟  ·  ·  ·  │
4 │ ·  ·  ·  ·  ♙  ·  ·  ·  │
3 │ ·  ·  ·  ·  ·  ♘  ·  ·  │
2 │ ♙  ♙  ♙  ♙  ·  ♙  ♙  ♙  │
1 │ ♖  ♘  ♗  ♕  ♔  ♗  ·  ♖  │
  └─────────────────────────────────┘
    a   b   c   d   e   f   g   h
```

**Move History Panel:**
```
1. e4 e5
2. Nf3 Nc6
```

**Game Status:**
- Turn: White
- Status: Active
- Material: Equal

## Screenshot 3: AI Analysis

When asking "What should white play next?", the AI assistant provides:

**AI Response:**
> This is a standard Italian Game opening position. White has several strong options:
> 
> 1. **Bc4** - Develops the bishop to an active square, attacking f7 (the weakest point in Black's position). This leads to the Italian Game proper.
> 
> 2. **Bb5** - The Ruy Lopez (Spanish Opening), one of the most popular and deeply analyzed openings in chess. Puts pressure on the knight defending e5.
> 
> 3. **d4** - The Scotch Game, immediately challenging the center and opening lines for piece development.
> 
> I recommend **Bc4** for a classical Italian Game setup, which offers:
> - Quick development
> - Pressure on f7
> - Flexible pawn structure
> - Rich tactical opportunities

## Features Demonstrated

### Interactive Chessboard
- ✓ Unicode chess pieces for clear visualization
- ✓ Rank and file labels
- ✓ Real-time board updates after each move

### AI Assistant
- ✓ Natural language understanding
- ✓ Strategic analysis
- ✓ Move suggestions with explanations
- ✓ Educational insights

### Game Management
- ✓ Standard chess notation input
- ✓ Move history tracking
- ✓ Material balance calculation
- ✓ Game status indicators (check, checkmate, stalemate)

### User Interface
- ✓ Clean, organized layout
- ✓ Responsive keyboard shortcuts
- ✓ Separate panels for different information
- ✓ Help system

## Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit the application |
| `r` | Reset | Start a new game |
| `u` | Undo | Take back the last move |
| `h` | Help | Show help information |
| `a` | Analyze | Quick position analysis |

## Usage Examples

### Making Moves
Simply type standard chess notation:
- `e4` - Move pawn to e4
- `Nf3` - Move knight to f3
- `O-O` - Castle kingside
- `Qxd5` - Queen captures on d5

### Asking Questions
Type natural language questions:
- "What's the best opening move?"
- "Analyze this position"
- "Explain the Sicilian Defense"
- "What should I play next?"
- "Is this move good?"

The AI assistant powered by Grok-4 and LangGraph will provide intelligent, educational responses to help improve your chess understanding.
