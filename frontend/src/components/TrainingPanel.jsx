import React from 'react';
import HistoryLog from './HistoryLog';

const TrainingPanel = ({ metrics, history }) => {
    return (
        <div className="training-container">
            {metrics && (
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
                        <span className="metric-label">Loss</span>
                        <strong className="metric-value">{metrics.avg_loss}</strong>
                    </div>
                    <div className="metric-card">
                        <span className="metric-label">ELO</span>
                        <strong className="metric-value">{metrics.elo_rating}</strong>
                    </div>
                </div>
            )}

            <div className="history-panel">
                <HistoryLog history={history} />
            </div>
        </div>
    );
};

export default TrainingPanel;
