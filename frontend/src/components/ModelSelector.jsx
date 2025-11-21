import React, { useState } from 'react';

const ModelSelector = ({ models, currentModel, onLoadModel }) => {
    const [selected, setSelected] = useState('');

    const handleLoad = () => {
        if (selected) {
            onLoadModel(selected);
        }
    };

    return (
        <div className="model-selector">
            <div className="selector-group">
                <select
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                    className="model-dropdown"
                >
                    <option value="">Select Model...</option>
                    {models.map((m) => (
                        <option key={m} value={m}>{m}</option>
                    ))}
                </select>
                <button
                    onClick={handleLoad}
                    disabled={!selected}
                    className="load-btn"
                >
                    Load
                </button>
            </div>
            {currentModel && (
                <div className="current-model">
                    <span>Active: </span>
                    <strong>{currentModel}</strong>
                </div>
            )}
        </div>
    );
};

export default ModelSelector;
