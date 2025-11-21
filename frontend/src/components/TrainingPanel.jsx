import React from 'react';
import HistoryLog from './HistoryLog';

const TrainingPanel = ({ metrics, history }) => {
    return (
        <div className="training-container">
            {metrics && (
                <section className="metrics-panel">
                    <div className="guide-header">
                        <h2>Learning Progress</h2>
                        <span>AI is improving</span>
                    </div>
                    <div className="metrics-grid">
                        <div className="metric-card">
                            <span className="metric-label">Episodes</span>
                            <strong className="metric-value">{metrics.total_episodes}</strong>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Win Rate</span>
                            <strong className="metric-value">{metrics.p1_win_rate}%</strong>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Avg Loss</span>
                            <strong className="metric-value">{metrics.avg_loss}</strong>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">ELO Rating</span>
                            <strong className="metric-value">{metrics.elo_rating}</strong>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Avg Steps</span>
                            <strong className="metric-value">{metrics.avg_episode_length}</strong>
                        </div>
                    </div>
                    {metrics.recent_losses && metrics.recent_losses.length > 0 && (
                        <div className="loss-trend">
                            <span className="trend-label">Loss Trend (last 10)</span>
                            <div className="trend-bars">
                                {metrics.recent_losses.map((loss, idx) => (
                                    <div
                                        key={idx}
                                        className="trend-bar"
                                        style={{ height: `${Math.min(loss * 100, 100)}%` }}
                                        title={`Episode ${metrics.total_episodes - metrics.recent_losses.length + idx + 1}: ${loss}`}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </section>
            )}

            <section className="history-panel">
                <div className="guide-header">
                    <h2>Live training feed</h2>
                    <span>Move · Build</span>
                </div>
                <HistoryLog history={history} />
            </section>
        </div>
    );
};

export default TrainingPanel;
