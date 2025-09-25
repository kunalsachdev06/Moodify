document.addEventListener('DOMContentLoaded', function() {
    const moodForm = document.getElementById('moodForm');
    const moodInput = document.getElementById('moodInput');
    const resultDiv = document.getElementById('result');
    const loadingDiv = document.getElementById('loading');
    const suggestionTags = document.querySelectorAll('.suggestion-tag');

    suggestionTags.forEach(tag => {
        tag.addEventListener('click', function() {
            const mood = this.dataset.mood;
            moodInput.value = mood;
            generatePlaylist(mood);
        });
    });

    moodForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const mood = moodInput.value.trim();
        if (mood) {
            generatePlaylist(mood);
        }
    });

    async function generatePlaylist(mood) {
        showLoading();
        
        try {
            const response = await fetch('http://127.0.0.1:5000/api/recommendations?mood=' + encodeURIComponent(mood));
            const data = await response.json();
            
            hideLoading();
            
            if (response.status === 401) {
                // Not authenticated - redirect to login
                showError('Please log in with Spotify first');
                setTimeout(() => {
                    window.location.href = 'http://127.0.0.1:5000/login';
                }, 2000);
                return;
            }
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            if (data.tracks && data.tracks.length > 0) {
                displayTracks(data.tracks, mood);
            } else {
                showNoResults();
            }
        } catch (error) {
            hideLoading();
            showError('Failed to generate playlist. Please try again.');
        }
    }

    function showLoading() {
        loadingDiv.style.display = 'block';
        resultDiv.style.display = 'none';
    }

    function hideLoading() {
        loadingDiv.style.display = 'none';
        resultDiv.style.display = 'block';
    }

    function displayTracks(tracks, mood) {
        let html = `
            <div class="playlist-header">
                <h3>Your ${mood} playlist is ready! 🎵</h3>
                <p>Found ${tracks.length} perfect tracks for your mood</p>
            </div>
            <div class="tracks">
        `;

        tracks.forEach(track => {
            html += `
                <div class="track" data-track-id="${track.id}">
                    ${track.image ? `<img src="${track.image}" alt="Album" class="track-image">` : ''}
                    <div class="track-info">
                        <div class="track-name">${track.name}</div>
                        <div class="track-artist">${track.artist}</div>
                        <div class="track-album">${track.album}</div>
                    </div>
                    <div class="track-controls">
                        ${track.preview_url ? `<audio controls preload="none">
                            <source src="${track.preview_url}" type="audio/mpeg">
                        </audio>` : '<span class="no-preview">No preview</span>'}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        
        html += `
            <div class="playlist-actions">
                <button class="create-playlist-btn" onclick="createSpotifyPlaylist('${mood}', ${JSON.stringify(tracks.map(t => t.id))})">
                    Save to Spotify
                </button>
                <button class="surprise-btn" onclick="surpriseMe()">
                    Surprise Me!
                </button>
            </div>
        `;

        resultDiv.innerHTML = html;
    }

    function showError(message) {
        resultDiv.innerHTML = `
            <div class="error-message">
                <p>⚠️ ${message}</p>
                <button onclick="location.reload()" class="retry-btn">Try Again</button>
            </div>
        `;
    }

    function showNoResults() {
        resultDiv.innerHTML = `
            <div class="no-results">
                <p>🤔 Hmm, couldn't find tracks for that mood.</p>
                <p>Try describing your feeling differently or use one of our suggestions!</p>
            </div>
        `;
    }

    window.createSpotifyPlaylist = async function(mood, trackIds) {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/create_playlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mood: mood,
                    track_ids: trackIds
                })
            });

            const data = await response.json();

            if (data.error) {
                alert('Failed to create playlist: ' + data.error);
                return;
            }

            alert(`Playlist "${data.name}" created successfully! Added ${data.tracks_added} tracks.`);
            
        } catch (error) {
            alert('Failed to create playlist. Please try again.');
        }
    };

    window.surpriseMe = function() {
        const surpriseMoods = [
            'upbeat summer vibes',
            'chill coffee shop',
            'nostalgic 90s throwback',
            'dreamy night drive',
            'energetic morning workout',
            'cozy rainy day',
            'party dance floor',
            'focus study session'
        ];
        
        const randomMood = surpriseMoods[Math.floor(Math.random() * surpriseMoods.length)];
        moodInput.value = randomMood;
        generatePlaylist(randomMood);
    };
});