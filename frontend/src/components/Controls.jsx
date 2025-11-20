import React from 'react';

const Controls = ({ onReset, mode, setMode }) => {
    return (
        <div className="controls">
            <button onClick={onReset}>Reset Game</button>
            {/* <button onClick={() => setMode(mode === 'play' ? 'watch' : 'play')}>
        Mode: {mode === 'play' ? 'Play vs AI' : 'Watch Training'}
      </button> */}
        </div>
    );
};

export default Controls;
