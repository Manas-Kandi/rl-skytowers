import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import GameInfo from './components/GameInfo';
import TrainingPanel from './components/TrainingPanel';
import GameCanvas from './components/GameCanvas';
import './index.css';

const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/training';

function App() {
    const [gameState, setGameState] = useState(null);
    const [mode, setMode] = useState('play'); // 'play' or 'train'
    const [message, setMessage] = useState('Welcome to SkyTowers');
    const [history, setHistory] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [models, setModels] = useState([]);
    const [currentModel, setCurrentModel] = useState(null);
    const ws = useRef(null);

    const fetchState = async () => {
        if (mode === 'train') return; // Don't poll in train mode
        try {
            const res = await axios.get(`${API_URL}/game/state`);
            setGameState(res.data);
            if (res.data.winner !== null) {
                setMessage(res.data.winner === 0 ? 'Draw!' : `Player ${res.data.winner} Wins!`);
            }
        } catch (err) {
            console.error('Error fetching state:', err);
        }
    };

    const fetchModels = async () => {
        try {
            const res = await axios.get(`${API_URL}/models`);
            setModels(res.data.models);
        } catch (err) {
            console.error('Error fetching models:', err);
        }
    };

    const handleLoadModel = async (filename) => {
        try {
            await axios.post(`${API_URL}/models/load`, { filename });
            setCurrentModel(filename);
            setMessage(`Loaded Model: ${filename}`);
        } catch (err) {
            setMessage('Error loading model');
            console.error(err);
        }
    };

    useEffect(() => {
        fetchState();
        fetchModels();
        const interval = setInterval(fetchState, 1000); // Poll every second
        return () => clearInterval(interval);
    }, [mode]);

    const startTraining = async () => {
        setMode('train');
        setHistory([]);
        setMessage('Training Started...');

        ws.current = new WebSocket(WS_URL);
        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // Handle metrics updates
            if (data.type === 'metrics') {
                setMetrics(data);
                return;
            }

            // Handle game state updates
            if (data.type === 'game_update') {
                setGameState(data);
                if (data.last_move) {
                    setHistory((prev) => [
                        ...prev,
                        {
                            player: data.current_player * -1,
                            move: data.last_move.move,
                            build: data.last_move.build
                        }
                    ]);
                }
                if (data.winner !== null) {
                    setMessage(`Episode Finished. Winner: ${data.winner}`);
                } else {
                    setMessage(`Training Episode · Step ${data.step}`);
                }
            } else if (!data.type) {
                // Fallback for legacy or direct state
                setGameState(data);
            }
        };

        await axios.post(`${API_URL}/training/start`);
    };

    const stopTraining = async () => {
        setMode('play');
        if (ws.current) ws.current.close();
        await axios.post(`${API_URL}/training/stop`);
        fetchState();
        fetchModels(); // Refresh models list after training
    };

    const handleMove = async (move) => {
        if (mode === 'train') return;
        try {
            const res = await axios.post(`${API_URL}/game/move`, move);
            if (res.data.winner !== null) {
                setMessage(res.data.winner === 0 ? 'Draw!' : `Player ${res.data.winner} Wins!`);
            }
            fetchState();
        } catch (err) {
            setMessage('Invalid Move!');
            console.error(err);
        }
    };

    const handleReset = async () => {
        await axios.post(`${API_URL}/game/reset`);
        setMessage('Game Reset');
        setHistory([]);
        fetchState();
    };

    return (
        <div className="app-container">
            <GameInfo
                gameState={gameState}
                mode={mode}
                message={message}
                onReset={handleReset}
                onStartTraining={startTraining}
                onStopTraining={stopTraining}
                models={models}
                currentModel={currentModel}
                onLoadModel={handleLoadModel}
            />

            {mode === 'train' && (
                <TrainingPanel metrics={metrics} history={history} />
            )}

            <GameCanvas gameState={gameState} onMove={handleMove} />
        </div>
    );
}

export default App;
