# Security Advisory

## ⚠️ Important Security Notice

If you cloned this repository before the security fix (commit fd3d906), please note that API keys were previously committed to the repository history.

## Required Actions:

### 1. Revoke Compromised Keys
- **Spotify API**: Go to [Spotify Developer Dashboard](https://developer.spotify.com/) and regenerate your Client Secret
- **Gemini API**: Go to [Google AI Studio](https://ai.google.dev/) and regenerate your API key

### 2. Set Up New Environment
1. Copy `.env.example` to `.env`
2. Add your new API keys to the `.env` file
3. Ensure `.env` is in your `.gitignore` (it should be by default)

### 3. Verify Security
- Never commit the `.env` file
- Always use environment variables for sensitive data
- Regularly rotate API keys

## Git History Note
The git history may still contain the old credentials. For maximum security, consider:
- Creating a fresh fork/clone after revoking old keys
- Using tools like `git-filter-branch` if you need to clean history (advanced users only)

## Prevention
- Always use `.env` files for credentials
- Check files before committing with `git status` and `git diff`
- Use pre-commit hooks to scan for secrets