import React from 'react';
import { Text } from '@react-three/drei';

const Cell = ({ r, c, height, onClick, isP1, isP2, isSelected, isTarget }) => {
    // Height 0: Flat
    // Height 1, 2, 3: Blocks
    // Height 4: Dome

    const blocks = [];
    for (let i = 0; i < height && i < 4; i++) {
        blocks.push(
            <mesh key={i} position={[0, i * 0.2 + 0.1, 0]} castShadow receiveShadow>
                <boxGeometry args={[0.9, 0.2, 0.9]} />
                <meshStandardMaterial color={i === 3 ? "blue" : "white"} />
            </mesh>
        );
    }

    return (
        <group position={[r - 2, 0, c - 2]} onClick={(e) => { e.stopPropagation(); onClick(r, c); }}>
            {/* Base Grid */}
            <mesh position={[0, -0.05, 0]}>
                <boxGeometry args={[0.95, 0.1, 0.95]} />
                <meshStandardMaterial color={isSelected ? "yellow" : isTarget ? "orange" : "#444"} />
            </mesh>

            {blocks}

            {/* Players */}
            {isP1 && (
                <mesh position={[0, height * 0.2 + 0.3, 0]}>
                    <sphereGeometry args={[0.25, 32, 32]} />
                    <meshStandardMaterial color="#00ff88" />
                </mesh>
            )}
            {isP2 && (
                <mesh position={[0, height * 0.2 + 0.3, 0]}>
                    <sphereGeometry args={[0.25, 32, 32]} />
                    <meshStandardMaterial color="#ff0055" />
                </mesh>
            )}
        </group>
    );
};

const Board = ({ board, p1_pos, p2_pos, onCellClick, selectedPos }) => {
    const grid = [];
    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            const isP1 = p1_pos[0] === r && p1_pos[1] === c;
            const isP2 = p2_pos[0] === r && p2_pos[1] === c;

            let isSelected = false;
            let isTarget = false;

            if (selectedPos) {
                if (selectedPos.phase === 'move' && selectedPos.r === r && selectedPos.c === c) {
                    isSelected = true;
                }
                if (selectedPos.phase === 'build' && selectedPos.move_r === r && selectedPos.move_c === c) {
                    isSelected = true; // The piece moved here
                }
            }

            grid.push(
                <Cell
                    key={`${r}-${c}`}
                    r={r}
                    c={c}
                    height={board[r][c]}
                    onClick={onCellClick}
                    isP1={isP1}
                    isP2={isP2}
                    isSelected={isSelected}
                    isTarget={isTarget}
                />
            );
        }
    }

    return <group>{grid}</group>;
};

export default Board;
