import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import GameScene from './components/GameScene';
import Controls from './components/Controls';
import axios from 'axios';
import './index.css';

const API_URL = 'http://localhost:8000';

function App() {
    const [gameState, setGameState] = useState(null);
    const [mode, setMode] = useState('play'); // 'play' or 'watch'
    const [message, setMessage] = useState('Welcome to SkyTowers');

    const fetchState = async () => {
        try {
            const res = await axios.get(`${API_URL}/game/state`);
            setGameState(res.data);
            if (res.data.winner !== null) {
                setMessage(res.data.winner === 0 ? "Draw!" : `Player ${res.data.winner} Wins!`);
            }
        } catch (err) {
            console.error("Error fetching state:", err);
        }
    };

    useEffect(() => {
        fetchState();
        const interval = setInterval(fetchState, 1000); // Poll every second
        return () => clearInterval(interval);
    }, []);

    const handleMove = async (move) => {
        try {
            const res = await axios.post(`${API_URL}/game/move`, move);
            if (res.data.winner !== null) {
                setMessage(res.data.winner === 0 ? "Draw!" : `Player ${res.data.winner} Wins!`);
            }
            fetchState();
        } catch (err) {
            setMessage("Invalid Move!");
            console.error(err);
        }
    };

    const handleReset = async () => {
        await axios.post(`${API_URL}/game/reset`);
        setMessage("Game Reset");
        fetchState();
    };

    return (
        <div className="app-container">
            <div className="ui-layer">
                <h1>SkyTowers</h1>
                <div className="status-bar">{message}</div>
                <Controls onReset={handleReset} mode={mode} setMode={setMode} />
            </div>
            <div className="canvas-container">
                <Canvas camera={{ position: [8, 8, 8], fov: 50 }}>
                    <color attach="background" args={['#111']} />
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} intensity={1} />
                    <Stars />
                    <GameScene gameState={gameState} onMove={handleMove} />
                    <OrbitControls />
                </Canvas>
            </div>
        </div>
    );
}

export default App;
