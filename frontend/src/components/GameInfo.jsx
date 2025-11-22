import React from 'react';
import Controls from './Controls';
import ModelSelector from './ModelSelector';

const GameInfo = ({ gameState, mode, message, onReset, onStartTraining, onStopTraining, models, currentModel, onLoadModel }) => {
    const getPlayerLabel = (value) => {
        if (value === 1) return 'P1';
        if (value === -1) return 'P2';
        return '-';
    };

    return (
        <section className="info-panel">
            <div className="header-minimal">
                <h1>SkyTowers</h1>
                <div className="status-line">
                    <span className={`status-dot ${mode === 'train' ? 'active' : ''}`}></span>
                    <p>{message}</p>
                </div>
            </div>

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
                    <span>{mode === 'play' ? 'Manual' : 'Auto'}</span>
                </div>
            </div>

            {mode === 'play' && (
                <div className="control-group">
                    <label>Opponent</label>
                    <ModelSelector
                        models={models}
                        currentModel={currentModel}
                        onLoadModel={onLoadModel}
                    />
                </div>
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
