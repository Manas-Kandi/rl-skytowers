import React, { useEffect, useRef } from 'react';

const HistoryLog = ({ history }) => {
    const endRef = useRef(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history]);

    return (
        <div className="history-log">
            <ul>
                {history.map((entry, i) => (
                    <li key={i}>
                        <span className={entry.player === 1 ? "p1" : "p2"}>
                            P{entry.player === 1 ? "1" : "2"}
                        </span>
                        : Move ({entry.move[0]},{entry.move[1]}) → Build ({entry.build[0]},{entry.build[1]})
                    </li>
                ))}
            </ul>
            <div ref={endRef} />
        </div>
    );
};

export default HistoryLog;
