import React, { useState } from 'react';

const Controls = ({ onReset, mode, onStartTraining, onStopTraining }) => {
    const [duration, setDuration] = useState(5);

    const handleStartTraining = () => {
        onStartTraining(duration);
    };

    return (
        <div className="controls">
            {mode === 'play' ? (
                <>
                    <button onClick={onReset}>Reset Game</button>
                    <div className="training-controls">
                        <label htmlFor="duration">Training Duration:</label>
                        <select
                            id="duration"
                            value={duration}
                            onChange={(e) => setDuration(Number(e.target.value))}
                        >
                            <option value={2}>2 minutes</option>
                            <option value={5}>5 minutes</option>
                            <option value={10}>10 minutes</option>
                            <option value={30}>30 minutes</option>
                            <option value={60}>1 hour</option>
                        </select>
                        <button onClick={handleStartTraining}>Start Training</button>
                    </div>
                </>
            ) : (
                <button onClick={onStopTraining} className="stop-btn">Stop Watching</button>
            )}
        </div>
    );
};

export default Controls;
