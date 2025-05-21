from flask import Flask, jsonify, request
from time import time
from datetime import date
import hashlib
from uuid import uuid4
import os
import json
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

load_dotenv()

db_url = os.getenv('MYSQL_URL')
engine = create_engine(db_url)

def load_allowed_candidates():
    global ALLOWED_CANDIDATES
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM candidates"))
        ALLOWED_CANDIDATES = [row.name for row in result]

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.create_genesis_block()

    def create_genesis_block(self):
        self.new_block(proof=1, previous_hash='0')

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'votes': self.current_votes,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_votes = []  # Reset pending votes
        self.chain.append(block)
        return block

    def hash_vote(vote):
        vote_string = json.dumps(vote, sort_keys=True).encode()
        return hashlib.sha256(vote_string).hexdigest()

    def new_vote(self, voter_id, candidate):
        with engine.connect() as conn:
            try:
                conn.execute(text(f"INSERT INTO pollData (id, timestamp, candidate) VALUES (:id, :timestamp, :candidate)"), {"id": voter_id.replace('-', ''), "timestamp": date.today(), "candidate": candidate})
                conn.commit()
                vote = {
                    'voter_id': voter_id,
                    'candidate': candidate,
                }
                vote['hash'] = hash_vote(vote)
                self.current_votes.append(vote)
                return self.last_block['index'] + 1
            except IntegrityError as e:
                conn.rollback()
                print("Integrity violation occurred: ", e.orig)
                return -1

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def get_leaderboard(self):
        leaderboard = {}
        with engine.connect() as conn:
            for c in ALLOWED_CANDIDATES:
                data = conn.execute(text(f"SELECT COUNT(*) FROM pollData WHERE candidate = :candidate"), {"candidate": c})
                if c not in leaderboard:
                    leaderboard[c] = 0
                leaderboard[c] += data.scalar()
        sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        return sorted_leaderboard
    
app = Flask(__name__)
CORS(app)
blockchain = Blockchain()
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

@app.route('/vote', methods=['POST'])
@limiter.limit("2 per minute") # Reasonable voting limit
def cast_vote():
    values = request.get_json()
    required = ['voter_id', 'candidate']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    # voting validation
    candidate = values['candidate']
    if candidate not in ALLOWED_CANDIDATES:
        return jsonify({'message': f"Invalid candidate. Choose from: {', '.join(ALLOWED_CANDIDATES)}"}), 400

    voted_ids = list()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM pollData"))
        for row in result:
            voted_ids.append(row.id)

    voter_id = values['voter_id']
    for block in blockchain.chain:
        for vote in block['votes']:
            if vote['voter_id'] == voter_id or voter_id.replace('-', '') in voted_ids:
                return jsonify({'message': 'Voter has already cast a vote'}), 403
    for vote in blockchain.current_votes:
        if vote['voter_id'] == voter_id:
            return jsonify({'message': 'Voter has already cast a vote (pending mining)'}), 403

    index = blockchain.new_vote(values['voter_id'], values['candidate'])
    if index > -1:
        mine_block() # called from backend only
        return jsonify({'message': f'Vote will be added to Block {index}'}), 201
    else:
        return jsonify({'message': 'Voter has already cast a vote (stored in DB).'}), 403

@limiter.limit("2 per minute") # Don't spam block creation
def mine_block():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    block = blockchain.new_block(proof)

@app.route('/votes', methods=['GET'])
def get_votes():
    all_votes = []
    for block in blockchain.chain:
        all_votes.extend(block['votes'])
    return jsonify({'votes': all_votes}), 200

@app.route('/pending', methods=['GET'])
def get_pending_votes():
    return jsonify({'pending_votes': blockchain.current_votes}), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200

@app.route('/candidates', methods=['GET'])
def get_candidates():
    global ALLOWED_CANDIDATES
    candidates = {}
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name, color, image FROM candidates"))
        for row in result:
            candidates[row.name] = ({'name': row.name, 'color': row.color, 'image': row.image})
    ALLOWED_CANDIDATES = list(candidates.keys())
    return jsonify({'candidates': candidates}), 200

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    leaderboard = blockchain.get_leaderboard()
    return jsonify({'leaderboard': leaderboard}), 200

if __name__ == '__main__':
    load_allowed_candidates() # Ensure list is initialized
    app.run(debug=True, port=os.getenv("PORT", default=5000))