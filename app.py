from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import os

app = Flask(__name__)
socketio = SocketIO(app)

# MongoDB setup with authentication
# Replace <username>, <password>, <hostname>, <port>, <database_name>
username =  os.getenv('MONGODB_USERNAME')
password = os.getenv('MONGODB_PASSWORD')
hostname = os.getenv('MONGODB_HOSTNAME')  # e.g., 'localhost' or MongoDB Atlas cluster URL
port = 27017  # MongoDB default port
database_name = os.getenv('MONGODB_DATABASE')

client = MongoClient(f'mongodb://{username}:{password}@{hostname}:{port}/{database_name}?authMechanism=PLAIN')
db = client[database_name]
leaderboard = db['leaderboard']

# Game state
game_state = {
    'board': [''] * 9,
    'current_turn': 'X',
    'winner': None,
    'message': "Player X's turn"
}

@app.route('/')
def index():
    return render_template('index.html', game_state=game_state)

@socketio.on('make_move')
def handle_make_move(json):
    global game_state
    position = int(json['position'])
    player = json['player']
    
    if player != game_state['current_turn']:
        return
    
    if game_state['board'][position] == '' and game_state['winner'] is None:
        game_state['board'][position] = game_state['current_turn']
        if check_winner(game_state['board']):
            game_state['winner'] = game_state['current_turn']
            game_state['message'] = f"Player {game_state['current_turn']} wins!"
            update_leaderboard(player)
        elif '' not in game_state['board']:
            game_state['message'] = "It's a tie!"
        else:
            game_state['current_turn'] = 'O' if game_state['current_turn'] == 'X' else 'X'
            game_state['message'] = f"Player {game_state['current_turn']}'s turn"
    
    emit('update', game_state, broadcast=True)

@socketio.on('reset')
def handle_reset():
    global game_state
    game_state = {
        'board': [''] * 9,
        'current_turn': 'X',
        'winner': None,
        'message': "Player X's turn"
    }
    emit('update', game_state, broadcast=True)

def check_winner(board):
    winning_combinations = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != '':
            return True
    return False

def update_leaderboard(player):
    existing_record = leaderboard.find_one({'player': player})
    if existing_record:
        leaderboard.update_one({'player': player}, {'$inc': {'score': 1}})
    else:
        leaderboard.insert_one({'player': player, 'score': 1})

@app.route('/leaderboard')
def show_leaderboard():
    leaderboard_data = list(leaderboard.find().sort('score', -1))
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
