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

    // Training state
    const [trainingStartTime, setTrainingStartTime] = useState(null);
    const [trainingDuration, setTrainingDuration] = useState(null);
    const [currentGameMoves, setCurrentGameMoves] = useState([]);
    const [completedGames, setCompletedGames] = useState([]);
    const [isReplaying, setIsReplaying] = useState(false);

    const ws = useRef(null);
    const gameIdCounter = useRef(0);

    const fetchState = async () => {
        if (mode === 'train' || isReplaying) return; // Don't poll in train mode or during replay
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
        const interval = setInterval(fetchState, 1000);
        return () => clearInterval(interval);
    }, [mode, isReplaying]);

    const startTraining = async (durationMinutes) => {
        setMode('train');
        setHistory([]);
        setCurrentGameMoves([]);
        setCompletedGames([]);
        setTrainingStartTime(Date.now());
        setTrainingDuration(durationMinutes);
        setMessage(`Training Started for ${durationMinutes} minutes...`);

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
                    const move = {
                        player: data.current_player * -1,
                        move: data.last_move.move,
                        build: data.last_move.build
                    };

                    setCurrentGameMoves(prev => [...prev, move]);
                    setHistory(prev => [...prev, move]);
                }

                // Game completed
                if (data.winner !== null) {
                    setMessage(`Episode Finished. Winner: ${data.winner}`);

                    // Save completed game
                    setCompletedGames(prev => [...prev, {
                        id: gameIdCounter.current++,
                        winner: data.winner,
                        moves: currentGameMoves,
                        finalBoard: data.board
                    }]);

                    // Reset current game moves for next episode
                    setCurrentGameMoves([]);
                } else {
                    setMessage(`Training Episode · Step ${data.step}`);
                }
            } else if (!data.type) {
                setGameState(data);
            }
        };

        await axios.post(`${API_URL}/training/start`, { duration_minutes: durationMinutes });
    };

    const stopTraining = async () => {
        setMode('play');
        setTrainingStartTime(null);
        setTrainingDuration(null);
        setCurrentGameMoves([]);
        if (ws.current) ws.current.close();
        await axios.post(`${API_URL}/training/stop`);
        fetchState();
        fetchModels();
    };

    const replayGame = async (game) => {
        if (!game || !game.moves) return;

        setIsReplaying(true);
        setMessage(`Replaying Game (Winner: P${game.winner})`);

        // Reset to initial state
        await axios.post(`${API_URL}/game/reset`);
        await new Promise(resolve => setTimeout(resolve, 300));

        // Replay each move with delay
        for (let i = 0; i < game.moves.length; i++) {
            const move = game.moves[i];
            try {
                await axios.post(`${API_URL}/game/move`, {
                    move_r: move.move[0],
                    move_c: move.move[1],
                    build_r: move.build[0],
                    build_c: move.build[1]
                });
                await fetchState();
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch (err) {
                console.error('Replay error:', err);
                break;
            }
        }

        setIsReplaying(false);
        setMessage(`Replay Complete (Winner: P${game.winner})`);
    };

    const handleMove = async (move) => {
        if (mode === 'train' || isReplaying) return;
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
                trainingStartTime={trainingStartTime}
                trainingDuration={trainingDuration}
                currentGameMoves={currentGameMoves}
                completedGames={completedGames}
                onReplayGame={replayGame}
                metrics={metrics}
            />

            {mode === 'train' && (
                <TrainingPanel metrics={metrics} history={history} />
            )}

            <GameCanvas gameState={gameState} onMove={handleMove} />
        </div>
    );
}

export default App;
