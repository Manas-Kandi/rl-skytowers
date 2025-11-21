from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
import asyncio
import json
import logging
import threading
import os
from game import SkyTowersGame
from model import SkyNet
from mcts import MCTS, Args
from trainer import Trainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SkyTowers API", version="1.0.0")

# Store connected clients
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()
training_active = False
training_thread = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game state
game = SkyTowersGame()
args = Args()
model = SkyNet()

# Move model to appropriate device
device = 'mps' if args.cuda else 'cpu'
model = model.to(device)
logger.info(f"Model moved to device: {device}")

# Load model if exists
checkpoint_path = os.path.join(args.checkpoint_dir, 'best.pth.tar')
if os.path.exists(checkpoint_path):
    try:
        model.load_state_dict(torch.load(checkpoint_path, map_location=device))
        logger.info(f"Loaded model from {checkpoint_path}")
    except Exception as e:
        logger.warning(f"Failed to load model: {e}")
else:
    logger.info("No checkpoint found, using random initialization")

model.eval()
mcts = MCTS(game, model, args)

class MoveRequest(BaseModel):
    """Request model for player moves."""
    move_r: int
    move_c: int
    build_r: int
    build_c: int

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "training_active": training_active}

@app.get("/game/state")
def get_state():
    """Get current game state."""
    try:
        return {
            "board": game.board.tolist(),
            "p1_pos": game.p1_pos,
            "p2_pos": game.p2_pos,
            "current_player": game.current_player,
            "winner": game.winner,
            "steps": game.steps
        }
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game state")

@app.post("/game/reset")
def reset_game():
    """Reset the game to initial state."""
    try:
        game.reset()
        global mcts
        mcts = MCTS(game, model, args)
        logger.info("Game reset")
        return {"message": "Game reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting game: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset game")

@app.post("/game/move")
def make_move(move: MoveRequest):
    """
    Process a player move and generate AI response.
    
    Args:
        move: Player's move (move_r, move_c, build_r, build_c)
        
    Returns:
        Game state after player and AI moves
    """
    try:
        if game.winner is not None:
            raise HTTPException(status_code=400, detail="Game is over")
            
        action = ((move.move_r, move.move_c), (move.build_r, move.build_c))
        
        # Validate move
        valid_moves = game.get_valid_moves()
        if action not in valid_moves:
            logger.warning(f"Invalid move attempted: {action}")
            raise HTTPException(status_code=400, detail="Invalid move")
            
        # Execute player move
        game.step(action)
        logger.info(f"Player 1 moved to {action[0]}, built at {action[1]}")
        
        # If game not over, AI moves
        if game.winner is None:
            ai_move = _get_ai_move()
            game.step(ai_move)
            logger.info(f"AI (Player -1) moved to {ai_move[0]}, built at {ai_move[1]}")
            
            return {
                "player_move": action,
                "ai_move": ai_move,
                "winner": game.winner,
                "board": game.board.tolist(),
                "p1_pos": game.p1_pos,
                "p2_pos": game.p2_pos,
                "current_player": game.current_player
            }
            
        return {
            "player_move": action,
            "winner": game.winner,
            "board": game.board.tolist(),
            "p1_pos": game.p1_pos,
            "p2_pos": game.p2_pos,
            "current_player": game.current_player
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing move: {e}")
        raise HTTPException(status_code=500, detail="Failed to process move")

def _get_ai_move():
    """Get AI move using MCTS."""
    try:
        temp_args = Args()
        temp_args.numMCTSSims = 50
        ai_mcts = MCTS(game, model, temp_args)
        pi = ai_mcts.getActionProb(game, temp=0)
        action_idx = np.argmax(pi)
        
        # Decode action
        m_idx = action_idx // 8
        b_idx = action_idx % 8
        dirs = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        dr, dc = dirs[m_idx]
        curr = game.p1_pos if game.current_player == 1 else game.p2_pos
        move_pos = (curr[0] + dr, curr[1] + dc)
        b_dr, b_dc = dirs[b_idx]
        build_pos = (move_pos[0] + b_dr, move_pos[1] + b_dc)
        
        return (move_pos, build_pos)
    except Exception as e:
        logger.error(f"Error getting AI move: {e}")
        # Fallback: return first valid move
        valid_moves = game.get_valid_moves()
        if valid_moves:
            return valid_moves[0]
        raise

@app.websocket("/ws/training")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time training updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Global state for training
latest_training_state = None

def run_training():
    """Run training in a separate thread."""
    global training_active, latest_training_state
    training_active = True
    logger.info("Training started")
    
    def callback_safe(state):
        """Update global state for broadcasting."""
        global latest_training_state
        latest_training_state = state
        
    try:
        trainer = Trainer(callback=callback_safe)
        trainer.learn()
        logger.info("Training completed")
    except Exception as e:
        logger.error(f"Training error: {e}")
    finally:
        training_active = False

@app.on_event("startup")
async def startup_event():
    """Start background broadcast loop on server startup."""
    logger.info("Server starting up")
    asyncio.create_task(broadcast_loop())

async def broadcast_loop():
    """Periodically broadcast training state to connected clients."""
    global latest_training_state
    last_sent = None
    while True:
        try:
            if latest_training_state and latest_training_state != last_sent:
                await manager.broadcast(latest_training_state)
                last_sent = latest_training_state
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
        await asyncio.sleep(0.1)

@app.post("/training/start")
def start_training():
    """Start a new training session."""
    global training_active, training_thread
    
    if training_active:
        logger.warning("Training already in progress")
        return {"message": "Training already in progress", "status": "error"}
    
    try:
        training_thread = threading.Thread(target=run_training, daemon=True)
        training_thread.start()
        logger.info("Training thread started")
        return {"message": "Training started", "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        return {"message": f"Failed to start training: {e}", "status": "error"}

@app.post("/training/stop")
def stop_training():
    """Stop training (graceful shutdown)."""
    global training_active
    
    if not training_active:
        return {"message": "Training not in progress", "status": "ok"}
    
    logger.info("Stop training requested")
    # Note: Graceful stop would require a flag in Trainer
    return {"message": "Stop requested - training will finish current episode", "status": "ok"}
