#!/usr/bin/env python3
"""
Configuration file for Instagram Bot
Contains all configurable parameters, paths, and API settings
"""

###################
## TIME AND DELAY SETTINGS
###################

SECONDS_IN_A_MINUTE = 60
MIN_DELAY_MINUTES = 150
MAX_DELAY_MINUTES = 300
SHORT_DELAY_MIN_MINUTES = 1
SHORT_DELAY_MAX_MINUTES = 3

###################
## FILE AND DIRECTORY PATHS
###################

LOCAL_DIRECTORY_PATH = "c:\\src\\python\\bdfr\\output\\to_ig\\"
HASHTAGS_FILE_PATH = "hashtags.txt"
TOKEN_FILE_PATH = "instagram_token.json"

###################
## SFTP SERVER CONFIGURATION
###################

# SFTP settings moved to config_security.py for better security

###################
## FACEBOOK/INSTAGRAM API CONFIGURATION
###################

# Non-sensitive API settings (sensitive credentials are in config_security.py)
GRAPH_API_VERSION = 'v18.0'
GRAPH_URL = f'https://graph.facebook.com/{GRAPH_API_VERSION}/'

###################
## MEDIA FILE SETTINGS
###################

VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
MAX_IMAGE_SIZE_MB = 8
MAX_VIDEO_SIZE_MB = 100
MB_TO_BYTES = 1024 * 1024

###################
## TOKEN MANAGEMENT SETTINGS
###################

TOKEN_EXPIRY_WARNING_DAYS = 7
LONG_LIVED_TOKEN_DURATION_DAYS = 60

###################
## HASHTAG SETTINGS
###################

DEFAULT_HASHTAG_COUNT = 5

###################
## NETWORK SETTINGS
###################

HTTP_TIMEOUT_SECONDS = 10

###################
## REELS SETTINGS
###################

REELS_THUMB_OFFSET = '10'

###################
## DEBUG AND LOGGING SETTINGS
###################

# Controls verbosity of debug output
# 0 = Silent (only errors), 1 = Basic info, 2 = Detailed debug, 3 = Verbose debug
DEBUG_VERBOSITY = 1

# Enable/disable specific debug categories
DEBUG_FILE_OPERATIONS = True
DEBUG_API_CALLS = True
DEBUG_CAPTION_GENERATION = True
DEBUG_NETWORK_OPERATIONS = True
DEBUG_TOKEN_MANAGEMENT = True

# PowerShell color codes for debug messages
DEBUG_COLORS = {
    'general': '\033[37m',      # White
    'file_ops': '\033[36m',     # Cyan
    'api': '\033[32m',          # Green
    'caption': '\033[35m',      # Magenta
    'network': '\033[34m',      # Blue
    'token': '\033[33m',        # Yellow
    'error': '\033[31m',        # Red
    'success': '\033[92m',      # Bright Green
    'warning': '\033[93m',      # Bright Yellow
    'info': '\033[96m',         # Bright Cyan
    'reset': '\033[0m'          # Reset to default
}

# Enable/disable colored output
DEBUG_USE_COLORS = True

###################
## API AND RESPONSE SETTINGS
###################

# HTTP status codes
HTTP_SUCCESS_CODE = 200

# Caption display limits
CAPTION_PREVIEW_LENGTH = 100

# Token display settings
TOKEN_PREVIEW_LENGTH = 20

# Sleep intervals (seconds)
WAIT_CHECK_INTERVAL_SECONDS = 60  # How often to check if wait time is complete
TERMINAL_CLEAR_SPACES = 80  # Spaces to clear terminal line