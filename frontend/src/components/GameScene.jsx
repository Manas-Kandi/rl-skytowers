import React, { useState } from 'react';
import Board from './Board';

const GameScene = ({ gameState, onMove }) => {
    const [selectedPos, setSelectedPos] = useState(null); // {r, c}

    if (!gameState) return null;

    const handleCellClick = (r, c) => {
        if (gameState.winner !== null) return;

        // If nothing selected, select current player's piece
        if (!selectedPos) {
            const isP1 = gameState.current_player === 1;
            const pPos = isP1 ? gameState.p1_pos : gameState.p2_pos;
            if (pPos[0] === r && pPos[1] === c) {
                setSelectedPos({ r, c, phase: 'move' }); // Phase: move or build
            }
            return;
        }

        // If selected and in move phase
        if (selectedPos.phase === 'move') {
            // Check if clicking on self (deselect)
            if (selectedPos.r === r && selectedPos.c === c) {
                setSelectedPos(null);
                return;
            }

            // Assume valid move for UI (backend validates)
            // Transition to build phase
            setSelectedPos({
                r: selectedPos.r,
                c: selectedPos.c,
                move_r: r,
                move_c: c,
                phase: 'build'
            });
            return;
        }

        // If in build phase
        if (selectedPos.phase === 'build') {
            // Submit move
            onMove({
                move_r: selectedPos.move_r,
                move_c: selectedPos.move_c,
                build_r: r,
                build_c: c
            });
            setSelectedPos(null);
        }
    };

    return (
        <group>
            <Board
                board={gameState.board}
                p1_pos={gameState.p1_pos}
                p2_pos={gameState.p2_pos}
                onCellClick={handleCellClick}
                selectedPos={selectedPos}
            />
        </group>
    );
};

export default GameScene;
