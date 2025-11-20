# SkyTowers: AI-Powered Game with MCTS and Neural Networks

A sophisticated implementation of the SkyTowers game (similar to Santorini) featuring:
- **Game Engine**: Full 5x5 board game with complex move validation
- **AI Opponent**: Monte Carlo Tree Search (MCTS) guided by a neural network
- **Self-Play Training**: Reinforcement learning through self-play episodes
- **Real-Time Visualization**: 3D interactive board using Three.js
- **WebSocket Training**: Live training visualization and monitoring

## Architecture Overview

### Backend (Python/FastAPI)
- **game.py**: Core game logic with state management and move validation
- **model.py**: Neural network architecture (SkyNet) for policy and value estimation
- **mcts.py**: Monte Carlo Tree Search implementation with neural network guidance
- **trainer.py**: Self-play training loop with experience collection
- **server.py**: FastAPI REST API with WebSocket support for real-time updates

### Frontend (React/Three.js)
- **App.jsx**: Main application component with game state management
- **GameScene.jsx**: 3D game board rendering and interaction
- **Board.jsx**: Individual cell rendering with visual effects
- **Controls.jsx**: UI controls for game actions
- **HistoryLog.jsx**: Training episode history display

## Game Rules

### Board
- 5x5 grid with height levels (0-4)
- Level 0: Ground
- Levels 1-3: Building blocks
- Level 4: Dome (winning position)

### Gameplay
1. **Move**: Player moves to an adjacent cell (including diagonals)
   - Can climb up to 1 level
   - Cannot move onto domes
   - Cannot move onto opponent

2. **Build**: After moving, player builds on an adjacent cell
   - Increases height by 1
   - Cannot build on occupied cells
   - Cannot build on domes

3. **Win Condition**: First player to reach level 3 wins

4. **Lose Condition**: Player with no valid moves loses

## Setup and Installation

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- PyTorch (with MPS support for Apple Silicon)
- FastAPI
- NumPy

### Frontend Setup

```bash
cd frontend
npm install
```

**Dependencies:**
- React 19+
- Three.js
- @react-three/fiber
- @react-three/drei
- Axios

## Running the Application

### Start Backend Server

```bash
cd backend
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5176` (Vite may use a different port if 5173 is occupied)

## API Endpoints

### Game Management
- `GET /health` - Health check
- `GET /game/state` - Get current game state
- `POST /game/reset` - Reset game to initial state
- `POST /game/move` - Make a player move

### Training
- `POST /training/start` - Start self-play training
- `POST /training/stop` - Stop training
- `WS /ws/training` - WebSocket for real-time training updates

## Game State Format

```json
{
  "board": [[0, 0, 0, 0, 0], ...],
  "p1_pos": [0, 0],
  "p2_pos": [4, 4],
  "current_player": 1,
  "winner": null,
  "steps": 0
}
```

## Move Format

```json
{
  "move_r": 1,
  "move_c": 1,
  "build_r": 2,
  "build_c": 2
}
```

## Training Configuration

Edit `backend/mcts.py` `Args` class to modify:
- `numMCTSSims`: Number of MCTS simulations per move (default: 25)
- `cpuct`: UCB exploration constant (default: 1.0)
- `lr`: Learning rate (default: 0.001)
- `epochs`: Training epochs per batch (default: 5)
- `batch_size`: Batch size for training (default: 64)
- `num_episodes`: Number of self-play episodes (default: 5)

## Model Architecture

### SkyNet Neural Network
- **Input**: 4-channel state tensor (5x5)
  - Channel 0: Player 1 position
  - Channel 1: Player 2 position
  - Channel 2: Board heights (normalized)
  - Channel 3: Current player indicator

- **Trunk**: 3 convolutional layers (64 channels each)

- **Policy Head**: Outputs probability distribution over 64 actions
  - 8 move directions × 8 build directions

- **Value Head**: Outputs game value estimate (-1 to 1)

## Action Space

Actions are encoded as: `action_idx = move_direction * 8 + build_direction`

**Directions (0-7):**
```
0: (-1, -1)  1: (-1, 0)  2: (-1, 1)
3: (0, -1)   [center]    4: (0, 1)
5: (1, -1)   6: (1, 0)   7: (1, 1)
```

## Performance Notes

- **MCTS Simulations**: 25-50 simulations per move provides good balance
- **Training Time**: ~5 episodes takes 5-10 minutes on Apple Silicon
- **Model Size**: ~500KB checkpoint
- **Inference**: ~50ms per move with MCTS

## Troubleshooting

### Model Not Loading
- Check checkpoint path in `server.py`
- Ensure checkpoint file exists: `./checkpoints/best.pth.tar`
- Model will initialize randomly if checkpoint not found

### WebSocket Connection Issues
- Ensure backend is running on port 8000
- Check CORS settings in `server.py`
- Verify WebSocket URL in frontend

### GPU/Device Issues
- MPS (Apple Silicon) is auto-detected
- Falls back to CPU if MPS unavailable
- Set `args.cuda = False` to force CPU

## Future Improvements

- [ ] Symmetry augmentation for training data
- [ ] Replay buffer for experience replay
- [ ] Parallel self-play episodes
- [ ] Better exploration strategies
- [ ] Evaluation metrics and statistics
- [ ] Model versioning and comparison
- [ ] Web-based training dashboard
- [ ] Mobile-responsive UI

## License

MIT

## Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- All functions have docstrings
- Error handling is comprehensive
- Logging is informative
