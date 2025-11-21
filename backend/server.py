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
import queue
import time
from typing import Optional, List, Dict, Any

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
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to client: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

manager = ConnectionManager()

class GameManager:
    """
    Manages the global game state and AI models.
    Thread-safe singleton-like pattern for the server.
    """
    def __init__(self):
        self.args = Args()
        self.game = SkyTowersGame()
        self.model = SkyNet()
        self.mcts = None
        self.device = 'mps' if self.args.cuda else 'cpu'
        
        # Training state
        self.training_active = False
        self.training_thread = None
        self.trainer = None
        self.update_queue = queue.Queue(maxsize=1000) # Buffer for UI updates
        
        self._load_model()
        self._init_mcts()
        
    def _load_model(self):
        self.model = self.model.to(self.device)
        checkpoint_path = os.path.join(self.args.checkpoint_dir, 'best.pth.tar')
        if os.path.exists(checkpoint_path):
            try:
                checkpoint = torch.load(checkpoint_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['state_dict'])
                logger.info(f"Loaded model from {checkpoint_path}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
        else:
            logger.info("No checkpoint found, using random initialization")
        self.model.eval()

    def _init_mcts(self):
        self.mcts = MCTS(self.game, self.model, self.args)

    def reset_game(self):
        self.game.reset()
        self._init_mcts()
        logger.info("Game reset")

    def get_state(self):
        return {
            "board": self.game.board.tolist(),
            "p1_pos": self.game.p1_pos,
            "p2_pos": self.game.p2_pos,
            "current_player": self.game.current_player,
            "winner": self.game.winner,
            "steps": self.game.steps
        }

    def start_training(self):
        if self.training_active:
            raise Exception("Training already in progress")
        
        self.training_active = True
        # Clear queue
        with self.update_queue.mutex:
            self.update_queue.queue.clear()
            
        self.trainer = Trainer(callback_queue=self.update_queue)
        self.training_thread = threading.Thread(target=self._run_training_loop, daemon=True)
        self.training_thread.start()
        logger.info("Training thread started")

    def stop_training(self):
        if self.training_active and self.trainer:
            self.trainer.stop()
            logger.info("Stop signal sent to trainer")
            # We don't join here to avoid blocking, the thread will exit eventually
            # But we set flag to false immediately for UI feedback
            self.training_active = False 

    def _run_training_loop(self):
        try:
            if self.trainer:
                self.trainer.learn()
        except Exception as e:
            logger.error(f"Training error: {e}")
        finally:
            self.training_active = False
            # Reload model to get latest weights
            self._load_model()
            self._init_mcts()
            logger.info("Training finished, model reloaded")

    def list_models(self):
        """List available model checkpoints."""
        checkpoint_dir = self.args.checkpoint_dir
        if not os.path.exists(checkpoint_dir):
            return []
        return [f for f in os.listdir(checkpoint_dir) if f.endswith('.pth.tar')]

    def load_model(self, filename):
        """Load a specific model checkpoint."""
        filepath = os.path.join(self.args.checkpoint_dir, filename)
        if not os.path.exists(filepath):
            logger.error(f"Model file {filename} not found")
            return False
        
        try:
            checkpoint = torch.load(filepath, map_location=self.device)
            self.model.load_state_dict(checkpoint['state_dict'])
            self.model.eval()
            self._init_mcts() # Re-init MCTS with new model
            logger.info(f"Loaded model from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
            self.training_active = False
            logger.info("Training thread finished")
            # Reload model after training to get latest weights for play mode
            self._load_model()
            self._init_mcts()

# Global instance
gm = GameManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MoveRequest(BaseModel):
    """Request model for player moves."""
    move_r: int
    move_c: int
    build_r: int
    build_c: int

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "training_active": gm.training_active}

@app.get("/game/state")
def get_state():
    """Get current game state."""
    try:
        return gm.get_state()
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game state")

@app.post("/game/reset")
def reset_game():
    """Reset the game to initial state."""
    try:
        gm.reset_game()
        return {"message": "Game reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting game: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset game")

@app.post("/game/move")
def make_move(move: MoveRequest):
    """
    Process a player move and generate AI response.
    """
    try:
        if gm.game.winner is not None:
            raise HTTPException(status_code=400, detail="Game is over")
            
        action = ((move.move_r, move.move_c), (move.build_r, move.build_c))
        
        # Validate move
        valid_moves = gm.game.get_valid_moves()
        if action not in valid_moves:
            logger.warning(f"Invalid move attempted: {action}")
            raise HTTPException(status_code=400, detail="Invalid move")
            
        # Execute player move
        gm.game.step(action)
        logger.info(f"Player 1 moved to {action[0]}, built at {action[1]}")
        
        # If game not over, AI moves
        ai_move = None
        if gm.game.winner is None:
            ai_move = _get_ai_move()
            gm.game.step(ai_move)
            logger.info(f"AI (Player -1) moved to {ai_move[0]}, built at {ai_move[1]}")
            
        return {
            "player_move": action,
            "ai_move": ai_move,
            "winner": gm.game.winner,
            "board": gm.game.board.tolist(),
            "p1_pos": gm.game.p1_pos,
            "p2_pos": gm.game.p2_pos,
            "current_player": gm.game.current_player
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing move: {e}")
        raise HTTPException(status_code=500, detail="Failed to process move")

def _get_ai_move():
    """Get AI move using MCTS."""
    try:
        # Use a fresh MCTS for the move to ensure exploration
        temp_args = Args()
        temp_args.numMCTSSims = 50
        ai_mcts = MCTS(gm.game, gm.model, temp_args)
        pi = ai_mcts.getActionProb(gm.game, temp=0)
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
        curr = gm.game.p1_pos if gm.game.current_player == 1 else gm.game.p2_pos
        move_pos = (curr[0] + dr, curr[1] + dc)
        b_dr, b_dc = dirs[b_idx]
        build_pos = (move_pos[0] + b_dr, move_pos[1] + b_dc)
        
        return (move_pos, build_pos)
    except Exception as e:
        logger.error(f"Error getting AI move: {e}")
        # Fallback: return first valid move
        valid_moves = gm.game.get_valid_moves()
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
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    """Start background broadcast loop on server startup."""
    logger.info("Server starting up")
    asyncio.create_task(broadcast_loop())

async def broadcast_loop():
    """
    Periodically consume updates from the queue and broadcast to clients.
    Limits broadcast rate to ~30fps to avoid overwhelming frontend.
    """
    while True:
        try:
            # Consume all available updates, but only broadcast the latest game state
            # to catch up if falling behind, BUT keep all metrics updates?
            # For now, let's just take the latest available item if multiple are queued
            # to prevent lag.
            
            update = None
            # Drain queue to get latest
            try:
                while True:
                    update = gm.update_queue.get_nowait()
            except queue.Empty:
                pass
            
            if update:
                await manager.broadcast(update)
                
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
        
        await asyncio.sleep(0.033) # ~30 FPS

@app.post("/training/start")
def start_training():
    """Start a new training session."""
    try:
        gm.start_training()
        return {"message": "Training started", "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        return {"message": f"Failed to start training: {e}", "status": "error"}

@app.post("/training/stop")
def stop_training():
    """Stop training (graceful shutdown)."""
    try:
        gm.stop_training()
        return {"message": "Stop requested", "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to stop training: {e}")
        return {"message": f"Failed to stop training: {e}", "status": "error"}

@app.get("/models")
async def list_models():
    return {"models": gm.list_models()}

@app.post("/models/load")
async def load_model(request: dict):
    filename = request.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    success = gm.load_model(filename)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found or invalid")
    
    return {"status": "loaded", "model": filename}
