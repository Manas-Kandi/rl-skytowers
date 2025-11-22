import React from 'react';

const Controls = ({ onReset, mode, onStartTraining, onStopTraining }) => {
    return (
        <div className="controls">
            {mode === 'play' ? (
                <>
                    <button onClick={onReset}>Reset Game</button>
                    <button onClick={onStartTraining}>Start Training</button>
                </>
            ) : (
                <button onClick={onStopTraining} className="stop-btn">Stop Watching</button>
            )}
        </div>
    );
};

export default Controls;
