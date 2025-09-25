from flask import Flask, request, redirect, session, jsonify, render_template_string
import requests
import base64
import secrets
import os
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')
SPOTIFY_SCOPE = 'playlist-modify-public playlist-modify-private user-read-private user-read-email'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Moodify - Login</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>Welcome to Moodify</h1>
        <p>Generate playlists based on your mood!</p>
        <a href="/login">
            <button>Login with Spotify</button>
        </a>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SPOTIFY_SCOPE,
        'state': state,
        'show_dialog': 'true'
    }
    
    auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if request.args.get('state') != session.get('oauth_state'):
        return jsonify({'error': 'Invalid state parameter'}), 400
    
    auth_code = request.args.get('code')
    if not auth_code:
        error = request.args.get('error')
        return jsonify({'error': f'Authorization failed: {error}'}), 400
    
    try:
        token_data = exchange_code_for_token(auth_code)
        
        # Store tokens in session
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token')
        session['token_expires_in'] = token_data.get('expires_in', 3600)
        
        # Get user info
        user_info = get_user_profile(token_data['access_token'])
        session['user_id'] = user_info.get('id')
        session['display_name'] = user_info.get('display_name')
        
        # Redirect to mood input page (we'll create this later)
        return redirect('/mood')
        
    except Exception as e:
        return jsonify({'error': f'Token exchange failed: {str(e)}'}), 500

def exchange_code_for_token(auth_code):
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    # Prepare request
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
    
    if response.status_code != 200:
        raise Exception(f'Token request failed: {response.text}')
    
    return response.json()

def get_user_profile(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f'{SPOTIFY_API_BASE}/me', headers=headers)
    
    if response.status_code != 200:
        raise Exception(f'Failed to get user profile: {response.text}')
    
    return response.json()

@app.route('/mood')
def mood_page():
    if 'access_token' not in session:
        return redirect('/')
    
    display_name = session.get('display_name', 'User')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Moodify - What's Your Mood?</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>Hi {display_name}! What's your mood?</h1>
        <p>Describe how you're feeling and we'll create the perfect playlist</p>
        
        <form id="moodForm">
            <input type="text" id="moodInput" placeholder="e.g., chill rainy evening 🌧️" style="width: 300px; padding: 10px;">
            <button type="submit">Generate Playlist</button>
        </form>
        
        <div id="result"></div>
        
        <script>
            document.getElementById('moodForm').addEventListener('submit', function(e) {{
                e.preventDefault();
                const mood = document.getElementById('moodInput').value;
                if (mood) {{
                    document.getElementById('result').innerHTML = '<p>Generating playlist for: ' + mood + '</p>';
                    // We'll implement the actual API call later
                }}
            }});
        </script>
    </body>
    </html>
    '''

@app.route('/api/recommendations')
def get_recommendations():
    """API endpoint to get playlist recommendations"""
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    mood = request.args.get('mood')
    if not mood:
        return jsonify({'error': 'Mood parameter required'}), 400
    
    # For now, return a placeholder response
    # We'll implement the actual Spotify API integration next
    return jsonify({
        'mood': mood,
        'message': 'Playlist generation coming soon!',
        'tracks': []
    })

if __name__ == '__main__':
    print("Starting Moodify server...")
    print(f"Spotify Client ID: {SPOTIFY_CLIENT_ID[:8]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    app.run(debug=True, port=5000)