from flask import Flask, request, redirect, session, jsonify, send_from_directory
from flask_cors import CORS
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

# Enhanced session configuration
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'moodify_secret_key_2025_fixed')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'moodify:'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Enable CORS for Live Server (port 5500)
CORS(app, origins=['http://127.0.0.1:5500', 'http://localhost:5500', 'http://127.0.0.1:5000', 'http://localhost:5000'])

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')
SPOTIFY_SCOPE = 'playlist-modify-public playlist-modify-private user-read-private user-read-email user-library-read user-top-read'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'

@app.route('/')
def index():
    frontend_dir = os.path.join(project_root, 'frontend')
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/login')
def login():
    print("🚀 Login route accessed")
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    print(f"🔑 OAuth state set: {state}")
    print(f"🔗 Redirect URI: {REDIRECT_URI}")
    
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SPOTIFY_SCOPE,
        'state': state,
        'show_dialog': 'true'
    }
    
    auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    print(f"🌐 Redirecting to: {auth_url[:100]}...")
    return redirect(auth_url)

@app.route('/callback')
def callback():
    print(f"📥 Callback received with args: {dict(request.args)}")
    print(f"📋 Session state: {session.get('oauth_state')}")
    
    if request.args.get('state') != session.get('oauth_state'):
        print("❌ State mismatch!")
        return jsonify({'error': 'Invalid state parameter'}), 400
    
    auth_code = request.args.get('code')
    if not auth_code:
        error = request.args.get('error')
        print(f"❌ No auth code: {error}")
        return jsonify({'error': f'Authorization failed: {error}'}), 400
    
    try:
        print("🔄 Exchanging code for token...")
        token_data = exchange_code_for_token(auth_code)
        
        # Store tokens in session
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token')
        session['token_expires_in'] = token_data.get('expires_in', 3600)
        
        print(f"✅ Token stored: {token_data['access_token'][:20]}...")
        
        # Get user info
        user_info = get_user_profile(token_data['access_token'])
        session['user_id'] = user_info.get('id')
        session['display_name'] = user_info.get('display_name')
        
        print(f"✅ User authenticated: {user_info.get('display_name')} ({user_info.get('id')})")
        print(f"📋 Final session: {dict(session)}")
        
        # Redirect to mood input page (we'll create this later)
        return redirect('/mood')
        
    except Exception as e:
        print(f"❌ Token exchange error: {str(e)}")
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
    
    frontend_dir = os.path.join(project_root, 'frontend')
    return send_from_directory(frontend_dir, 'mood.html')

@app.route('/debug/session')
def debug_session():
    """Debug endpoint to check session contents"""
    return jsonify({
        'session_contents': dict(session),
        'has_access_token': 'access_token' in session,
        'session_id': request.cookies.get('session'),
        'all_cookies': dict(request.cookies)
    })

@app.route('/debug/simple-test')
def simple_test():
    """Test basic Spotify API connectivity"""
    if 'access_token' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    access_token = session['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    
    results = {}
    
    # Test 1: Get user profile (should always work)
    try:
        print("🧪 Testing /me endpoint...")
        response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        print(f"📊 /me status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            results['profile_test'] = {
                'status': 'success',
                'user_id': user_data.get('id'),
                'display_name': user_data.get('display_name'),
                'country': user_data.get('country')
            }
        else:
            results['profile_test'] = {
                'status': 'error',
                'status_code': response.status_code,
                'error': response.text[:200]
            }
    except Exception as e:
        results['profile_test'] = {'status': 'exception', 'error': str(e)}
    
    # Test 2: Try recommendations API
    try:
        print("🧪 Testing recommendations endpoint...")
        params = {'limit': 5, 'seed_genres': 'pop'}
        response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
        print(f"📊 Recommendations status: {response.status_code}")
        print(f"📄 Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            data = response.json()
            results['recommendations_test'] = {
                'status': 'success',
                'track_count': len(data.get('tracks', []))
            }
        else:
            results['recommendations_test'] = {
                'status': 'error',
                'status_code': response.status_code,
                'error': response.text[:200]
            }
    except Exception as e:
        results['recommendations_test'] = {'status': 'exception', 'error': str(e)}
    
    return jsonify(results)

@app.route('/api/recommendations')
def get_recommendations():
    print(f"Session contents: {dict(session)}")  # Debug session
    
    if 'access_token' not in session:
        return jsonify({
            'error': 'Please log in with Spotify first',
            'redirect': '/login'
        }), 401
    
    mood = request.args.get('mood')
    if not mood:
        return jsonify({'error': 'Mood parameter required'}), 400
    
    print(f"Getting recommendations for mood: {mood}")  # Debug
    
    try:
        tracks = get_spotify_recommendations(session['access_token'], mood)
        return jsonify({
            'mood': mood,
            'tracks': tracks
        })
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")  # Debug
        return jsonify({'error': str(e)}), 500

def get_spotify_recommendations(access_token, mood):
    headers = {'Authorization': f'Bearer {access_token}'}
    
    mood_params = parse_mood_to_spotify_params(mood)
    
    # Spotify API requires seed parameters - use only validated genres
    valid_spotify_genres = [
        'acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient', 'blues', 'bossanova', 
        'brazil', 'breakbeat', 'british', 'chill', 'classical', 'club', 'country', 'dance', 
        'dancehall', 'deep-house', 'disco', 'drum-and-bass', 'dub', 'dubstep', 'electronic', 
        'folk', 'funk', 'garage', 'gospel', 'groove', 'grunge', 'hip-hop', 'house', 'indie', 
        'jazz', 'latin', 'metal', 'new-age', 'pop', 'punk', 'r-n-b', 'reggae', 'rock', 'soul', 
        'techno', 'trance', 'world-music'
    ]
    
    # Get genres and filter to only valid ones
    requested_genres = mood_params.get('genres', ['pop'])
    genres = [g for g in requested_genres if g in valid_spotify_genres]
    
    # Fallback to 'pop' if no valid genres
    if not genres:
        genres = ['pop']
    
    audio_features = mood_params.get('audio_features', {})
    
    # Build parameters with market (required for some regions)
    params = {
        'limit': 10,  # Reduced for reliability
        'seed_genres': ','.join(genres[:3]),  # Reduced to 3 genres max
        'market': 'US'  # Add market parameter to prevent 404
    }
    
    # Add only basic audio features to minimize API complexity
    if 'energy' in audio_features:
        params['target_energy'] = round(audio_features['energy'], 1)  # Round to 1 decimal
    
    print(f"🎵 Spotify API Request: {SPOTIFY_API_BASE}/recommendations")
    print(f"📋 Params: {params}")
    print(f"🔑 Headers: Authorization Bearer {access_token[:20]}...")
    
    response = requests.get(f'{SPOTIFY_API_BASE}/recommendations', headers=headers, params=params)
    
    print(f"📊 Spotify API Response: {response.status_code}")
    
    # If primary request fails, try with ultra-minimal params
    if response.status_code == 404:
        print("🔄 Retrying with minimal parameters...")
        minimal_params = {
            'limit': 5,
            'seed_genres': 'pop',
            'market': 'US'
        }
        response = requests.get(f'{SPOTIFY_API_BASE}/recommendations', headers=headers, params=minimal_params)
        print(f"📊 Retry Response: {response.status_code}")
    
    if response.status_code != 200:
        error_details = response.text
        try:
            error_json = response.json()
            error_details = f"Status: {response.status_code}, Error: {error_json}"
        except:
            pass
        print(f"❌ Spotify API Error: {error_details}")
        raise Exception(f'Spotify API Error ({response.status_code}): {error_details}')
    
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
    print(f"🧠 Parsing mood: {mood}")
    
    try:
        ai_params = get_ai_mood_analysis(mood)
        if ai_params:
            print(f"✅ AI analysis successful: {ai_params}")
            return ai_params
        else:
            print("⚠️ AI analysis returned None")
    except Exception as e:
        print(f"❌ AI analysis failed: {str(e)}")
        pass
    
    mood_lower = mood.lower()
    
    if any(word in mood_lower for word in ['chill', 'calm', 'relax', 'peaceful']):
        return {
            'genres': ['ambient', 'chill', 'new-age'],
            'audio_features': {'valence': 0.3, 'energy': 0.2, 'danceability': 0.3}
        }
    elif any(word in mood_lower for word in ['happy', 'upbeat', 'energetic', 'party']):
        return {
            'genres': ['pop', 'dance', 'disco'],
            'audio_features': {'valence': 0.8, 'energy': 0.8, 'danceability': 0.7}
        }
    elif any(word in mood_lower for word in ['sad', 'melancholy', 'depressed', 'blue']):
        return {
            'genres': ['indie', 'alternative', 'blues'],
            'audio_features': {'valence': 0.2, 'energy': 0.3, 'danceability': 0.2}
        }
    elif any(word in mood_lower for word in ['workout', 'gym', 'exercise', 'run']):
        return {
            'genres': ['hip-hop', 'electronic', 'techno'],
            'audio_features': {'valence': 0.7, 'energy': 0.9, 'danceability': 0.8}
        }
    elif any(word in mood_lower for word in ['focus', 'study', 'concentration']):
        return {
            'genres': ['ambient', 'classical', 'electronic'],
            'audio_features': {'valence': 0.4, 'energy': 0.3, 'danceability': 0.2}
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
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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
    app.run(debug=True, port=5000, host='127.0.0.1')