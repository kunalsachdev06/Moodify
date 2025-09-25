# 🎵 Moodify

Transform your feelings into the perfect soundtrack. Moodify is an intelligent mood-based playlist generator that uses AI to create personalized Spotify playlists based on your current vibe.

## ✨ Features

- **Smart Mood Analysis**: Powered by Google Gemini AI to understand natural language mood descriptions
- **Spotify Integration**: Seamless OAuth login and playlist creation directly in your Spotify account  
- **Intelligent Recommendations**: Advanced audio feature matching for perfect mood-to-music translation
- **Modern UI**: Clean, responsive design with smooth animations and intuitive controls
- **Real-time Preview**: Listen to track previews before saving your playlist
- **One-Click Save**: Instantly save generated playlists to your Spotify library

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/kunalsachdev06/Moodify.git
   cd Moodify
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   GEMINI_API_KEY=your_gemini_api_key
   REDIRECT_URI=http://localhost:5000/callback
   FLASK_SECRET_KEY=your_secret_key
   ```

4. **Run the application**
   ```bash
   python backend/app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🎯 How It Works

1. **Login**: Connect your Spotify account securely via OAuth
2. **Describe Your Mood**: Type natural language like "chill rainy evening vibes" or "pump me up for the gym"
3. **AI Analysis**: Gemini AI interprets your mood and maps it to audio features
4. **Smart Matching**: Spotify's recommendation engine finds perfect tracks based on the analysis
5. **Save & Enjoy**: Preview tracks and save your custom playlist directly to Spotify

## 🛠 Tech Stack

- **Backend**: Python Flask
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **AI**: Google Gemini API for mood analysis
- **Music**: Spotify Web API
- **Styling**: Modern CSS with gradient backgrounds and smooth animations

## 📱 Usage Examples

Try these mood descriptions:
- "chill rainy evening 🌧️"
- "energetic morning workout 💪"
- "focus study session 📚"
- "nostalgic 90s throwback"
- "cozy coffee shop vibes ☕"
- "party dance floor 🕺"

## 🔧 API Endpoints

- `GET /` - Landing page
- `GET /login` - Spotify OAuth login
- `GET /callback` - OAuth callback handler
- `GET /mood` - Mood input interface
- `GET /api/recommendations?mood={mood}` - Get track recommendations
- `POST /api/create_playlist` - Create Spotify playlist

## 📁 Project Structure

```
Moodify/
├── backend/
│   └── app.py                 # Main Flask application
├── frontend/
│   ├── index.html            # Landing page
│   └── mood.html             # Mood input page
├── static/
│   ├── css/
│   │   └── style.css         # Styles and animations
│   └── js/
│       └── mood.js           # Frontend interactivity
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
└── README.md
```

## 🎨 Design Philosophy

Moodify follows a minimalist design approach with:
- **Pastel Color Palette**: Soft lavender, teal, and peach tones
- **Smooth Transitions**: Subtle hover effects and animations
- **Responsive Layout**: Works seamlessly on desktop and mobile
- **Clean Typography**: Readable and modern font choices

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.