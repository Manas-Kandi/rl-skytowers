import React from 'react';
import { Text } from '@react-three/drei';

const Cell = ({ r, c, height, onClick, isP1, isP2, isSelected, isTarget }) => {
    // Height 0: Flat
    // Height 1, 2, 3: Blocks
    // Height 4: Dome

    const blocks = [];
    const blockColors = ["#e8e8e8", "#d0d0d0", "#a0a0ff", "#6060ff"];
    
    for (let i = 0; i < height && i < 4; i++) {
        blocks.push(
            <mesh key={i} position={[0, i * 0.2 + 0.1, 0]} castShadow receiveShadow>
                <boxGeometry args={[0.88, 0.19, 0.88]} />
                <meshStandardMaterial 
                    color={blockColors[i]} 
                    metalness={0.3}
                    roughness={0.7}
                />
            </mesh>
        );
    }

    // Dome (height 4)
    if (height >= 4) {
        blocks.push(
            <mesh key="dome" position={[0, 0.8 + 0.1, 0]} castShadow receiveShadow>
                <sphereGeometry args={[0.45, 16, 16]} />
                <meshStandardMaterial 
                    color="#6060ff" 
                    metalness={0.6}
                    roughness={0.4}
                    emissive="#3030ff"
                    emissiveIntensity={0.2}
                />
            </mesh>
        );
    }

    const baseColor = isSelected ? "#ffff00" : isTarget ? "#ff8800" : "#555555";

    return (
        <group position={[r - 2, 0, c - 2]} onClick={(e) => { e.stopPropagation(); onClick(r, c); }}>
            {/* Base Grid */}
            <mesh position={[0, -0.05, 0]} receiveShadow>
                <boxGeometry args={[0.95, 0.1, 0.95]} />
                <meshStandardMaterial 
                    color={baseColor}
                    metalness={0.2}
                    roughness={0.8}
                    emissive={isSelected ? "#ffff00" : "#000000"}
                    emissiveIntensity={isSelected ? 0.3 : 0}
                />
            </mesh>

            {blocks}

            {/* Players */}
            {isP1 && (
                <mesh position={[0, height * 0.2 + 0.35, 0]} castShadow>
                    <sphereGeometry args={[0.22, 32, 32]} />
                    <meshStandardMaterial 
                        color="#00ff88" 
                        metalness={0.5}
                        roughness={0.3}
                        emissive="#00ff88"
                        emissiveIntensity={0.3}
                    />
                </mesh>
            )}
            {isP2 && (
                <mesh position={[0, height * 0.2 + 0.35, 0]} castShadow>
                    <sphereGeometry args={[0.22, 32, 32]} />
                    <meshStandardMaterial 
                        color="#ff0055" 
                        metalness={0.5}
                        roughness={0.3}
                        emissive="#ff0055"
                        emissiveIntensity={0.3}
                    />
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
