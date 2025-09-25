# Moodify - Intelligent Mood-Based Playlist Generator

An AI-powered web application that generates Spotify playlists based on your mood and natural language input.

## Features

- **Smart Mood Interpretation**: Uses Gemini AI to parse natural language mood descriptions
- **Spotify Integration**: Creates and manages playlists directly in your Spotify account
- **Minimalist UI**: Clean, responsive design with pastel colors and smooth animations
- **Interactive Features**: Surprise Me button, playlist refinement, and preview controls

## Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **APIs**: Spotify Web API, Google Gemini AI
- **Authentication**: Spotify OAuth 2.0

## Setup

### Prerequisites
- Python 3.7+
- Spotify Developer Account
- Google Gemini API Key

### Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install flask requests python-dotenv
   ```
3. Create `.env` file with your API credentials:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   GEMINI_API_KEY=your_gemini_key
   ```
4. Run the application:
   ```bash
   python backend/app.py
   ```

## Project Structure

```
Moodify/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── spotify_client.py   # Spotify API wrapper
│   └── gemini_client.py    # Gemini AI integration
├── frontend/
│   ├── index.html          # Login page
│   ├── mood.html           # Mood input page
│   ├── playlist.html       # Playlist display
│   └── static/
│       ├── css/
│       │   └── style.css   # Main stylesheet
│       └── js/
│           └── app.js      # Frontend logic
├── .env                    # Environment variables
├── .gitignore
└── README.md
```

## Usage

1. **Login**: Click "Login with Spotify" to authenticate
2. **Input Mood**: Describe your mood (e.g., "chill rainy evening 🌧️")
3. **Generate Playlist**: AI creates a personalized playlist
4. **Enjoy**: Preview tracks and save to your Spotify account

## Contributing

1. Make small, incremental commits
2. Document code changes
3. Test on multiple devices
4. Follow the UI/UX guidelines

## License

MIT License