import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import GameScene from './GameScene';

const GameCanvas = ({ gameState, onMove }) => {
    return (
        <section className="canvas-panel">
            <div className="canvas-wrapper">
                <Canvas camera={{ position: [8, 8, 8], fov: 50 }}>
                    <color attach="background" args={['#050505']} />
                    <ambientLight intensity={0.8} />
                    <hemisphereLight skyColor="#ffffff" groundColor="#000000" intensity={0.5} />
                    <pointLight position={[10, 10, 10]} intensity={1.5} color="#ffffff" castShadow />
                    <pointLight position={[-5, 5, -5]} intensity={0.8} color="#6dd5ed" />
                    <Stars
                        radius={100}
                        depth={50}
                        count={3000}
                        factor={4}
                        saturation={0}
                        fade
                        speed={0.5}
                    />
                    <GameScene gameState={gameState} onMove={onMove} />
                    <OrbitControls
                        enableDamping
                        dampingFactor={0.05}
                        minDistance={5}
                        maxDistance={15}
                    />
                </Canvas>
                <div className="canvas-glow" />
            </div>
            <p className="canvas-caption">
                Orbit the board, trace luminous towers, and feel the hush between strategic breaths.
            </p>
        </section>
    );
};

export default GameCanvas;
