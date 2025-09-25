from flask import Flask, request, redirect, session, jsonify, send_from_directory
import requests
import base64
import secrets
import os
import json
from dotenv import load_dotenv
from urllib.parse import urlencode
import google.generativeai as genai

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

app = Flask(__name__, 
           static_folder=os.path.join(project_root, 'static'), 
           static_url_path='/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')
SPOTIFY_SCOPE = 'playlist-modify-public playlist-modify-private user-read-private user-read-email'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'

@app.route('/')
def index():
    return send_from_directory(os.path.join(project_root, 'frontend'), 'index.html')

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
    
    return send_from_directory(os.path.join(project_root, 'frontend'), 'mood.html')

@app.route('/api/recommendations')
def get_recommendations():
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    mood = request.args.get('mood')
    if not mood:
        return jsonify({'error': 'Mood parameter required'}), 400
    try:
        tracks = get_spotify_recommendations(session['access_token'], mood)
        return jsonify({
            'mood': mood,
            'tracks': tracks
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_spotify_recommendations(access_token, mood):
    headers = {'Authorization': f'Bearer {access_token}'}
    
    mood_params = parse_mood_to_spotify_params(mood)
    
    params = {
        'limit': 20,
        'seed_genres': mood_params.get('genres', ['pop']),
        **mood_params.get('audio_features', {})
    }
    
    response = requests.get(f'{SPOTIFY_API_BASE}/recommendations', headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(f'Failed to get recommendations: {response.text}')
    
    data = response.json()
    tracks = []
    
    for track in data.get('tracks', []):
        tracks.append({
            'id': track['id'],
            'name': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'preview_url': track.get('preview_url'),
            'external_url': track['external_urls']['spotify']
        })
    
    return tracks

def parse_mood_to_spotify_params(mood):
    try:
        ai_params = get_ai_mood_analysis(mood)
        if ai_params:
            return ai_params
    except:
        pass
    
    mood_lower = mood.lower()
    
    if any(word in mood_lower for word in ['chill', 'calm', 'relax', 'peaceful']):
        return {
            'genres': ['ambient', 'chill'],
            'audio_features': {'valence': 0.3, 'energy': 0.2, 'danceability': 0.3}
        }
    elif any(word in mood_lower for word in ['happy', 'upbeat', 'energetic', 'party']):
        return {
            'genres': ['pop', 'dance'],
            'audio_features': {'valence': 0.8, 'energy': 0.8, 'danceability': 0.7}
        }
    elif any(word in mood_lower for word in ['sad', 'melancholy', 'depressed', 'blue']):
        return {
            'genres': ['indie', 'alternative'],
            'audio_features': {'valence': 0.2, 'energy': 0.3, 'danceability': 0.2}
        }
    elif any(word in mood_lower for word in ['workout', 'gym', 'exercise', 'run']):
        return {
            'genres': ['hip-hop', 'electronic'],
            'audio_features': {'valence': 0.7, 'energy': 0.9, 'danceability': 0.8}
        }
    else:
        return {
            'genres': ['pop'],
            'audio_features': {'valence': 0.5, 'energy': 0.5, 'danceability': 0.5}
        }

def get_ai_mood_analysis(mood):
    if not GEMINI_API_KEY:
        return None
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Analyze this mood description and return ONLY a JSON object with Spotify audio features and genres.
        
        Mood: "{mood}"
        
        Return format (must be valid JSON):
        {{
            "genres": ["genre1", "genre2"],
            "audio_features": {{
                "valence": 0.0-1.0,
                "energy": 0.0-1.0,
                "danceability": 0.0-1.0
            }}
        }}
        
        Available genres: pop, rock, hip-hop, electronic, indie, alternative, r-n-b, country, jazz, blues, classical, reggae, punk, metal, folk, ambient, chill, dance, house, techno, disco, funk, soul, gospel, latin, world-music, new-age, singer-songwriter
        
        Valence: 0.0 = sad/negative, 1.0 = happy/positive
        Energy: 0.0 = calm/peaceful, 1.0 = energetic/intense  
        Danceability: 0.0 = not danceable, 1.0 = very danceable
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        parsed = json.loads(text)
        return parsed
        
    except Exception as e:
        print(f"AI mood analysis failed: {e}")
        return None

@app.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    mood = data.get('mood')
    track_ids = data.get('track_ids', [])
    
    if not mood or not track_ids:
        return jsonify({'error': 'Mood and track_ids required'}), 400
    
    try:
        playlist = create_spotify_playlist(session['access_token'], session['user_id'], mood, track_ids)
        return jsonify(playlist)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_spotify_playlist(access_token, user_id, mood, track_ids):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    playlist_name = f"{mood.title()} Vibes"
    
    playlist_data = {
        'name': playlist_name,
        'description': f'Generated playlist for {mood} mood',
        'public': False
    }
    
    response = requests.post(f'{SPOTIFY_API_BASE}/users/{user_id}/playlists', 
                           headers=headers, json=playlist_data)
    
    if response.status_code != 201:
        raise Exception(f'Failed to create playlist: {response.text}')
    
    playlist = response.json()
    playlist_id = playlist['id']
    
    track_uris = [f'spotify:track:{track_id}' for track_id in track_ids]
    tracks_data = {'uris': track_uris}
    
    response = requests.post(f'{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks',
                           headers=headers, json=tracks_data)
    
    if response.status_code != 201:
        raise Exception(f'Failed to add tracks to playlist: {response.text}')
    
    return {
        'id': playlist_id,
        'name': playlist_name,
        'url': playlist['external_urls']['spotify'],
        'tracks_added': len(track_ids)
    }

if __name__ == '__main__':
    print("Starting Moodify server...")
    print(f"Spotify Client ID: {SPOTIFY_CLIENT_ID[:8]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    app.run(debug=True, port=5500, host='127.0.0.1')