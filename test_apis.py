#!/usr/bin/env python3
"""
Quick test script to verify Gemini AI and Spotify API configurations
"""
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini_api():
    """Test Gemini AI API"""
    print("🤖 Testing Gemini AI API...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple test
        response = model.generate_content("Say 'Hello from Gemini!' in JSON format")
        print(f"✅ Gemini API Response: {response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API Error: {str(e)}")
        return False

def test_spotify_client_credentials():
    """Test Spotify API with client credentials"""
    print("\n🎵 Testing Spotify API...")
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Spotify credentials not found")
        return False
    
    print(f"✅ Client ID: {client_id[:10]}...")
    print(f"✅ Client Secret: {client_secret[:10]}...")
    
    try:
        # Test client credentials flow
        import base64
        
        auth_string = f"{client_id}:{client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Spotify API Token obtained: {token_data['access_token'][:20]}...")
            
            # Test recommendations API
            headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
            params = {
                'limit': 5,
                'seed_genres': 'pop',
                'target_energy': 0.7
            }
            
            rec_response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
            
            if rec_response.status_code == 200:
                rec_data = rec_response.json()
                print(f"✅ Spotify Recommendations API working: {len(rec_data.get('tracks', []))} tracks found")
                return True
            else:
                try:
                    error_data = rec_response.json()
                    print(f"❌ Recommendations API Error: {rec_response.status_code}")
                    print(f"   Error Details: {error_data}")
                except:
                    print(f"❌ Recommendations API Error: {rec_response.status_code} - {rec_response.text}")
                return False
        else:
            print(f"❌ Spotify Token Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Spotify API Error: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print("🔍 API Configuration Test\n" + "="*50)
    
    gemini_ok = test_gemini_api()
    spotify_ok = test_spotify_client_credentials()
    
    print(f"\n📊 Test Results:")
    print(f"Gemini AI: {'✅ Working' if gemini_ok else '❌ Failed'}")
    print(f"Spotify API: {'✅ Working' if spotify_ok else '❌ Failed'}")
    
    if gemini_ok and spotify_ok:
        print("\n🎉 All APIs are working correctly!")
    else:
        print("\n⚠️  Some APIs have issues - check the errors above")

if __name__ == '__main__':
    main()