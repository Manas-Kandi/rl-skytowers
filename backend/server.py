from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
import asyncio
import json
from .game import SkyTowersGame
from .model import SkyNet
from .mcts import MCTS, Args
from .trainer import Trainer

app = FastAPI()

# Store connected clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()
training_active = False

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
if args.cuda:
    model = model.to('mps')

# Load model if exists
import os
if os.path.exists(args.checkpoint_dir + '/best.pth.tar'):
    model.load_state_dict(torch.load(args.checkpoint_dir + '/best.pth.tar', map_location='mps' if args.cuda else 'cpu'))
model.eval()
mcts = MCTS(game, model, args)

class MoveRequest(BaseModel):
    move_r: int
    move_c: int
    build_r: int
    build_c: int

@app.get("/game/state")
def get_state():
    return {
        "board": game.board.tolist(),
        "p1_pos": game.p1_pos,
        "p2_pos": game.p2_pos,
        "current_player": game.current_player,
        "winner": game.winner
    }

@app.post("/game/reset")
def reset_game():
    game.reset()
    global mcts
    mcts = MCTS(game, model, args)
    return {"message": "Game reset"}

@app.post("/game/move")
def make_move(move: MoveRequest):
    if game.winner is not None:
        raise HTTPException(status_code=400, detail="Game over")
        
    action = ((move.move_r, move.move_c), (move.build_r, move.build_c))
    
    # Validate move (simple check if it's in valid moves)
    valid_moves = game.get_valid_moves()
    if action not in valid_moves:
        raise HTTPException(status_code=400, detail="Invalid move")
        
    game.step(action)
    
    # If game not over, AI moves
    if game.winner is None:
        # AI Move
        # Use MCTS to get best move
        # For responsiveness, we might want to reduce sims or do this async
        # But for simplicity, let's do it blocking with fewer sims
        temp_args = Args()
        temp_args.numMCTSSims = 50 # Fast enough?
        ai_mcts = MCTS(game, model, temp_args)
        pi = ai_mcts.getActionProb(game, temp=0)
        action_idx = np.argmax(pi)
        
        # Decode
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
        
        game.step((move_pos, build_pos))
        
        return {
            "player_move": action,
            "ai_move": ((move_pos[0], move_pos[1]), (build_pos[0], build_pos[1])),
            "winner": game.winner
        }
        
    return {"player_move": action, "winner": game.winner}

@app.websocket("/ws/training")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def training_callback(state):
    # This runs in the training thread. We need to broadcast to websocket.
    # Since broadcast is async, we need to run it in the event loop.
    # But we are in a sync thread.
    # Simple hack: use asyncio.run or run_coroutine_threadsafe if we had access to the loop.
    # Better: Just put it in a queue or similar?
    # For simplicity in this MVP, let's try to use the loop.
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    # Actually, getting the running loop from a separate thread is hard.
    # Let's just use a global queue or variable, and have a background task in FastAPI poll it?
    # Or simpler: Use `asyncio.run` to send a single message? No, that creates a new loop.
    # Correct way: Use `run_coroutine_threadsafe`.
    pass

# Let's redefine the callback to be simpler.
# We will run training in a background task using FastAPI's BackgroundTasks?
# No, training is blocking. We should run it in a separate thread.
import threading

def run_training():
    global training_active
    training_active = True
    
    # Helper to broadcast from thread
    def callback(state):
        asyncio.run(manager.broadcast(state)) 
        # Warning: asyncio.run creates a new loop. 
        # If manager.broadcast uses objects bound to the main loop, it might fail.
        # But here it just sends on sockets. Sockets are bound to main loop.
        # This will likely fail.
        
    # Better approach:
    # The callback updates a global "latest_state".
    # A background asyncio task broadcasts "latest_state" every X ms.
    
    global latest_training_state
    def callback_safe(state):
        global latest_training_state
        latest_training_state = state
        
    trainer = Trainer(callback=callback_safe)
    trainer.learn()
    training_active = False

latest_training_state = None

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_loop())

async def broadcast_loop():
    global latest_training_state
    last_sent = None
    while True:
        if latest_training_state and latest_training_state != last_sent:
            await manager.broadcast(latest_training_state)
            last_sent = latest_training_state
        await asyncio.sleep(0.1)

@app.post("/training/start")
def start_training():
    global training_active
    if training_active:
        return {"message": "Training already in progress"}
    
    thread = threading.Thread(target=run_training)
    thread.start()
    return {"message": "Training started"}

@app.post("/training/stop")
def stop_training():
    # Not easily stoppable without flags in Trainer, but for now we just let it finish
    return {"message": "Stop not implemented yet"}
