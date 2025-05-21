import React, { useEffect, useState } from 'react';
import axios from 'axios';
import LeaderboardRow from './LeaderboardRow';

function App() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [candidates, setCandidates] = useState([]);
  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  // Voter ID from localStorage
  const getVoterId = () => {
    let id = localStorage.getItem('voter_id');
    if (!id) {
      id = `${Date.now()}-${Math.floor(Math.random() * 1000000)}`;
      localStorage.setItem('voter_id', id);
    }
    return id;
  };

  const voterId = getVoterId();

  const castVote = async (candidate) => {
    try {
      await axios.post(`${backendUrl}/vote`, {
        voter_id: voterId,
        candidate,
      });
      setErrorMessage('');
      setSuccessMessage('Your vote has been cast successfully!');
    } catch (error) {
      const msg = error.response?.data?.message || 'Error casting vote';
      setSuccessMessage('');
      setErrorMessage(msg);
    }
  };

  useEffect(() => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL;
    const fetchLeaderboard = async () => {
      try {
        const response = await axios.get(`${backendUrl}/leaderboard`);
        setLeaderboard(response.data.leaderboard);
      } catch (error) {
        console.error('Error fetching leaderboard');
      }
    }

    const fetchCandidates = async () => {
      try {
        const response = await axios.get(`${backendUrl}/candidates`);
        setCandidates(response.data.candidates);
      } catch (error) {
        console.error('Error fetching candidates');
      }
    }

    fetchLeaderboard();
    fetchCandidates();
  }, []);

  return (
    <div style={{ maxWidth: '360px', fontFamily: 'Arial, sans-serif', padding: '1rem', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', backgroundColor:'#888', border: '1px solid #ddd' }}>
      <h1 style={{ color: '#fff', textAlign: 'center' }}>Which animal is your favorite?</h1>
      <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', margin: '2rem' }}>
        {Object.values(candidates).map((candidate) => (
          <div
            key={candidate.name}
            onClick={() => castVote(candidate.name)}
            style={{
              backgroundColor: candidate.color,
              borderRadius: '10px',
              padding: '2rem',
              marginBottom: '0.75rem',
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
              transition: 'transform 0.1s ease',
            }}
          >
            <img
              src={candidate.image}
              alt={candidate.name}
              style={{ width: '80px', height: '80px', borderRadius: '50%', marginRight: '1rem' }}
            />
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>{candidate.name}</div>
              <div style={{ fontSize: '0.85rem' }}>Tap to vote</div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ align: 'center', color: '#fff' }}>
        {successMessage && (
          <div style={{ background: '#0805', marginBottom: '1rem', padding: '1rem', textAlign: 'center', border: '3px solid #080', borderRadius: '10px' }}>
            {successMessage}
          </div>
        )}
        {errorMessage && (
          <div style={{ background: '#8005', marginBottom: '1rem', padding: '1rem', textAlign: 'center', border: '3px solid #800', borderRadius: '10px'  }}>
            {errorMessage}
          </div>
        )}
      </div>

      <hr />

      <div style={{ marginTop: '1rem', color: '#fff' }}>
        <h4 style={{ marginBottom: '0.5rem' }}>Leaderboard</h4>
        <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.9rem' }}>
          {leaderboard.map(([name, count], index) => (
            <LeaderboardRow key={index} name={name} count={count} maxCount={Math.max(...leaderboard.map(([_, count]) => Number(count)))} />
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;