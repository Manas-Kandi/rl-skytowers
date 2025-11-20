from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
from .game import SkyTowersGame
from .model import SkyNet
from .mcts import MCTS, Args

app = FastAPI()

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

@app.get("/training/start")
def start_training():
    # Trigger a training episode in background? 
    # For now, let's just say we can run the trainer.py separately
    return {"message": "Run 'python backend/trainer.py' to train"}
