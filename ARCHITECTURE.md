# SkyTowers Architecture Documentation

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Three.js)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   App.jsx    │  │ GameScene.jsx│  │ Controls.jsx │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              REST API Endpoints                     │   │
│  │  /game/state, /game/move, /game/reset             │   │
│  │  /training/start, /training/stop                  │   │
│  │  /ws/training (WebSocket)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Game Engine & AI                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │   │
│  │  │ game.py  │  │ mcts.py  │  │model.py  │        │   │
│  │  └──────────┘  └──────────┘  └──────────┘        │   │
│  │  ┌──────────────────────────────────────────┐    │   │
│  │  │       trainer.py (Self-Play)            │    │   │
│  │  └──────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Persistent Storage                        │   │
│  │  ./checkpoints/best.pth.tar (Model weights)       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Architecture

#### App.jsx (Root Component)
- **Responsibilities**:
  - Global state management (gameState, mode, message, history)
  - API communication (axios)
  - WebSocket connection management
  - Mode switching (play vs. train)

- **State**:
  - `gameState`: Current board state
  - `mode`: 'play' or 'train'
  - `message`: Status message
  - `history`: Move history for training visualization
  - `ws`: WebSocket reference

- **Key Methods**:
  - `fetchState()`: Poll game state from backend
  - `startTraining()`: Initiate training session
  - `stopTraining()`: Stop training visualization
  - `handleMove()`: Process player move
  - `handleReset()`: Reset game

#### GameScene.jsx (Game Logic UI)
- **Responsibilities**:
  - Handle cell click events
  - Manage move/build phase selection
  - Validate UI interactions

- **State**:
  - `selectedPos`: Currently selected cell with phase info

- **Interaction Flow**:
  1. Click on player piece → select for move
  2. Click destination → move piece there, enter build phase
  3. Click build location → submit move

#### Board.jsx (3D Rendering)
- **Responsibilities**:
  - Render 5x5 grid with height visualization
  - Render player pieces with effects
  - Handle click interactions

- **Visual Elements**:
  - Base grid (gray, highlighted when selected)
  - Building blocks (white to blue gradient)
  - Domes (blue spheres with glow)
  - Player pieces (green and red spheres with emission)

#### Controls.jsx (UI Controls)
- **Responsibilities**:
  - Display action buttons
  - Switch between play and train modes

### Backend Architecture

#### game.py (Core Game Engine)
```
SkyTowersGame
├── __init__()
├── reset()
├── get_state() → np.ndarray (4, 5, 5)
├── get_valid_moves() → List[((r,c), (br,bc))]
├── step(action) → Optional[int]
├── is_terminal() → bool
└── getGameEnded() → int
```

**Key Features**:
- Comprehensive move validation
- State representation for neural network
- Terminal state detection
- Stalemate handling

**State Representation**:
- Channel 0: Player 1 position (one-hot)
- Channel 1: Player 2 position (one-hot)
- Channel 2: Board heights (normalized 0-1)
- Channel 3: Current player indicator

#### model.py (Neural Network)
```
SkyNet (nn.Module)
├── Shared Trunk (3 conv layers)
├── Policy Head
│   ├── Conv2d(64→2)
│   ├── FC(50→64)
│   └── Log-softmax
└── Value Head
    ├── Conv2d(64→1)
    ├── FC(25→64)
    ├── FC(64→1)
    └── Tanh
```

**Architecture Rationale**:
- Shared trunk extracts common features
- Policy head learns action distribution
- Value head estimates game outcome
- Log-softmax for numerical stability

#### mcts.py (Monte Carlo Tree Search)
```
MCTS
├── getActionProb(game_state, temp) → List[float]
├── search(game_state) → float
├── _expand_node(game_state, state_key) → float
├── _select_and_recurse(game_state, state_key) → float
├── _create_action_mask() → np.ndarray
├── _decode_action() → ((r,c), (br,bc))
└── stringRepresentation(game) → str
```

**Algorithm**:
1. **Selection**: Use UCB to traverse tree
2. **Expansion**: Evaluate leaf with neural network
3. **Backup**: Update statistics along path
4. **Action Selection**: Temperature-scaled probabilities

**UCB Formula**:
```
U(s,a) = Q(s,a) + cpuct * P(s,a) * sqrt(N(s)) / (1 + N(s,a))
```

#### trainer.py (Self-Play Training)
```
Trainer
├── execute_episode() → List[(state, pi, v)]
├── learn()
├── train(examples)
└── [Training Loop]
    ├── Self-play episode
    ├── Collect training data
    ├── Update neural network
    └── Save checkpoint
```

**Training Pipeline**:
1. Generate self-play episodes
2. Collect (state, policy, value) tuples
3. Train neural network on batch
4. Save best model checkpoint

#### server.py (REST API)
```
FastAPI App
├── ConnectionManager (WebSocket)
├── Endpoints
│   ├── GET /health
│   ├── GET /game/state
│   ├── POST /game/reset
│   ├── POST /game/move
│   ├── POST /training/start
│   ├── POST /training/stop
│   └── WS /ws/training
├── Background Tasks
│   └── broadcast_loop()
└── Helper Functions
    ├── run_training()
    └── _get_ai_move()
```

**Request/Response Flow**:
```
Client Request
    ↓
Validation & Error Handling
    ↓
Game Logic Execution
    ↓
AI Move Generation (if needed)
    ↓
State Update
    ↓
Response with Updated State
```

## Data Flow

### Play Mode
```
User Click
    ↓
GameScene.handleCellClick()
    ↓
App.handleMove() [HTTP POST]
    ↓
server.make_move()
    ├─ Validate move
    ├─ Execute player move
    ├─ Generate AI move (MCTS)
    ├─ Execute AI move
    └─ Return updated state
    ↓
App.setGameState()
    ↓
Board re-renders
```

### Training Mode
```
App.startTraining() [HTTP POST]
    ↓
server.start_training()
    ├─ Create training thread
    └─ Run trainer.learn()
    ↓
trainer.execute_episode()
    ├─ Self-play game
    ├─ Collect training data
    └─ Callback with state
    ↓
server.latest_training_state = state
    ↓
broadcast_loop() [async]
    ├─ Detect state change
    └─ WebSocket broadcast
    ↓
App.ws.onmessage
    ├─ Update gameState
    ├─ Update history
    └─ Re-render board
```

## State Management

### Frontend State
```javascript
{
  gameState: {
    board: [[...], ...],
    p1_pos: [r, c],
    p2_pos: [r, c],
    current_player: 1 | -1,
    winner: 1 | -1 | 0 | null,
    steps: number
  },
  mode: 'play' | 'train',
  message: string,
  history: [{player, move, build}, ...],
  ws: WebSocket | null
}
```

### Backend State
```python
{
  game: SkyTowersGame(),
  model: SkyNet(),
  mcts: MCTS(),
  training_active: bool,
  latest_training_state: dict | None
}
```

## Error Handling

### Frontend
- Try-catch blocks around API calls
- User-friendly error messages
- Graceful fallbacks

### Backend
- Input validation (Pydantic models)
- Exception logging
- HTTP error codes
- Fallback strategies (e.g., random move if AI fails)

## Performance Considerations

### Optimization Strategies
1. **MCTS Caching**: State hashing for tree reuse
2. **Batch Processing**: Neural network inference
3. **Async Operations**: Non-blocking training
4. **WebSocket Broadcasting**: Efficient state updates

### Bottlenecks
- MCTS simulations: ~50ms per move
- Neural network inference: ~10ms
- Game state serialization: ~1ms

## Extensibility Points

1. **Game Rules**: Modify `game.py` for variant rules
2. **Model Architecture**: Extend `model.py` with new layers
3. **MCTS Parameters**: Tune `Args` class in `mcts.py`
4. **Training Strategy**: Customize `trainer.py` loop
5. **UI Components**: Add new React components
6. **API Endpoints**: Extend `server.py` routes

## Testing Strategy

### Unit Tests
- Game move validation
- State representation
- MCTS action decoding
- Neural network forward pass

### Integration Tests
- API endpoint responses
- WebSocket communication
- Training pipeline
- Game completion scenarios

### Performance Tests
- MCTS simulation speed
- Model inference latency
- API response times
- Memory usage during training
