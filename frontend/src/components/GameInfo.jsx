import React, { useState, useEffect } from 'react';
import Controls from './Controls';
import ModelSelector from './ModelSelector';

const GameInfo = ({
    gameState,
    mode,
    message,
    onReset,
    onStartTraining,
    onStopTraining,
    models,
    currentModel,
    onLoadModel,
    trainingStartTime,
    trainingDuration,
    currentGameMoves,
    completedGames,
    onReplayGame,
    metrics
}) => {
    const [elapsedTime, setElapsedTime] = useState(0);

    const getPlayerLabel = (value) => {
        if (value === 1) return 'P1';
        if (value === -1) return 'P2';
        return '-';
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    useEffect(() => {
        if (mode === 'train' && trainingStartTime) {
            const interval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - trainingStartTime) / 1000);
                setElapsedTime(elapsed);
            }, 1000);
            return () => clearInterval(interval);
        } else {
            setElapsedTime(0);
        }
    }, [mode, trainingStartTime]);

    const remainingTime = trainingDuration ? Math.max(0, trainingDuration * 60 - elapsedTime) : 0;

    return (
        <section className="info-panel">
            <div className="header-minimal">
                <h1>SkyTowers</h1>
                <div className="status-line">
                    <span className={`status-dot ${mode === 'train' ? 'active' : ''}`}></span>
                    <p>{message}</p>
                </div>
            </div>

            {mode === 'train' ? (
                <>
                    {/* Training Timer */}
                    <div className="training-timer">
                        <div className="timer-row">
                            <label>Elapsed</label>
                            <span className="time-value">{formatTime(elapsedTime)}</span>
                        </div>
                        {trainingDuration && (
                            <div className="timer-row">
                                <label>Remaining</label>
                                <span className="time-value">{formatTime(remainingTime)}</span>
                            </div>
                        )}
                    </div>

                    {/* Training Metrics */}
                    {metrics && (
                        <div className="metrics-compact">
                            <div className="metric-row">
                                <label>Episodes</label>
                                <span>{metrics.total_episodes}</span>
                            </div>
                            <div className="metric-row">
                                <label>Win Rate</label>
                                <span>{metrics.p1_win_rate}%</span>
                            </div>
                            <div className="metric-row">
                                <label>Loss</label>
                                <span>{metrics.avg_loss}</span>
                            </div>
                            <div className="metric-row">
                                <label>ELO</label>
                                <span>{metrics.elo_rating}</span>
                            </div>
                        </div>
                    )}

                    {/* Current Game Moves */}
                    {currentGameMoves && currentGameMoves.length > 0 && (
                        <div className="moves-section">
                            <label className="section-label">Current Game</label>
                            <div className="moves-log">
                                {currentGameMoves.slice(-8).map((move, idx) => (
                                    <div key={idx} className="move-entry">
                                        <span className={`player-tag ${move.player === 1 ? 'p1' : 'p2'}`}>
                                            {move.player === 1 ? 'P1' : 'P2'}
                                        </span>
                                        <span className="move-text">
                                            →({move.move[0]},{move.move[1]})
                                            ⬆({move.build[0]},{move.build[1]})
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Completed Games History */}
                    {completedGames && completedGames.length > 0 && (
                        <div className="games-section">
                            <label className="section-label">Recent Games ({completedGames.length})</label>
                            <div className="games-list">
                                {completedGames.slice(-10).reverse().map((game, idx) => (
                                    <div
                                        key={game.id}
                                        className="game-item"
                                        onClick={() => onReplayGame(game)}
                                    >
                                        <span className={`winner-tag ${game.winner === 1 ? 'p1' : 'p2'}`}>
                                            {game.winner === 1 ? 'P1' : 'P2'}
                                        </span>
                                        <span className="game-info">
                                            {game.moves.length} moves
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <>
                    <div className="stat-row">
                        <div className="stat-item">
                            <label>Turn</label>
                            <span>{getPlayerLabel(gameState?.current_player)}</span>
                        </div>
                        <div className="stat-item">
                            <label>Step</label>
                            <span>{gameState?.steps ?? 0}</span>
                        </div>
                        <div className="stat-item">
                            <label>Mode</label>
                            <span>Manual</span>
                        </div>
                    </div>

                    <div className="control-group">
                        <label>Opponent</label>
                        <ModelSelector
                            models={models}
                            currentModel={currentModel}
                            onLoadModel={onLoadModel}
                        />
                    </div>
                </>
            )}

            <div className="actions">
                <Controls
                    onReset={onReset}
                    mode={mode}
                    onStartTraining={onStartTraining}
                    onStopTraining={onStopTraining}
                />
            </div>
        </section>
    );
};

export default GameInfo;
