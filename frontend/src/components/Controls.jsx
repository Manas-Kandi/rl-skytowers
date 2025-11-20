import React from 'react';

const Controls = ({ onReset, mode, onStartTraining, onStopTraining }) => {
    return (
        <div className="controls">
            {mode === 'play' ? (
                <>
                    <button onClick={onReset}>Reset Game</button>
                    <button onClick={onStartTraining} style={{ marginLeft: '10px' }}>Start Training</button>
                </>
            ) : (
                <button onClick={onStopTraining} style={{ background: '#ff4444' }}>Stop Watching</button>
            )}
        </div>
    );
};

export default Controls;
