import React from 'react';

const LeaderboardRow = ({ name, count, maxCount }) => {
  const percent = (Number(count) / Number(maxCount)) * 100;

  const progressStyle = {
    height: '10px',
    width: '100%',
    backgroundColor: '#444',
    borderRadius: '5px',
    overflow: 'hidden',
    marginTop: '4px',
  };

  const fillStyle = {
    height: '100%',
    width: `${percent}%`,
    backgroundColor: `#0a0`,
    transition: 'width 0.5s ease-in-out',
  };

  return (
    <li style={{ marginBottom: '1rem' }}>
      <strong>{name}</strong>, {count} vote{count !== 1 ? 's' : ''}
      <div style={progressStyle}>
        <div style={fillStyle}></div>
      </div>
    </li>
  );
};

export default LeaderboardRow;