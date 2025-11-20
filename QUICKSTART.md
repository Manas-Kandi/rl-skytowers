# Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Step 1: Clone and Navigate
```bash
cd 9xf
```

### Step 2: Backend Setup (Terminal 1)
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Frontend Setup (Terminal 2)
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

You should see:
```
VITE v7.2.4  ready in 123 ms

➜  Local:   http://localhost:5173/
```

### Step 4: Open in Browser
Navigate to `http://localhost:5173/`

## Playing the Game

### Game Controls
1. **Click your piece** (green sphere) to select it
2. **Click destination** to move there
3. **Click build location** to build a tower
4. **AI responds** automatically

### Winning
- First to reach a level 3 tower wins
- If you have no valid moves, you lose

## Training the AI

1. Click **"Start Training"** button
2. Watch the AI play against itself
3. The board updates in real-time
4. Training history shows on the right
5. Click **"Stop Watching"** to return to play mode

## Common Issues

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process if needed
kill -9 <PID>
```

### Frontend won't connect
- Ensure backend is running on port 8000
- Check browser console for errors (F12)
- Try refreshing the page

### GPU/Device errors
- The app auto-detects Apple Silicon (MPS)
- Falls back to CPU automatically
- No action needed

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [DEVELOPMENT.md](DEVELOPMENT.md) for development guide

## File Structure Reference

```
9xf/
├── backend/          # Python FastAPI server
│   ├── game.py      # Game logic
│   ├── model.py     # Neural network
│   ├── mcts.py      # AI algorithm
│   ├── trainer.py   # Training loop
│   └── server.py    # REST API
├── frontend/        # React app
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   └── package.json
└── checkpoints/     # Saved models
```

## API Quick Reference

### Play a Move
```bash
curl -X POST http://localhost:8000/game/move \
  -H "Content-Type: application/json" \
  -d '{"move_r": 1, "move_c": 1, "build_r": 2, "build_c": 2}'
```

### Get Game State
```bash
curl http://localhost:8000/game/state
```

### Reset Game
```bash
curl -X POST http://localhost:8000/game/reset
```

### Start Training
```bash
curl -X POST http://localhost:8000/training/start
```

## Tips

- **Stronger AI**: Increase `numMCTSSims` in `backend/mcts.py` (default: 25)
- **Faster Training**: Decrease `num_episodes` in `backend/mcts.py` (default: 5)
- **Better Model**: Train longer or increase `batch_size`
- **Debug**: Check browser console (F12) and backend logs

## Performance

- **First move**: ~2 seconds (model loading)
- **Subsequent moves**: ~1-2 seconds (MCTS)
- **Training episode**: ~2-3 minutes
- **Full training**: ~10-15 minutes (5 episodes)

Enjoy playing SkyTowers! 🎮
