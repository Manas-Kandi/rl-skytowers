# Development Guide

## Project Structure

```
9xf/
├── backend/
│   ├── game.py           # Core game engine
│   ├── model.py          # Neural network (SkyNet)
│   ├── mcts.py           # MCTS implementation
│   ├── trainer.py        # Self-play training
│   ├── server.py         # FastAPI server
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Root component
│   │   ├── main.jsx      # Entry point
│   │   ├── index.css     # Global styles
│   │   └── components/
│   │       ├── GameScene.jsx
│   │       ├── Board.jsx
│   │       ├── Controls.jsx
│   │       └── HistoryLog.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── checkpoints/          # Model weights
├── README.md
├── ARCHITECTURE.md
└── DEVELOPMENT.md
```

## Code Style Guide

### Python
- Follow PEP 8
- Use type hints for function signatures
- Add docstrings to all functions and classes
- Use logging instead of print statements
- Keep functions focused and modular

**Example**:
```python
def get_valid_moves(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Get all valid moves for the current player.
    
    Returns:
        List of tuples: [((move_r, move_c), (build_r, build_c)), ...]
    """
    # Implementation
```

### JavaScript/React
- Use functional components with hooks
- Use camelCase for variables and functions
- Use PascalCase for components
- Add JSDoc comments for complex logic
- Keep components focused on single responsibility

**Example**:
```javascript
/**
 * Renders a single cell on the game board
 * @param {number} r - Row index
 * @param {number} c - Column index
 * @param {number} height - Cell height
 */
const Cell = ({ r, c, height, onClick, isP1, isP2, isSelected, isTarget }) => {
  // Implementation
};
```

## Development Workflow

### Setting Up Development Environment

1. **Clone and navigate**:
```bash
cd 9xf
```

2. **Backend setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend setup**:
```bash
cd ../frontend
npm install
```

### Running in Development Mode

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### Making Changes

#### Backend Changes
1. Edit relevant `.py` file
2. Server auto-reloads with `--reload` flag
3. Test via API or frontend
4. Check logs for errors

#### Frontend Changes
1. Edit relevant `.jsx` or `.css` file
2. Vite hot-reloads automatically
3. Check browser console for errors
4. Verify API communication

## Common Development Tasks

### Adding a New Game Feature

1. **Update game.py**:
   - Modify `get_valid_moves()` if move rules change
   - Update `step()` for new mechanics
   - Adjust `get_state()` if state representation changes

2. **Update model.py** (if needed):
   - Modify input channels if state changes
   - Adjust output size if action space changes

3. **Update frontend**:
   - Modify `Board.jsx` for visual changes
   - Update `GameScene.jsx` for interaction changes

4. **Test**:
   - Verify move validation
   - Check game completion
   - Test edge cases

### Adding a New API Endpoint

1. **Define request model** in `server.py`:
```python
class NewRequest(BaseModel):
    field1: int
    field2: str
```

2. **Create endpoint**:
```python
@app.post("/path/endpoint")
def endpoint_name(request: NewRequest):
    """Endpoint description."""
    try:
        # Implementation
        return {"result": value}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error message")
```

3. **Update frontend** to call new endpoint:
```javascript
const response = await axios.post(`${API_URL}/path/endpoint`, data);
```

### Modifying Neural Network Architecture

1. **Edit model.py**:
```python
class SkyNet(nn.Module):
    def __init__(self, ...):
        # Add new layers
        self.new_layer = nn.Conv2d(...)
    
    def forward(self, x):
        # Use new layers
        x = self.new_layer(x)
        return p, v
```

2. **Update input/output handling** in `mcts.py` if needed

3. **Retrain model**:
```bash
cd backend
python trainer.py
```

### Adjusting MCTS Parameters

Edit `backend/mcts.py` `Args` class:
```python
class Args:
    def __init__(self):
        self.numMCTSSims = 50  # Increase for stronger AI
        self.cpuct = 1.5       # Increase for more exploration
        # ... other parameters
```

## Debugging

### Backend Debugging

**Enable verbose logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Add debug prints**:
```python
logger.debug(f"Variable value: {var}")
```

**Use Python debugger**:
```python
import pdb; pdb.set_trace()
```

### Frontend Debugging

**Browser DevTools**:
- F12 to open developer tools
- Console tab for errors
- Network tab for API calls
- React DevTools extension

**Add debug logs**:
```javascript
console.log("Debug info:", variable);
console.error("Error:", error);
```

## Testing

### Manual Testing Checklist

- [ ] Game starts correctly
- [ ] Valid moves are accepted
- [ ] Invalid moves are rejected
- [ ] Win condition triggers
- [ ] Lose condition triggers
- [ ] Draw condition triggers
- [ ] AI makes reasonable moves
- [ ] Training starts and completes
- [ ] WebSocket updates work
- [ ] UI responds to game state changes

### Performance Testing

**Measure MCTS speed**:
```python
import time
start = time.time()
# MCTS operation
elapsed = time.time() - start
print(f"Time: {elapsed:.3f}s")
```

**Profile neural network**:
```python
import torch.profiler as profiler
with profiler.profile(...) as prof:
    output = model(input_tensor)
```

## Deployment

### Backend Deployment

1. **Production server**:
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

2. **Environment variables**:
```bash
export CHECKPOINT_DIR=/path/to/checkpoints
export LOG_LEVEL=INFO
```

### Frontend Deployment

1. **Build**:
```bash
npm run build
```

2. **Deploy dist/ folder** to static hosting (Netlify, Vercel, etc.)

3. **Update API_URL** in `App.jsx` for production

## Troubleshooting

### Backend Issues

**Port already in use**:
```bash
lsof -i :8000  # Find process
kill -9 <PID>  # Kill process
```

**Module import errors**:
```bash
pip install -r requirements.txt --upgrade
```

**Model loading fails**:
- Check checkpoint path
- Verify file permissions
- Ensure PyTorch version compatibility

### Frontend Issues

**CORS errors**:
- Verify backend CORS settings
- Check API_URL matches backend host

**WebSocket connection fails**:
- Ensure backend is running
- Check WS_URL in App.jsx
- Verify firewall settings

**Blank 3D canvas**:
- Check browser console for errors
- Verify Three.js is loaded
- Check camera position

## Performance Optimization

### Backend Optimization
1. Increase MCTS simulations for stronger AI
2. Use batch processing for neural network
3. Cache game states to avoid recomputation
4. Profile code to find bottlenecks

### Frontend Optimization
1. Memoize expensive computations
2. Use React.memo for components
3. Optimize 3D rendering (reduce geometry complexity)
4. Lazy load components

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes following style guide
3. Test thoroughly
4. Commit with clear messages: `git commit -m "Add feature description"`
5. Push and create pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Three.js Documentation](https://threejs.org/docs/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [MCTS Algorithm](https://en.wikipedia.org/wiki/Monte_Carlo_tree_search)
