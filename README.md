# ChessCode - Interactive Chess TUI

An interactive terminal-based chess application built with Textual, featuring an AI assistant powered by LangGraph and Grok-4 for intelligent analysis and free-form question answering.

This project migrates the original Streamlit-based `chesscode` application to a modern, responsive terminal user interface (TUI).

## Features

- **Interactive Terminal UI**: A fully interactive chessboard experience in your terminal, built with the Textual framework.
- **AI-Powered Analysis**: Get strategic insights and move suggestions from an AI assistant powered by Grok-4 and LangGraph.
- **Free-Form Questions**: Ask any question about the current position, chess strategy, or openings in natural language.
- **Real-Time Game State**: Keep track of whose turn it is, game status (check, checkmate), and material advantage.
- **Move History**: View a complete history of all moves made in the current game.
- **Keyboard Shortcuts**: Use convenient shortcuts for common actions like resetting the game, undoing moves, and getting help.

## Screenshots

Here are some text-based screenshots demonstrating the TUI in action:

**1. Initial Board State**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ChessCode - Interactive Chess TUI                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Chess Board                          │  AI Assistant                        ║
║  ┌─────────────────────────────────┐  │                                      ║
║8 │ ♜  ♞  ♝  ♛  ♚  ♝  ♞  ♜  │         │  AI Assistant ready!                 ║
║7 │ ♟  ♟  ♟  ♟  ♟  ♟  ♟  ♟  │         │  Ask me anything about chess.        ║
║6 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │                                      ║
║5 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │  Try: 'What's the best opening       ║
║4 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │  move?' or 'Analyze this position'   ║
║3 │ ·  ·  ·  ·  ·  ·  ·  ·  │         │                                      ║
║2 │ ♙  ♙  ♙  ♙  ♙  ♙  ♙  ♙  │         │                                      ║
║1 │ ♖  ♘  ♗  ♕  ♔  ♗  ♘  ♖  │         │                                      ║
║  └─────────────────────────────────┘  │                                      ║
║    a   b   c   d   e   f   g   h      │                                      ║
║                                        │                                      ║
║  Game Status                           │  Move History                        ║
║  Turn: White                           │  No moves yet                        ║
║  Status: Active                        │                                      ║
║  Material: Equal                       │                                      ║
║                                        │                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Enter move (e.g., 'e4', 'Nf3') or ask a question...                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ q: Quit │ r: Reset │ u: Undo │ h: Help │ a: Analyze Position                ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**2. AI Analysis in Action**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ChessCode - Interactive Chess TUI                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Chess Board                          │  AI Assistant                        ║
║  ┌─────────────────────────────────┐  │                                      ║
║8 │ ♜  ·  ♝  ♛  ♚  ♝  ♞  ♜  │         │  You: What should I play next?       ║
║7 │ ♟  ♟  ♟  ♟  ·  ♟  ♟  ♟  │         │                                      ║
║6 │ ·  ·  ♞  ·  ·  ·  ·  ·  │         │  AI: This is a standard Italian      ║
║5 │ ·  ·  ·  ·  ♟  ·  ·  ·  │         │  Game opening. White has several     ║
║4 │ ·  ·  ·  ·  ♙  ·  ·  ·  │         │  strong options:                     ║
║3 │ ·  ·  ·  ·  ·  ♘  ·  ·  │         │                                      ║
║2 │ ♙  ♙  ♙  ♙  ·  ♙  ♙  ♙  │         │  1. Bc4 - Develops the bishop to    ║
║1 │ ♖  ♘  ♗  ♕  ♔  ♗  ·  ♖  │         │     an active square, attacking f7   ║
║  └─────────────────────────────────┘  │                                      ║
║    a   b   c   d   e   f   g   h      │  2. Bb5 - The Ruy Lopez, one of     ║
║                                        │     the most popular openings        ║
║  Game Status                           │                                      ║
║  Turn: White                           │  3. d4 - Challenging the center      ║
║  Status: Active                        │     immediately                      ║
║  Material: Equal                       │                                      ║
║                                        │  I recommend Bc4 for a classical     ║
║                                        │  Italian Game setup.                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Enter move (e.g., 'e4', 'Nf3') or ask a question...                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ q: Quit │ r: Reset │ u: Undo │ h: Help │ a: Analyze Position                ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kaljuvee/chesscode.git
    cd chesscode
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**
    Create a `.env` file in the root of the project and add your XAI API key:
    ```env
    # LLM Provider Configuration
    MODEL_PROVIDER=xai
    MODEL=grok-4-fast-reasoning
    XAI_API_KEY=your-xai-api-key-here
    ```

## Usage

Run the Textual TUI application:

```bash
python3 chess_tui.py
```

-   **Make moves** by typing standard chess notation (e.g., `e4`, `Nf3`, `O-O`) and pressing Enter.
-   **Ask questions** in natural language (e.g., `analyze this position`, `what is the best move?`).

## Project Structure

```
chesscode/
├── chess_agent.py      # Core LangGraph agent for chess analysis
├── chess_tui.py        # Main Textual TUI application
├── llm_provider.py     # XAI (Grok) integration
├── requirements.txt    # Python dependencies
├── .env                # Environment configuration (not in version control)
└── README.md           # This file
```

## Architecture

The application's intelligence is powered by a `ChessAgent` built with **LangGraph**. This agent processes user queries, analyzes the current board state, and uses the **Grok-4** model from **xAI** to generate insightful and educational responses.

The user interface is built with **Textual**, a modern TUI framework for Python, providing a responsive and interactive experience directly in the terminal.

## Contributing

1.  Fork the repository
2.  Create a feature branch (`git checkout -b feature/your-feature`)
3.  Commit your changes (`git commit -am 'Add some feature'`)
4.  Push to the branch (`git push origin feature/your-feature`)
5.  Create a new Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
