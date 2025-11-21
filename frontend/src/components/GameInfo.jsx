import React from 'react';
import Controls from './Controls';
import ModelSelector from './ModelSelector';

const GameInfo = ({ gameState, mode, message, onReset, onStartTraining, onStopTraining, models, currentModel, onLoadModel }) => {
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

    const modeCaption =
        mode === 'play'
            ? 'Manual Command · Orchestrate every ascent yourself.'
            : 'Neural Training · Watch self-play iterations converge.';

    return (
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

            {mode === 'play' && (
                <div className="model-section">
                    <h3>Opponent Intelligence</h3>
                    <ModelSelector
                        models={models}
                        currentModel={currentModel}
                        onLoadModel={onLoadModel}
                    />
                </div>
            )}

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
                onReset={onReset}
                mode={mode}
                onStartTraining={onStartTraining}
                onStopTraining={onStopTraining}
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
        </section>
    );
};

export default GameInfo;
