#!/usr/bin/env python3
"""
Debug Spotify API connectivity and permissions
"""

import requests
import json
import os
from dotenv import load_dotenv
import base64

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

def get_client_credentials_token():
    """Get a client credentials token"""
    auth_url = 'https://accounts.spotify.com/api/token'
    
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post(auth_url, headers=headers, data=data)
    print(f"Token request status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"Token type: {token_data.get('token_type')}")
        print(f"Scope: {token_data.get('scope', 'No scope')}")
        return token_data['access_token']
    else:
        print(f"Token error: {response.text}")
        return None

def debug_spotify_api():
    """Debug what endpoints work with our token"""
    token = get_client_credentials_token()
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test different endpoints to see what works
    endpoints_to_test = [
        ('Available Genre Seeds', 'https://api.spotify.com/v1/recommendations/available-genre-seeds'),
        ('Markets', 'https://api.spotify.com/v1/markets'),
        ('Search', 'https://api.spotify.com/v1/search?q=pop&type=track&limit=1'),
        ('Recommendations Basic', 'https://api.spotify.com/v1/recommendations?seed_genres=pop&limit=1'),
        ('Recommendations with Market', 'https://api.spotify.com/v1/recommendations?seed_genres=pop&limit=1&market=US'),
    ]
    
    print(f"\n🧪 Testing Spotify API endpoints...")
    print(f"Using Client ID: {SPOTIFY_CLIENT_ID[:8]}...")
    
    for name, url in endpoints_to_test:
        print(f"\n📡 Testing {name}:")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'genres' in data:
                    print(f"   ✅ Available genres: {data['genres'][:5]}...")
                elif 'markets' in data:
                    print(f"   ✅ Available markets: {data['markets'][:5]}...")
                elif 'tracks' in data:
                    if 'items' in data['tracks']:
                        print(f"   ✅ Search results: {len(data['tracks']['items'])} tracks")
                    else:
                        print(f"   ✅ Recommendations: {len(data.get('tracks', []))} tracks")
                else:
                    print(f"   ✅ Success: {list(data.keys())}")
            else:
                error_text = response.text[:200] if response.text else "No error text"
                print(f"   ❌ Error: {error_text}")
                
                # Try to parse JSON error
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_info = error_data['error']
                        print(f"   📋 Error details: {error_info.get('message', 'No message')}")
                        print(f"   🔍 Error status: {error_info.get('status', 'No status')}")
                except:
                    pass
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")

if __name__ == '__main__':
    debug_spotify_api()