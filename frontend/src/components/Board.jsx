import React from 'react';
import { Text } from '@react-three/drei';
import * as THREE from 'three';

const Cell = ({ r, c, height, onClick, isP1, isP2, isSelected, isTarget }) => {
    const blocks = [];
    
    // Refined color palette - visible against black
    const blockColors = [
        "#3a4050",  // Level 1
        "#4a5060",  // Level 2
        "#5a6070",  // Level 3
        "#6a7080"   // Level 4
    ];
    
    // Build tower blocks with refined geometry
    for (let i = 0; i < height && i < 4; i++) {
        const blockHeight = 0.18;
        const yPos = i * blockHeight + blockHeight / 2;
        
        blocks.push(
            <group key={i}>
                {/* Main block */}
                <mesh position={[0, yPos, 0]} castShadow receiveShadow>
                    <boxGeometry args={[0.85, blockHeight, 0.85]} />
                    <meshStandardMaterial 
                        color={blockColors[i]}
                        metalness={0.6}
                        roughness={0.4}
                        emissive={blockColors[i]}
                        emissiveIntensity={0.05}
                    />
                </mesh>
                {/* Subtle edge glow */}
                <mesh position={[0, yPos, 0]}>
                    <boxGeometry args={[0.87, blockHeight + 0.01, 0.87]} />
                    <meshBasicMaterial 
                        color="#6dd5ed"
                        transparent
                        opacity={0.03 * (i + 1)}
                    />
                </mesh>
            </group>
        );
    }

    // Crown dome (height 4) - glowing cyan
    if (height >= 4) {
        blocks.push(
            <group key="dome">
                <mesh position={[0, 0.72 + 0.15, 0]} castShadow>
                    <sphereGeometry args={[0.38, 32, 32]} />
                    <meshStandardMaterial 
                        color="#1a2535"
                        metalness={0.8}
                        roughness={0.2}
                        emissive="#6dd5ed"
                        emissiveIntensity={0.4}
                    />
                </mesh>
                {/* Dome glow */}
                <mesh position={[0, 0.72 + 0.15, 0]}>
                    <sphereGeometry args={[0.42, 32, 32]} />
                    <meshBasicMaterial 
                        color="#6dd5ed"
                        transparent
                        opacity={0.15}
                    />
                </mesh>
            </group>
        );
    }

    const baseColor = isSelected ? "#6dd5ed" : "#2a3040";

    return (
        <group position={[r - 2, 0, c - 2]} onClick={(e) => { e.stopPropagation(); onClick(r, c); }}>
            {/* Island base - dark minimal */}
            <mesh position={[0, -0.04, 0]} receiveShadow>
                <boxGeometry args={[0.92, 0.08, 0.92]} />
                <meshStandardMaterial 
                    color={baseColor}
                    metalness={0.3}
                    roughness={0.7}
                    emissive={isSelected ? "#6dd5ed" : "#000000"}
                    emissiveIntensity={isSelected ? 0.2 : 0}
                />
            </mesh>

            {blocks}

            {/* Player 1 - Cyan glowing builder */}
            {isP1 && (
                <group position={[0, height * 0.18 + 0.3, 0]}>
                    <mesh castShadow>
                        <cylinderGeometry args={[0.15, 0.18, 0.35, 32]} />
                        <meshStandardMaterial 
                            color="#1a2535"
                            metalness={0.7}
                            roughness={0.3}
                            emissive="#6dd5ed"
                            emissiveIntensity={0.6}
                        />
                    </mesh>
                    {/* Player glow */}
                    <mesh>
                        <sphereGeometry args={[0.25, 16, 16]} />
                        <meshBasicMaterial 
                            color="#6dd5ed"
                            transparent
                            opacity={0.2}
                        />
                    </mesh>
                </group>
            )}
            
            {/* Player 2 - Magenta glowing builder */}
            {isP2 && (
                <group position={[0, height * 0.18 + 0.3, 0]}>
                    <mesh castShadow>
                        <cylinderGeometry args={[0.15, 0.18, 0.35, 32]} />
                        <meshStandardMaterial 
                            color="#2a1a35"
                            metalness={0.7}
                            roughness={0.3}
                            emissive="#ed6dd5"
                            emissiveIntensity={0.6}
                        />
                    </mesh>
                    {/* Player glow */}
                    <mesh>
                        <sphereGeometry args={[0.25, 16, 16]} />
                        <meshBasicMaterial 
                            color="#ed6dd5"
                            transparent
                            opacity={0.2}
                        />
                    </mesh>
                </group>
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
