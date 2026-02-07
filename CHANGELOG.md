# Changelog

All notable changes to the ChessCode project will be documented in this file.

## [2.0.0] - 2025-02-07

### Major Changes
- **Complete migration from Streamlit to Textual TUI**
  - Replaced web-based UI with modern terminal user interface
  - Implemented interactive chessboard with Unicode pieces
  - Added keyboard shortcuts for common actions

### Added
- **New Agents Architecture**
  - `agents/chess_agent.py`: LangGraph-based AI agent for chess analysis
  - `agents/llm_provider.py`: XAI Grok-4 integration module
  - `agents/__init__.py`: Package initialization

- **Comprehensive Test Suite**
  - `tests/test_ui.py`: 13 comprehensive UI and agent tests
  - `tests/test_tui.py`: Board display and agent functionality tests
  - `tests/capture_screenshots.py`: Automated screenshot capture
  - `tests/demo_screenshots.py`: Demo screenshot generation

- **Documentation**
  - `docs/SCREENSHOTS.md`: Visual documentation with examples
  - `docs/PROJECT_SUMMARY.md`: Complete project overview
  - `docs/01_initial_state.svg`: Application screenshot
  - Text-based screenshots in `docs/screenshots/`

- **Main Application**
  - `chess_tui.py`: Main Textual TUI application
    - Interactive chessboard display
    - AI assistant chat interface
    - Move history tracking
    - Game status indicators
    - Keyboard shortcuts (q, r, u, h, a)

### Changed
- **Dependencies** (`requirements.txt`)
  - Removed: `streamlit`, `streamlit-chat`, `torch`, `sentence-transformers`, `faiss-cpu`, `Pillow`, `openai`
  - Added: `textual`, `langgraph`, `langchain-core`, `langchain-openai`
  - Kept: `python-chess`, `python-dotenv`

- **Project Structure**
  - Organized code into `agents/`, `tests/`, and `docs/` directories
  - Moved chess agent logic to dedicated agents module
  - Centralized all tests in tests/ folder
  - Placed all documentation in docs/ folder

- **Configuration**
  - Updated `.env.sample` with XAI configuration
  - Removed OpenAI and database dependencies
  - Simplified to single LLM provider (XAI Grok-4)

### Features
- **Interactive Chessboard**
  - Unicode chess pieces (♔ ♕ ♖ ♗ ♘ ♙)
  - 8x8 board with rank/file labels
  - Real-time board updates
  - Move highlighting

- **AI Assistant (LangGraph + Grok-4)**
  - Natural language question answering
  - Position analysis
  - Move suggestions with explanations
  - Strategic insights
  - Educational responses

- **Game Management**
  - Standard chess notation input (e4, Nf3, O-O)
  - Move history tracking
  - Undo functionality
  - Game reset
  - Material balance calculation
  - Check/checkmate/stalemate detection

- **User Interface**
  - Clean, organized layout
  - Separate panels for board, info, history, and chat
  - Responsive input handling
  - Keyboard shortcuts
  - Built-in help system

### Technical Details
- **LangGraph Integration**
  - StateGraph for conversation flow management
  - Async/await for smooth UI updates
  - Typed state dictionaries
  - Process query and generate response nodes

- **Textual Framework**
  - Reactive widgets
  - CSS-like styling
  - Event-driven architecture
  - Responsive layout system

### Testing
- All 13 tests passing
- Board creation and initialization
- Move validation and execution
- Game state detection (check, checkmate, stalemate)
- Material counting
- Unicode piece rendering
- FEN parsing
- Agent initialization and queries
- Position analysis

### Removed
- Streamlit web application components
- OpenAI GPT-4 integration (replaced with XAI Grok-4)
- Vector database dependencies (torch, faiss, sentence-transformers)
- Embedding utilities
- Database connection code

## [1.0.0] - Previous Version

### Features
- Streamlit-based web application
- Interactive chess board with drag-and-drop
- AI analysis powered by GPT-4
- Multiple AI personalities
- Save/load game functionality
- Move history tracking
- Position analysis and material balance

---

## Migration Guide (1.0 → 2.0)

### For Users
1. **Installation**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

2. **Configuration**
   - Copy `.env.sample` to `.env`
   - Add your XAI API key: `XAI_API_KEY=your-key-here`
   - Remove old OpenAI configuration

3. **Running the Application**
   - Old: `streamlit run Home.py`
   - New: `python3 chess_tui.py`

### For Developers
1. **Import Changes**
   - Old: `from chess_agent import ChessAgent`
   - New: `from agents.chess_agent import ChessAgent`

2. **LLM Provider**
   - Old: OpenAI GPT-4
   - New: XAI Grok-4 via `agents.llm_provider.LLMProvider`

3. **Testing**
   - Run tests: `python3 tests/test_ui.py`
   - All tests must pass before committing

### Breaking Changes
- Streamlit UI completely replaced with Textual TUI
- OpenAI dependency removed
- Vector database features removed
- API changed from web-based to terminal-based
