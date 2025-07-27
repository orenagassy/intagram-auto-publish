# Instagram Bot

Automated Instagram posting bot that uploads images and videos from a local directory to Instagram with automatic token management and scheduled posting.

## Features

- **Automated Posting**: Automatically posts images and videos to Instagram
- **Token Management**: Handles Instagram API token lifecycle with automatic refresh
- **Story Support**: Posts images as both feed posts and stories
- **Reels Support**: Videos are posted as Instagram Reels
- **Smart Scheduling**: Pause-resistant scheduling using absolute timestamps
- **File Cleanup**: Automatic cleanup of local and remote files after posting
- **Hashtag Management**: Random hashtag selection from configurable file
- **Caption Cleaning**: Removes common filename suffixes like _1, _2 from captions
- **Debug Control**: Configurable debug verbosity levels

## Requirements

- Python 3.6+
- Instagram Business/Creator account
- Facebook Developer App with Instagram Basic Display API
- SFTP server for temporary file hosting (Instagram requires publicly accessible URLs)

## Installation

1. Clone this repository
2. Install required dependencies:
   ```bash
   pip install requests pysftp
   ```

3. Set up configuration:
   - Copy `config_security.py.example` to `config_security.py`
   - Update `config_security.py` with your API credentials and SFTP details
   - Update `config.py` with your local directory path and other settings

4. Create a `hashtags.txt` file with your hashtags (one per line, starting with #)

## Configuration

### Security Configuration (`config_security.py`)
Contains sensitive credentials that should not be committed to version control:
- Instagram API credentials (APP_ID, APP_SECRET, IG_ACCOUNT_ID)
- SFTP server credentials

### Operational Configuration (`config.py`)
Contains non-sensitive application settings:
- File paths and directories
- Timing and delay parameters
- Media file size limits
- Debug verbosity settings

## Usage

### First-time Setup
```bash
# Run one-time token setup
python instagram_bot.py setup

# Or use the separate setup script
python instagram_bot_setup.py
```

### Normal Operation
```bash
# Run the bot
python instagram_bot.py
```

## How It Works

1. **Startup**: Validates token, loads hashtags, checks configuration
2. **File Selection**: Randomly selects media file from configured directory
3. **File Processing**: 
   - Validates file size/format against Instagram limits
   - Uploads to SFTP server with sanitized filename
   - Tests URL accessibility
4. **Caption Generation**: 
   - Uses cleaned filename (removes _1, _2 suffixes)
   - Adds random hashtags from hashtags.txt
5. **Instagram Upload**:
   - Images: Posted as feed post + story
   - Videos: Posted as Instagram Reels
6. **Cleanup**: Removes both local and remote files
7. **Scheduling**: Waits 150-300 minutes before next post

## File Structure

```
instagram_bot/
├── instagram_bot.py          # Main application
├── instagram_bot_setup.py    # Token setup utility
├── config.py                 # Operational configuration
├── config_security.py        # Security credentials (not in git)
├── config_security.py.example # Template for security config
├── hashtags.txt              # Hashtags file
├── instagram_token.json      # Auto-managed token storage
├── CLAUDE.md                 # Development instructions
└── README.md                 # This file
```

## Instagram API Setup

1. Create a Facebook Developer App
2. Add Instagram Basic Display product
3. Set up Instagram Test User or use your Instagram Business account
4. Generate long-lived access token
5. Add credentials to `config_security.py`

## Troubleshooting

- **Token errors**: Run setup again or check API credentials
- **File upload errors**: Verify SFTP credentials and server accessibility
- **Instagram API errors**: Check account permissions and API quotas
- **Network errors**: Verify internet connection and server availability

## Debug Settings

Control debug output in `config.py`:
- `DEBUG_VERBOSITY`: 0-3 (silent to verbose)
- Category-specific flags for file operations, API calls, etc.

## Security Notes

- Never commit `config_security.py` to version control
- Use environment variables in production
- Regularly rotate API credentials
- Monitor API usage quotas

## License

This project is for educational purposes. Ensure compliance with Instagram's Terms of Service and API usage policies.