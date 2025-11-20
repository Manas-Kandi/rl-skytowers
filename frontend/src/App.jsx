import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import GameScene from './components/GameScene';
import Controls from './components/Controls';
import axios from 'axios';
import './index.css';

import HistoryLog from './components/HistoryLog';

const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/training';

function App() {
    const [gameState, setGameState] = useState(null);
    const [mode, setMode] = useState('play'); // 'play' or 'train'
    const [message, setMessage] = useState('Welcome to SkyTowers');
    const [history, setHistory] = useState([]);
    const ws = useRef(null);

    const fetchState = async () => {
        if (mode === 'train') return; // Don't poll in train mode
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
    }, [mode]);

    const startTraining = async () => {
        setMode('train');
        setHistory([]);
        setMessage("Training Started...");

        // Connect WS
        ws.current = new WebSocket(WS_URL);
        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setGameState(data);
            if (data.last_move) {
                setHistory(prev => [...prev, {
                    player: data.current_player * -1, // The player who JUST moved
                    move: data.last_move.move,
                    build: data.last_move.build
                }]);
            }
            if (data.winner !== null) {
                setMessage(`Episode Finished. Winner: ${data.winner}`);
                // Clear history after a delay or keep it? Keep it.
            } else {
                setMessage(`Training Episode... Step ${data.step}`);
            }
        };

        await axios.post(`${API_URL}/training/start`);
    };

    const stopTraining = () => {
        setMode('play');
        if (ws.current) ws.current.close();
        fetchState();
    };

    const handleMove = async (move) => {
        if (mode === 'train') return;
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
        setHistory([]);
        fetchState();
    };

    return (
        <div className="app-container">
            <div className="ui-layer">
                <h1>SkyTowers</h1>
                <div className="status-bar">{message}</div>
                <Controls
                    onReset={handleReset}
                    mode={mode}
                    onStartTraining={startTraining}
                    onStopTraining={stopTraining}
                />
                {mode === 'train' && <HistoryLog history={history} />}
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
