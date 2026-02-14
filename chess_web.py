#!/usr/bin/env python3
"""ChessCode Web - FastHTML chess application with multi-agent AI system.

Usage:
    python chess_web.py

Reuses all backend components (agents, router, tools, db) from the TUI version.
Runs on http://localhost:5001 by default.
"""
from fasthtml.common import *
import chess
import chess.svg
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────

BOARD_COLORS = {
    "square light": "#f0d9b5",
    "square dark": "#b58863",
    "margin": "#302e2b",
    "coord": "#e8e5e1",
}

AGENT_ALIASES = {
    "general": "general", "gen": "general", "db": "general",
    "coach": "children_coach", "child": "children_coach", "kids": "children_coach",
    "opening": "opening_teacher", "openings": "opening_teacher", "variation": "opening_teacher",
    "analyst": "player_analyst", "spy": "player_analyst", "pgn-spy": "player_analyst",
    "teacher": "personal_teacher", "personal": "personal_teacher", "improve": "personal_teacher",
    "engine": "engine", "stockfish": "engine", "sf": "engine",
    "auto": None,
}

HELP_TEXT = """Available commands:
  help (h, ?)       Show this help
  <move>            Make a chess move (e.g. e4, Nf3, O-O)
  analyze (a)       Analyze current position
  undo (u)          Take back last move
  reset (r)         Start a new game
  agents            List available AI agents
  agent <name>      Force a specific agent (or 'auto')
  cls               Clear chat

Or just type any question to ask the AI!

Agent aliases: general/gen, engine/stockfish/sf,
  coach/kids, opening/variation, analyst/spy, teacher/personal"""

# ─── CSS ─────────────────────────────────────────────────────────────────────

_css = Style("""
/* Layout */
.main-grid {
    display: grid;
    grid-template-columns: 440px 1fr;
    height: calc(100vh - 70px);
}
.board-panel {
    padding: 1rem;
    border-right: 1px solid var(--pico-muted-border-color);
    overflow-y: auto;
}
.chat-panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
}
#chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

/* Chat messages */
.msg {
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    font-size: 0.9rem;
    line-height: 1.6;
    max-width: 88%;
    white-space: pre-wrap;
    word-wrap: break-word;
}
.msg-user {
    background: var(--pico-primary-background);
    color: var(--pico-primary-inverse);
    align-self: flex-end;
    border-bottom-right-radius: 2px;
}
.msg-ai {
    background: var(--pico-card-background-color);
    border: 1px solid var(--pico-muted-border-color);
    align-self: flex-start;
    border-bottom-left-radius: 2px;
}
.msg-system {
    color: var(--pico-muted-color);
    font-style: italic;
    font-size: 0.85rem;
    align-self: center;
    text-align: center;
}
.msg-label {
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.2rem;
    opacity: 0.7;
}

/* Input form */
#input-form {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--pico-muted-border-color);
    display: flex;
    gap: 0.5rem;
    align-items: center;
}
#input-form input { flex: 1; margin: 0; }
#input-form button[type="submit"] { margin: 0; width: auto; white-space: nowrap; }

/* Board */
#board-svg svg {
    width: 100%;
    max-width: 400px;
    height: auto;
    border-radius: 4px;
}

/* Info cards */
.info-card, .move-history {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    border: 1px solid var(--pico-muted-border-color);
    border-radius: 8px;
    background: var(--pico-card-background-color);
}
.info-card h4, .move-history h4 {
    margin: 0 0 0.5rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.6;
}
.info-card p { margin: 0.2rem 0; font-size: 0.85rem; }
.move-history { max-height: 200px; overflow-y: auto; }
.move-pair {
    display: inline-block;
    margin: 0.1rem 0.75rem 0.1rem 0;
    font-family: var(--pico-font-family-monospace);
    font-size: 0.85rem;
}

/* Agent badge */
.agent-badge {
    display: inline-block;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--pico-primary);
    color: var(--pico-primary-inverse);
}

/* Action buttons */
.action-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.75rem;
}
.action-buttons button {
    flex: 1;
    padding: 0.4rem 0.5rem;
    font-size: 0.8rem;
    margin: 0;
}

/* Spinner */
#spinner {
    display: none;
    width: 18px; height: 18px;
    border: 2px solid transparent;
    border-top: 2px solid var(--pico-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
.htmx-request #spinner { display: inline-block !important; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Responsive */
@media (max-width: 900px) {
    .main-grid { grid-template-columns: 1fr; height: auto; }
    .board-panel { border-right: none; border-bottom: 1px solid var(--pico-muted-border-color); }
    .chat-panel { height: 60vh; }
    #board-svg svg { max-width: 320px; margin: 0 auto; display: block; }
}
""")

# ─── Client JS ───────────────────────────────────────────────────────────────

_js = Script("""
// Dark theme (runs before body paint)
document.documentElement.setAttribute('data-theme', 'dark');

// Auto-scroll chat + clear input after HTMX requests
document.addEventListener('htmx:afterSwap', function(e) {
    var c = document.getElementById('chat-messages');
    if (c) c.scrollTop = c.scrollHeight;
});
document.addEventListener('htmx:afterRequest', function(e) {
    var f = document.getElementById('input-form');
    if (f) {
        var i = f.querySelector('input[name="user_input"]');
        if (i) { i.value = ''; i.focus(); }
    }
});
""")

# ─── App ─────────────────────────────────────────────────────────────────────

app, rt = fast_app(
    hdrs=(_css, _js),
    secret_key=os.getenv("SECRET_KEY", "chesscode-dev-key"),
)

# ─── Router (lazy singleton, shared across sessions) ─────────────────────────

_router = None


def get_router():
    global _router
    if _router is not None:
        return _router
    try:
        from agents.router import Router
        from agents.general_agent import GeneralAgent
        from agents.engine_agent import EngineAgent
        from agents.children_coach import ChildrenCoachAgent
        from agents.opening_teacher import OpeningTeacherAgent
        from agents.player_analyst import PlayerAnalystAgent
        from agents.personal_teacher import PersonalTeacherAgent

        agents = {
            "general": GeneralAgent(),
            "engine": EngineAgent(),
            "children_coach": ChildrenCoachAgent(),
            "opening_teacher": OpeningTeacherAgent(),
            "player_analyst": PlayerAnalystAgent(),
            "personal_teacher": PersonalTeacherAgent(),
        }
        _router = Router(agents)
        print(f"Agent system ready: {', '.join(agents.keys())}")
    except Exception as e:
        print(f"Warning: Agent init failed: {e}")
    return _router


# ─── Session state ───────────────────────────────────────────────────────────


class GameState:
    def __init__(self):
        self.board = chess.Board()
        self.move_count = 1
        self.messages = []
        self.active_agent = "Auto"
        model = os.getenv("MODEL", "grok-4-fast-reasoning")
        provider = os.getenv("MODEL_PROVIDER", "xai")
        self.add("system", f"ChessCode Web — {model} ({provider})")
        self.add("system", "Type 'help' for commands, a chess move, or any question.")

    def add(self, role, text, agent=None):
        self.messages.append({"role": role, "text": text, "agent": agent})


_sessions = {}


def get_game(sess):
    sid = sess.get("sid")
    if not sid:
        sid = str(uuid.uuid4())
        sess["sid"] = sid
    if sid not in _sessions:
        _sessions[sid] = GameState()
    return _sessions[sid]


# ─── UI Components ───────────────────────────────────────────────────────────


def BoardSvg(board, last_move=None, oob=False):
    kw = dict(size=400, colors=BOARD_COLORS, coordinates=True)
    if last_move:
        kw["lastmove"] = last_move
    if board.is_check():
        kw["check"] = board.king(board.turn)
    attrs = dict(id="board-svg")
    if oob:
        attrs["hx_swap_oob"] = "true"
    return Div(Safe(chess.svg.board(board, **kw)), **attrs)


def GameInfoCard(board, active_agent="Auto", oob=False):
    turn = "White" if board.turn else "Black"
    if board.is_checkmate():
        status = f"Checkmate! {'Black' if board.turn else 'White'} wins!"
    elif board.is_stalemate():
        status = "Stalemate"
    elif board.is_check():
        status = "Check!"
    elif board.is_insufficient_material():
        status = "Draw (insufficient material)"
    else:
        status = "In progress"

    w = sum(
        len(board.pieces(pt, chess.WHITE)) * v
        for pt, v in [(1, 1), (2, 3), (3, 3), (4, 5), (5, 9)]
    )
    b = sum(
        len(board.pieces(pt, chess.BLACK)) * v
        for pt, v in [(1, 1), (2, 3), (3, 3), (4, 5), (5, 9)]
    )
    d = w - b
    mat = f"White +{d}" if d > 0 else f"Black +{abs(d)}" if d < 0 else "Equal"

    attrs = dict(cls="info-card", id="game-info")
    if oob:
        attrs["hx_swap_oob"] = "true"
    return Div(
        H4("Game Info"),
        P(Strong("Turn: "), turn),
        P(Strong("Status: "), status),
        P(Strong("Material: "), mat),
        P(Strong("Agent: "), Span(active_agent, cls="agent-badge")),
        **attrs,
    )


def MoveHistoryCard(board, oob=False):
    moves = []
    temp = chess.Board()
    for m in board.move_stack:
        moves.append(temp.san(m))
        temp.push(m)

    pairs = []
    for i in range(0, len(moves), 2):
        w_move = moves[i]
        b_move = moves[i + 1] if i + 1 < len(moves) else "..."
        pairs.append(Span(f"{i // 2 + 1}. {w_move} {b_move}", cls="move-pair"))

    if not pairs:
        pairs = [Small("No moves yet", style="opacity:0.5")]

    attrs = dict(cls="move-history", id="move-history")
    if oob:
        attrs["hx_swap_oob"] = "true"
    return Div(H4("Moves"), *pairs, **attrs)


def ChatMsg(msg):
    role, text, agent = msg["role"], msg["text"], msg.get("agent")
    if role == "system":
        return Div(text, cls="msg msg-system")
    elif role == "user":
        return Div(Div("You", cls="msg-label"), text, cls="msg msg-user")
    else:
        label = f"AI · {agent}" if agent else "AI"
        return Div(Div(label, cls="msg-label"), text, cls="msg msg-ai")


def InputForm():
    return Form(
        Input(
            name="user_input",
            placeholder="Type move, command, or question...",
            autofocus=True,
            autocomplete="off",
        ),
        Button("Send", type="submit"),
        Span(id="spinner"),
        id="input-form",
        hx_post="/send",
        hx_target="#chat-messages",
        hx_swap="innerHTML",
        hx_indicator="#spinner",
    )


def ActionButtons():
    a = dict(
        hx_post="/send",
        hx_target="#chat-messages",
        hx_swap="innerHTML",
        hx_indicator="#spinner",
    )
    return Div(
        Button(
            "New Game",
            hx_vals='{"user_input":"reset"}',
            cls="secondary outline",
            **a,
        ),
        Button(
            "Undo", hx_vals='{"user_input":"undo"}', cls="secondary outline", **a
        ),
        Button(
            "Analyze",
            hx_vals='{"user_input":"analyze"}',
            cls="contrast outline",
            **a,
        ),
        cls="action-buttons",
    )


# ─── Routes ──────────────────────────────────────────────────────────────────


@rt
def index(sess):
    game = get_game(sess)
    return (
        Title("ChessCode"),
        Nav(
            Ul(Li(Strong("♟ ChessCode"), Small(" Web", style="opacity:0.5"))),
            Ul(
                Li(
                    Small(
                        f"{os.getenv('MODEL', 'grok-4')} · {os.getenv('MODEL_PROVIDER', 'xai')}",
                        style="opacity:0.5",
                    )
                ),
            ),
            cls="container-fluid",
        ),
        Main(
            Div(
                # Left: Board panel
                Div(
                    BoardSvg(game.board),
                    ActionButtons(),
                    GameInfoCard(game.board, game.active_agent),
                    MoveHistoryCard(game.board),
                    cls="board-panel",
                ),
                # Right: Chat panel
                Div(
                    Div(
                        *[ChatMsg(m) for m in game.messages],
                        id="chat-messages",
                    ),
                    InputForm(),
                    cls="chat-panel",
                ),
                cls="main-grid",
            ),
            cls="container-fluid",
        ),
    )


@rt
async def send(sess, user_input: str):
    game = get_game(sess)
    raw = user_input.strip()
    if not raw:
        return tuple(ChatMsg(m) for m in game.messages)

    cmd = raw.lower()
    oob = []

    # ── Commands ──────────────────────────────────────────────────
    if cmd in ("help", "h", "?"):
        game.add("system", HELP_TEXT)

    elif cmd in ("reset", "r", "new", ".."):
        game.board = chess.Board()
        game.move_count = 1
        game.add("system", "New game started.")
        oob = _board_oob(game)

    elif cmd in ("undo", "u"):
        if game.board.move_stack:
            game.board.pop()
            game.add("system", "Move undone.")
            oob = _board_oob(game)
        else:
            game.add("system", "No moves to undo.")

    elif cmd in ("analyze", "a"):
        game.add("user", "Analyze the current position")
        await _ask_ai(
            game,
            "Analyze the current position in detail. What are the key features and best plans?",
        )
        oob.append(GameInfoCard(game.board, game.active_agent, oob=True))

    elif cmd in ("cls", "clear"):
        game.messages = []

    elif cmd == "agents":
        router = get_router()
        if router:
            names = ", ".join(router.agents.keys())
            game.add(
                "system",
                f"Available agents: {names}\nUse 'agent <name>' to force one, 'agent auto' to reset.",
            )
        else:
            game.add("system", "Agent system not available.")

    elif cmd.startswith("agent "):
        _handle_agent_cmd(game, cmd.split(None, 1)[1].strip())
        oob.append(GameInfoCard(game.board, game.active_agent, oob=True))

    # ── Move or question ──────────────────────────────────────────
    else:
        if _looks_like_move(raw):
            if _try_move(game, raw):
                oob = _board_oob(game)
            else:
                game.add("system", f"Invalid or illegal move: {raw}")
        else:
            game.add("user", raw)
            await _ask_ai(game, raw)
            oob.append(GameInfoCard(game.board, game.active_agent, oob=True))

    msgs = [ChatMsg(m) for m in game.messages]
    return tuple(msgs + oob)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _looks_like_move(text):
    """Heuristic: does this look like a chess move (not a question)?"""
    t = text.strip()
    if len(t) > 8 or len(t) < 2:
        return False
    if t.startswith(("O-O", "0-0")):
        return True
    clean = t.replace("+", "").replace("#", "").replace("x", "").replace("=", "")
    if clean and clean[0] in "abcdefghNBRQK" and any(
        c in "12345678" for c in clean
    ):
        return True
    return False


def _try_move(game, move_str):
    """Try to parse and execute a chess move. Returns True on success."""
    try:
        move = game.board.parse_san(move_str)
    except Exception:
        return False

    san = game.board.san(move)
    game.board.push(move)
    if not game.board.turn:
        game.move_count += 1

    game.add("system", f"♟ {san}")

    if game.board.is_checkmate():
        winner = "Black" if game.board.turn else "White"
        game.add("system", f"Checkmate! {winner} wins!")
    elif game.board.is_stalemate():
        game.add("system", "Stalemate — draw.")
    elif game.board.is_check():
        game.add("system", "Check!")
    return True


async def _ask_ai(game, question):
    """Send a question to the multi-agent router."""
    router = get_router()
    if not router:
        game.add("system", "Agent system not available. Check server logs.")
        return
    try:
        history = [str(m) for m in game.board.move_stack]
        response = await router.query(question, game.board.fen(), history)
        agent = router.last_agent_name
        game.active_agent = agent
        game.add("ai", response, agent=agent)
    except Exception as e:
        game.add("system", f"Error: {e}")


def _handle_agent_cmd(game, alias):
    """Handle 'agent <name>' command."""
    resolved = AGENT_ALIASES.get(alias, alias)
    router = get_router()

    if resolved is None:
        if router:
            router.clear_forced_agent()
        game.active_agent = "Auto"
        game.add("system", "Routing reset to automatic.")
    elif router and router.force_agent(resolved):
        game.active_agent = resolved
        game.add("system", f"Next query will use: {resolved}")
    else:
        game.add("system", f"Unknown agent: {alias}")


def _board_oob(game):
    """Return OOB swap elements for board, game info, and move history."""
    last = game.board.peek() if game.board.move_stack else None
    return [
        BoardSvg(game.board, last_move=last, oob=True),
        GameInfoCard(game.board, game.active_agent, oob=True),
        MoveHistoryCard(game.board, oob=True),
    ]


# ─── Entry point ─────────────────────────────────────────────────────────────

serve(port=int(os.getenv("PORT", 5001)))
