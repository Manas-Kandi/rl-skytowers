import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import GameScene from './components/GameScene';
import Controls from './components/Controls';
import HistoryLog from './components/HistoryLog';
import axios from 'axios';
import './index.css';

const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/training';

function App() {
    const [gameState, setGameState] = useState(null);
    const [mode, setMode] = useState('play'); // 'play' or 'train'
    const [message, setMessage] = useState('Welcome to SkyTowers');
    const [history, setHistory] = useState([]);
    const ws = useRef(null);

    const purposeCards = [
        {
            label: '01',
            title: 'Ascend',
            body: 'Move your builder to any neighboring tile, climbing at most one level per turn.'
        },
        {
            label: '02',
            title: 'Sculpt',
            body: 'After every move, elevate an adjacent tower to redirect paths or seal domes.'
        },
        {
            label: '03',
            title: 'Crown',
            body: 'Reach level three first—or strand your rival with no moves—to claim the skyline.'
        }
    ];

    const guideSteps = [
        'Choose the worker with the clearest stairwell and keep an escape lane in reserve.',
        'Step, slide, or descend a single level, then raise any adjacent tile to reshape the board.',
        'Cap towers with domes to lock them down and funnel your opponent into stalemate.'
    ];

    const getPlayerLabel = (value) => {
        if (value === 1) return 'Builder One';
        if (value === -1) return 'Builder Two';
        return '—';
    };

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

    useEffect(() => {
        fetchState();
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

    const modeCaption =
        mode === 'play'
            ? 'Manual Command · Orchestrate every ascent yourself.'
            : 'Neural Training · Watch self-play iterations converge.';

    return (
        <div className="app-container">
            <section className="info-panel">
                <div className="logo-lockup">
                    <p className="eyebrow">Minimal neural skirmish</p>
                    <h1>SkyTowers</h1>
                    <p className="subhead">
                        A tranquil race toward level-three rooftops. Move, sculpt, and crown towers while a silent skyline watches each decision.
                    </p>
                </div>

                <div className="purpose-grid">
                    {purposeCards.map((card) => (
                        <article key={card.label} className="purpose-card">
                            <span className="card-label">{card.label}</span>
                            <h3>{card.title}</h3>
                            <p>{card.body}</p>
                        </article>
                    ))}
                </div>

                <div className="status-stack">
                    <div className="status-chip">{message}</div>
                    <p className="mode-caption">{modeCaption}</p>
                </div>

                <div className="stat-grid">
                    <div className="stat-card">
                        <span>Current Player</span>
                        <strong>{getPlayerLabel(gameState?.current_player)}</strong>
                    </div>
                    <div className="stat-card">
                        <span>Steps Taken</span>
                        <strong>{gameState?.steps ?? '—'}</strong>
                    </div>
                    <div className="stat-card">
                        <span>Victory Condition</span>
                        <strong>Reach level three</strong>
                    </div>
                </div>

                <Controls
                    onReset={handleReset}
                    mode={mode}
                    onStartTraining={startTraining}
                    onStopTraining={stopTraining}
                />

                <section className="guide-panel">
                    <div className="guide-header">
                        <h2>How to ascend</h2>
                        <span>Three-phase ritual</span>
                    </div>
                    <ol>
                        {guideSteps.map((step, idx) => (
                            <li key={step}>
                                <span>{String(idx + 1).padStart(2, '0')}</span>
                                <p>{step}</p>
                            </li>
                        ))}
                    </ol>
                </section>

                {mode === 'train' && (
                    <section className="history-panel">
                        <div className="guide-header">
                            <h2>Live training feed</h2>
                            <span>Move · Build</span>
                        </div>
                        <HistoryLog history={history} />
                    </section>
                )}
            </section>

            <section className="canvas-panel">
                <div className="canvas-wrapper">
                    <Canvas camera={{ position: [8, 8, 8], fov: 50 }}>
                        <color attach="background" args={['#030712']} />
                        <ambientLight intensity={0.5} />
                        <pointLight position={[10, 10, 10]} intensity={1} />
                        <Stars />
                        <GameScene gameState={gameState} onMove={handleMove} />
                        <OrbitControls />
                    </Canvas>
                    <div className="canvas-glow" />
                </div>
                <p className="canvas-caption">
                    Orbit the board, trace luminous towers, and feel the hush between strategic breaths.
                </p>
            </section>
        </div>
    );
}

export default App;
